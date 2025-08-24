# Tello Drone AI Agent Project

A Python project that integrates two AI agents to control a Tello drone using natural language and provide real-time video analysis.

## Features

- **Control Agent**: Uses Azure OpenAI to convert natural language commands to drone control JSON
- **Vision Agent**: Uses Azure AI Vision for real-time object detection and analysis
- **Tello SDK Integration**: Full drone control capabilities
- **Vision-Only Mode**: Test vision features without drone using computer camera
- **Audio Input Support**: Voice commands for hands-free operation

## Project Structure

```
TelloDroneAgent/
├── src/
│   ├── agents/
│   │   ├── control_agent.py      # Azure OpenAI control agent
│   │   └── vision_agent.py       # Azure AI Vision agent
│   ├── drone/
│   │   ├── tello_controller.py   # Tello drone interface
│   │   └── commands.py           # Drone command definitions
│   ├── vision/
│   │   ├── camera_manager.py     # Camera abstraction (Tello/Webcam)
│   │   └── object_detector.py    # Object detection logic
│   ├── config/
│   │   └── settings.py           # Configuration management
│   └── main.py                   # Main application entry
├── tests/
├── examples/
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Azure services:
   - Create Azure OpenAI resource
   - Create Azure AI Vision resource
   - Create Azure Key Vault (recommended for secure credential storage)

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

### Full Drone Mode
- Connects to Tello drone
- Processes natural language commands
- Provides real-time vision analysis

### Vision-Only Mode
- Uses computer camera for testing
- Vision analysis without drone control
- Perfect for development and testing

## Example Commands

- "Take off and fly forward for 2 meters"
- "Find how many chairs are in the room"
- "Land on the table"
- "Scan the room and count people"

## Security

This project follows Azure security best practices:
- Uses Managed Identity when possible
- Credentials stored in Azure Key Vault
- No hardcoded secrets
- Proper error handling and logging

## License

MIT License
