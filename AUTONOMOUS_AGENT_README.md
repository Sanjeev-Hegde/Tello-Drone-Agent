# 🚁 Autonomous Drone Agent

An intelligent drone controller that takes natural language commands and autonomously controls a Tello drone using computer vision and Azure AI.

## ✨ Features

### 🧠 **Intelligent Command Processing**
- Natural language input via text or speech
- Understands complex commands like "explore the room" or "find a red object"
- Contextual awareness from previous conversations and actions

### 👁️ **Vision-Based Navigation**
- **Smart Movement**: Always captures images before moving to detect obstacles
- **Object Detection**: Uses GPT-4o multimodal to analyze camera feed
- **Safe Navigation**: Avoids obstacles and plans safe flight paths

### 🛡️ **Safety-First Design**
- **No Direct Side Movement**: Rotates first to see direction before moving left/right
- **Incremental Steps**: Small movements (20-50cm) to prevent crashes
- **Continuous Monitoring**: Checks environment before every action
- **Emergency Stop**: Immediate halt capability

### 🎯 **Autonomous Decision Making**
- Decides when to capture images based on task context
- Plans multi-step actions to achieve user goals
- Learns from visual feedback and conversation history
- Adapts strategy based on detected obstacles

## 🏗️ Architecture

```
User Input (Text/Speech)
     ↓
Azure AI Agent (GPT-4o)
     ↓
Autonomous Decision Engine
     ↓
┌─────────────────┬─────────────────┐
│  Vision System  │  Flight Control │
│  - Image        │  - SimpleTello  │
│    Capture      │    Integration  │
│  - GPT-4o       │  - Movement     │
│    Analysis     │    Commands     │
│  - Obstacle     │  - Safety       │
│    Detection    │    Protocols    │
└─────────────────┴─────────────────┘
```

## 📋 Core Principles

1. **Safety First**: Always analyze environment before moving
2. **Small Steps**: Take incremental movements (20-50cm) to avoid crashes  
3. **Vision-Guided**: Capture images before major movements to see obstacles
4. **Rotate Before Side Movement**: Never fly left/right directly - rotate first
5. **Remember Context**: Use previous images and conversation to make decisions

## 🛠️ Available Tools

| Tool | Purpose | Safety Features |
|------|---------|----------------|
| `takeoff` | Safe drone takeoff | Checks flight status |
| `land` | Safe landing | Verifies ground proximity |
| `move_forward` | Forward movement | Image analysis first |
| `move_back` | Backward movement | Distance limits |
| `move_up/down` | Vertical movement | Height monitoring |
| `rotate_clockwise/ccw` | Rotation for vision | Prepares for safe movement |
| `capture_image_and_analyze` | Computer vision | GPT-4o multimodal analysis |
| `get_drone_status` | Status monitoring | Battery, height, state |
| `emergency_stop` | Immediate halt | Emergency safety |

## 🚀 Usage

### Basic Setup

```python
from agents.autonomous_drone_agent import AutonomousDroneAgent

# Create agent (vision-only for testing)
agent = AutonomousDroneAgent(vision_only=True)

# Process user command
response = await agent.process_user_command("Take off and explore the room")

# Get status
context = agent.get_conversation_context()

# Cleanup
agent.cleanup()
```

### Real Drone Usage

```python
# For real Tello drone (requires physical drone)
agent = AutonomousDroneAgent(vision_only=False)
```

## 🎮 Example Commands

### Basic Navigation
- `"Take off and look around"`
- `"Move forward slowly"`
- `"Rotate to see what's behind me"`
- `"Land safely"`

### Vision-Based Tasks
- `"Capture an image and tell me what you see"`
- `"Look for obstacles before moving"`
- `"Find a red object in the room"`
- `"Check if the path ahead is clear"`

### Autonomous Exploration
- `"Explore the room and map out objects"`
- `"Navigate to the kitchen"`
- `"Find a safe landing spot"`
- `"Avoid the furniture and move around it"`

### Smart Navigation
- `"I want to go left - do it safely"` *(Agent will rotate first, then move forward)*
- `"Move to the right side of the room"` *(Agent will plan safe path)*
- `"Go around that obstacle"` *(Agent will analyze and navigate)*

