# AKIJ AIR Voice Booking Agent
This project is a Python-based voice agent for AKIJ AIR, designed to handle inbound calls and assist users with flight bookings using LiveKit. It includes features like turn detection, function calling, usage logging, and Krisp noise cancellation for a professional voice interaction experience.

## ✨ Features

Voice Interaction: Engage users with natural, voice-based flight booking assistance.
Language Support: Supports English and Bangla with DTMF-based language selection.
Flight Booking: Collects flight and passenger details, searches flights, and confirms bookings.
Background Audio: Plays a "thinking" sound during processing for a better user experience.
Modular Agents: Handles tasks like flight search, passenger details, and booking confirmation separately for better maintainability.


## 🔧 Prerequisites
Make sure you have the following installed and ready:

- Python 3.11 or higher
- Git
- LiveKit CLI (optional, for SIP and inbound call configuration)
- Code editor (e.g., VS Code)
- API access for:
- OpenAI
- Deepgram
- ElevenLabs
- AssemblyAI
- DeepSeek
- LangSmith (optional)


## A Twilio account (or similar) for inbound call support


### 🚀 Setup Instructions
- 1. Clone the Repository
git clone https://github.com/your-username/akij-air-voice-agent.git
cd akij-air-voice-agent

- 2. Create a Virtual Environment
Set up a virtual environment to manage dependencies.
Linux/macOS
python3 -m venv myenv
source myenv/bin/activate

- Windows
python3.11 -m venv myenv
myenv\Scripts\activate.bat

- 3. Install Dependencies
Install the required Python packages:
pip install -r requirements.txt

- 4. Download Required Files
Download necessary data files (e.g., thinking.wav):
python agent.py download-files


## 🔑 Configuration
Configure the environment by setting up API keys and URLs.

Create the .env File:
Copy the .env.example (if provided) to .env:
cp .env.example .env


Edit the .env File:
Add your API keys and configuration:
# API Keys
- API_KEY=your_api_key
SECRET_CODE=your_secret_code
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
LANGSMITH_API_KEY=your_langsmith_key
ASSEMBLYAI_API_KEY=your_assemblyai_key
DEEPGRAM_API_KEY=your_deepgram_key
ELEVEN_API_KEY=your_elevenlabs_key

# API URLs
FLIGHT_API_URL=https://serviceapi.innotraveltech.com/flight/search
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
BASE_URL=https://serviceapi.innotraveltech.com/flight/validate

# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://akij-inbound-flight-agent-rybk7ozs.livekit.cloud


Optional: Use LiveKit CLI:
Alternatively, configure the environment using:
lk app env




🏃 Running the Agent
Start the voice agent in development mode:
python agent.py dev

The agent will:

Greet users with a welcome message.
Prompt for language selection (Bangla: press 1, English: press 2).
Handle flight booking tasks via voice interaction.


📞 Enabling Inbound Calls
To enable inbound calls using Twilio, configure a SIP trunk and dispatch rule with LiveKit Cloud.
1. Install LiveKit CLI
brew update && brew install livekit-cli

2. Authenticate with LiveKit Cloud
lk cloud auth

Follow the browser instructions to log in.
3. Obtain a Phone Number
Get a phone number from Twilio or another SIP provider.
4. Create a SIP Trunk
Edit inbound-trunk.json to include Twilio’s regional IP addresses in allowed_addresses. Krisp noise cancellation is enabled by default.
lk sip inbound create inbound-trunk.json

Note the SIPTrunkID (e.g., ST_MZFiM5gHr7dH).
5. Create a Dispatch Rule
lk sip dispatch create dispatch-rule.json

Note the SIPDispatchRuleID (e.g., SDR_KqLmjGafcBR9).
6. Link Phone Number
Associate the phone number with the SIP trunk in your SIP provider’s dashboard (e.g., Twilio).
7. Test Inbound Calls
Dial the phone number to interact with the voice agent.

📂 Project Structure
akij-air-voice-agent/
├── agent.py               # Main voice agent script
├── .env                   # Environment variables (not tracked)
├── .gitignore             # Git ignore file
├── requirements.txt       # Python dependencies
├── data/                  # JSON files for flight and passenger data
├── inbound-trunk.json     # SIP trunk configuration
├── dispatch-rule.json     # Dispatch rule configuration
├── run.txt                # Setup and run commands
└── README.md              # Project documentation


🛠️ Troubleshooting

API Key Errors: Ensure all keys in .env are valid.
Dependency Issues: Verify Python 3.11+ is used and re-run pip install -r requirements.txt.
Audio Issues: Confirm thinking.wav is in data/ and the ElevenLabs API key is correct.
SIP Trunk Errors: Check inbound-trunk.json for correct IP addresses and re-run CLI commands.
Logs: Review console output or logs/ directory for errors.


🤝 Contributing
We welcome contributions! To contribute:

Fork the repository.

Create a feature branch:
git checkout -b feature/your-feature


Commit changes:
git commit -m "Add your feature"


Push to the branch:
git push origin feature/your-feature


Open a pull request.


Please adhere to the Code of Conduct (if available).

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

⭐ Star this repo if you find it useful!📩 For questions, open an issue or contact the maintainers.
