import os
import logging
import asyncio
import wave

from dotenv import load_dotenv

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.background_audio import BackgroundAudioPlayer, AudioConfig
from livekit.rtc import rtc, ParticipantKind
from livekit.plugins import openai, deepgram, elevenlabs, silero, turn_detector

from memory.json_memory import JSONMemory

# Import modular agents
from agents.agent_selector import select_agent
from agents.smart_assistant_agent import smart_assistant_agent
from agents.passenger_details_agent import collect_passenger_details, extract_passenger_details
from agents.language_detection_agent import detect_language_from_text
from agents.flight_selection_agent import flight_selection_agent
from agents.flight_search_api_agent import flight_search_api_agent
from agents.flight_search_agent import extract_flight_details
from agents.flight_query_agent import flight_query_agent
from agents.confirm_booking_agent import confirm_booking_agent

load_dotenv()
logger = logging.getLogger("inbound-flight-agent")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
THINKING_SOUND_PATH = os.path.join(DATA_DIR, "thinking.wav")

FLIGHT_SEARCH_DATA_FILE = os.path.join(DATA_DIR, "flight_search_data.json")
PASSENGER_DATA_FILE = os.path.join(DATA_DIR, "passenger_data.json")
SELECTED_FLIGHT_FILE = os.path.join(DATA_DIR, "selected_flight.json")
FLIGHT_LIST_FILE = os.path.join(DATA_DIR, "flight_list.json")

flight_memory = JSONMemory(FLIGHT_SEARCH_DATA_FILE)
passenger_memory = JSONMemory(PASSENGER_DATA_FILE)
selected_flight_memory = JSONMemory(SELECTED_FLIGHT_FILE)
flight_list_memory = JSONMemory(FLIGHT_LIST_FILE)

WELCOME_MESSAGE = """
Hello! Welcome to AKIJ AIR's booking assistant.  
How can I assist you today?
"""

INSTRUCTIONS = """
You are a friendly and professional flight booking assistant for AKIJ AIR.  
Your goal is to help users book flights by collecting flight details, passenger information, and confirming bookings.  
- Start by asking for flight details (origin, destination, date, etc.) if not provided.  
- Selecting a flight from options.
- Collect passenger details based on the number of travelers.  
- Offer flight options and confirm the booking.  
- Use the provided tools to search flights, save data, and confirm bookings.  
- Respond warmly, clearly, and professionally.  
"""

class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()

    @llm.ai_callable(description="Extract and save flight search details from user input")
    async def extract_flight_info(self, user_input: str):
        logger.info(f"Extracting flight info: {user_input}")
        return extract_flight_details(user_input, user_id="voice_user")

    @llm.ai_callable(description="Select a flight from available options based on user input")
    async def select_flight(self, user_input: str):
        logger.info(f"Selecting flight: {user_input}")
        return flight_selection_agent(user_input)

    @llm.ai_callable(description="Collect passenger details from user input")
    async def collect_passenger_info(self, user_input: str):
        logger.info(f"Collecting passenger info: {user_input}")
        extracted = extract_passenger_details(user_input)
        flight_details = flight_memory.load_data() or {}
        num_adults = flight_details.get("num_adults", 1)
        num_children = flight_details.get("num_children", 0)
        existing = passenger_memory.load_data() or {"passengers": []}
        passenger_index = next((i for i, p in enumerate(existing.get("passengers", [])) if not all(p.get(f) for f in p)), len(existing.get("passengers", [])))
        return collect_passenger_details(passenger_index=passenger_index, flight_type=flight_details.get("flight_type", "domestic"), **extracted)

    @llm.ai_callable(description="Confirm the flight booking")
    async def confirm_booking(self, user_input: str):
        logger.info(f"Confirming booking for input: {user_input}")
        return confirm_booking_agent()

    @llm.ai_callable(description="Answer general or fallback queries smartly")
    async def smart_assist(self, user_input: str):
        return smart_assistant_agent(user_input, user_id="voice_user")

    @llm.ai_callable(description="Detect the user's language from a given location text")
    async def detect_language(self, location_text: str):
        return detect_language_from_text(location_text)

    @llm.ai_callable(description="Answer flight-related questions from user input")
    async def query_flights(self, user_input: str):
        return flight_query_agent(user_input)

    @llm.ai_callable(description="Use the unified agent selector logic for flexible input handling")
    async def use_selector(self, user_input: str):
        return select_agent(user_input, user_id="voice_user")

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=INSTRUCTIONS + "\nUse the provided functions to assist with flight booking tasks step-by-step."
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant connected: {participant.identity}")

    dg_model = "nova-2-general"
    if participant.kind == ParticipantKind.PARTICIPANT_KIND_SIP:
        dg_model = "nova-2-phonecall"

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model=dg_model),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=elevenlabs.TTS(),
        turn_detector=turn_detector.EOUModel(),
        min_endpointing_delay=0.5,
        max_endpointing_delay=20.0,
        chat_ctx=initial_ctx,
        fnc_ctx=AssistantFnc(),
    )

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage Summary: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the VoicePipelineAgent
    agent.start(ctx.room, participant)

    # --- BACKGROUND THINKING AUDIO (ONLY thinking.wav when thinking) ---
    thinking_audio = AudioConfig(
        file_path=THINKING_SOUND_PATH,
        volume=0.8
    )

    background_audio = BackgroundAudioPlayer(
        ambient_sound=None,           # No ambient sound
        thinking_sound=[thinking_audio]  # Only thinking sound
    )

    await background_audio.start(room=ctx.room, agent_session=agent.agent_session)
    # --- END BACKGROUND AUDIO ---

    # Start by greeting the user
    await agent.say(WELCOME_MESSAGE, allow_interruptions=True)

    # Ask for language selection
    language_prompt = (
        "For Bangla (Bangladesh), press 1. "
        "For English, press 2. "
        "If no input is received, English will be selected automatically."
    )
    await agent.say(language_prompt, allow_interruptions=False)

    # Listen for DTMF input
    try:
        dtmf_input = await agent.listen_for_dtmf(timeout=5.0)  # 5 seconds timeout
    except asyncio.TimeoutError:
        dtmf_input = None

    selected_language = "english"  # Default

    if dtmf_input == "1":
        selected_language = "bangla"
    elif dtmf_input == "2":
        selected_language = "english"

    logger.info(f"Selected language: {selected_language}")

    if selected_language == "bangla":
        agent.chat_ctx.messages[0].text = "আপনি এখন বাংলা ভাষায় সহায়তা পাবেন। দয়া করে আপনার ফ্লাইট সংক্রান্ত তথ্য প্রদান করুন।"
        await agent.say("আপনি বাংলা ভাষা নির্বাচন করেছেন। এখন শুরু করা যাক!", allow_interruptions=True)
    else:
        await agent.say("You have selected English. Let's get started!", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="akij-inbound-flight-agent",
        )
    )