## 🧪 Testing Modes

### Vision-Only Mode (Recommended for Testing)
```python
agent = AutonomousDroneAgent(vision_only=True)
```
- ✅ Safe testing without real drone
- ✅ Simulated flight and image analysis  
- ✅ Full conversation and decision logic
- ✅ No risk of crashes or damage

### Real Drone Mode
```python
agent = AutonomousDroneAgent(vision_only=False)
```
- 🚁 Controls actual Tello drone
- 📹 Real camera feed analysis
- ⚡ Physical movement commands
- ⚠️ Requires careful testing in safe environment

## 📊 State Management

The agent maintains comprehensive state:

```python
context = agent.get_conversation_context()
# Returns:
{
    "drone_state": {
        "is_flying": bool,
        "battery": int,
        "height": int,
        "movement_count": int,
        "obstacles_detected": [str],
        "last_image_analysis": str
    },
    "recent_conversation": [conversation_history],
    "recent_images": [image_analyses],
    "mode": "VISION_ONLY" | "REAL_DRONE"
}
```

## 🔧 Integration Requirements

### Dependencies
```bash
pip install azure-ai-projects azure-identity opencv-python numpy djitellopy
```

### Configuration
Set up `config/settings.py` with Azure AI Projects credentials:
```python
azure_ai_project_endpoint = "your_endpoint_here"
```

### Azure AI Projects Setup
1. Create Azure AI Projects resource
2. Deploy GPT-4o model
3. Configure authentication

## 🛡️ Safety Protocols

### Movement Safety
- **Image Analysis First**: Always captures and analyzes view before moving
- **Distance Limits**: Maximum 100cm movements, recommended 20-50cm
- **Obstacle Detection**: Identifies walls, furniture, people, pets
- **Emergency Stop**: Immediate halt capability

### Navigation Logic
- **Smart Side Movement**: Rotates first to see direction, then moves forward
- **Incremental Progress**: Small steps with continuous monitoring
- **Path Planning**: Analyzes safe routes before execution
- **Contextual Memory**: Remembers obstacles and safe areas

### Battery & Status Monitoring
- **Continuous Monitoring**: Checks battery and height regularly
- **Low Battery Warnings**: Alerts for landing when battery low
- **Flight Status**: Tracks takeoff/landing state
- **Movement Counter**: Logs all movements for analysis

## 🎯 Use Cases

### Home Exploration
- Room mapping and navigation
- Object detection and identification
- Security monitoring
- Pet/family member detection

### Educational/Research
- Computer vision algorithm testing
- Autonomous navigation research
- AI decision-making studies
- Human-robot interaction

### Commercial Applications
- Indoor inspection tasks
- Inventory management
- Surveillance applications
- Delivery preparation

## 🚨 Important Notes

⚠️ **Always test in VISION_ONLY mode first**
⚠️ **Ensure adequate space for drone operations**
⚠️ **Keep emergency stop accessible**
⚠️ **Monitor battery levels continuously**
⚠️ **Test in safe, obstacle-free environment initially**

## 🔄 Workflow Example

1. **User**: *"Explore the living room and find my keys"*
2. **Agent**: *Analyzes command, decides to take off*
3. **Agent**: *Captures image, analyzes room layout*
4. **Agent**: *Plans systematic exploration pattern*
5. **Agent**: *Moves incrementally, rotating to scan areas*
6. **Agent**: *Identifies objects, looking for keys*
7. **Agent**: *Reports findings and returns to start*
8. **Agent**: *Lands safely at designated spot*

## 📈 Advanced Features

- **Contextual Memory**: Remembers previous conversations and images
- **Object Tracking**: Tracks objects across multiple image captures  
- **Adaptive Planning**: Adjusts strategy based on environment
- **Voice Integration**: Ready for speech-to-text input
- **Multi-Modal Analysis**: Combines visual and textual reasoning

---

🚁 **The AutonomousDroneAgent represents the next generation of intelligent drone control - combining natural language understanding, computer vision, and autonomous decision-making for safe and effective drone operations.**
