# Agentic Drone

## 🧩 Problem / Opportunity

Traditional drone operations rely heavily on manual control or rigid pre-programmed routines, limiting their adaptability in dynamic environments. Operators must translate high-level goals into granular commands, which is time-consuming and error-prone—especially in high-stakes scenarios like search and rescue, surveillance, or industrial inspection.

The opportunity lies in creating an agentic drone system powered by real-time GPT intelligence that can interpret natural language goals, autonomously break them down into executable micro-tasks, and adapt on the fly. This unlocks a new paradigm of human-drone interaction—fluid, intuitive, and context-aware.

## 🎯 Target Audience / Users

- **Field Operators & First Responders:** Emergency personnel who need drones to act quickly and intelligently in unpredictable environments.
- **Industrial Inspectors:** Professionals in oil & gas, infrastructure, or utilities who require autonomous inspection routines.
- **Defense & Security Agencies:** Tactical teams needing real-time reconnaissance with minimal manual intervention.
- **Researchers & Developers:** AI and robotics teams exploring agentic systems and autonomous task execution.
- **Enterprise Automation Leads:** Innovators looking to integrate drones into broader intelligent workflows.

## 🚀 Use Cases

- **Search & Rescue:** Ask the drone to look for people in a disaster zone
- **Inspection:** Tell it to check for damage on a bridge or building
- **Agriculture:** Request a crop health scan across a field
- **Security:** Set it to patrol a perimeter and report anything unusual
- **Event Coverage:** Use it to monitor crowd movement or traffic flow

## 💼 Opportunity for Microsoft

- **Copilot for the Physical World:** Extend Copilot beyond screens into drones, robots, and autonomous agents
- **Azure as the Agentic Backbone:** Use Azure for real-time reasoning, data processing, and fleet orchestration
- **Platform Play:** Build APIs and SDKs for developers to create their own embodied agents

## How the Demo Works

In the demo, the user speaks naturally to the drone. A Python backend streams audio, vision, and telemetry to an Azure GPT Realtime model, which interprets intent, decomposes it into tool calls, and safely executes flight actions via the Tello SDK. Azure AI Vision assists with richer scene understanding when needed.

- **React Web UI** – Real-time dashboard: video feed, battery, speech transcript, interaction log, and quick controls.
- **Python Backend** – Orchestrates drone control, model sessions, audio, vision, and tool execution pipeline.
- **GPT Realtime Model** – Core reasoning engine: converts spoken intent into structured micro-tasks (tools) with safety policies.
- **Azure AI Vision** – Augmented perception for object detection, spatial awareness, and navigation decisions.
- **Tello SDK** – Flight primitives (takeoff, move, rotate, stream video) plus higher-level maneuvers (e.g., curves).
- **Tool Abstraction Layer** – Each drone capability (e.g., move_forward, rotate_cw) is exposed as a callable tool the model can sequence.
- **Real-Time Speech Loop** – Low-latency bidirectional audio: user intent in, synthesized confirmations and status out.
- **Safety & Guardrails** – System prompt + runtime checks enforce altitude limits, battery thresholds, and restricted motions.

Flow (high level):

1. User speaks a goal (“Scan left side for obstacles.”)
2. Speech → text; model interprets context + recent frames.
3. Model plans: (adjust yaw) → (move forward 1m) → (capture frame) → (analyze) → (report).
4. Backend validates and executes each tool call via SDK.
5. Vision results + telemetry are fed back to refine the next step.
6. Model narrates progress to the user.

## Project Structure

```
TelloDroneAgent/
├── src/
│   ├── agents/
│   │   ├── autonomous_drone_agent.py      # Azure OpenAI control agent
│   │   └── vision_agent.py                # Azure AI Vision agent
│   ├── drone/
│   │   ├── simple_tello.py                # Tello drone interface
│   │   └── commands.py                    # Drone command definitions
│   ├── vision/
│   │   ├── camera_manager.py              # Camera abstraction (Tello/Webcam)
│   │   └── object_detector.py             # Object detection logic
│   ├── config/
│   │   └── settings.py                    # Configuration management
│   └── main.py                            # Main application entry
|     
├── web_drone_agent.py                     # Main python file to run for backend
|
|__ webui/                                 # React Frontend 
|
└── README.md
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Azure services:
   - Create gpt-realtime resource
   - Create Azure AI Agent              - Optional
   - Create Azure AI Vision resource    - Optional


3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

4. Run the application:
   ```bash
   python src/main.py
   ```

## Usage Modes

The platform supports multiple run configurations depending on what you want to test (simulation, real drone, speech control, or just the web UI).

### 1. Hybrid Mode (Default)
Runs speech control + web server + vision simulation.

```bash
python web_drone_agent.py
```

Starts the backend (port 8080) and enables speech if Azure env vars are set.

### 2. Start the Web UI (Frontend)
Run this in a separate terminal:
```bash
cd webui
npm install   # first time only
npm start
```
Open http://localhost:3000.

### 3. Web UI Only Mode
Disable speech / realtime model, keep manual + status UI:
```bash
python web_drone_agent.py --web-only
```

### 4. Real Drone Mode
Connect to a physical Tello (must be on its Wi‑Fi):
```bash
python web_drone_agent.py --real-drone
```
Combine flags as needed:
```bash
python web_drone_agent.py --real-drone --web-only
```

### 5. Speech Only (No Web UI)
```bash
python web_drone_agent.py --no-web-ui
```
Useful for headless / audio-only testing.

### 6. Environment Variables Required for Speech
Set at least:
```powershell
# PowerShell
$env:AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
$env:AZURE_OPENAI_API_KEY="your-api-key"
$env:AZURE_OPENAI_REALTIME_DEPLOYMENT="gpt-4o-realtime-preview"
```
Optional enhancements:
```powershell
$env:AZURE_OPENAI_GPT4O_DEPLOYMENT="gpt-4o"
$env:AZURE_AI_VISION_ENDPOINT="https://your-vision-resource.cognitiveservices.azure.com"
$env:AZURE_AI_VISION_KEY="your-vision-key"
```
You can instead copy `.env.example` to `.env` and fill values.

### 7. Quick End-to-End
```bash
python web_drone_agent.py          # backend
cd webui && npm start              # frontend (new terminal)
```
Speak a goal or use the on‑screen controls.


## License

MIT License
