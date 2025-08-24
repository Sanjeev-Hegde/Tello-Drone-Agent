# Tello Camera Integration Guide

This guide shows how to use your Tello drone's camera with the vision analysis system.

## Quick Start

### Option 1: Use Main Application with Tello Camera

```bash
# Vision-only mode with Tello camera (no flight control)
python src/main.py --vision-only --camera-source tello

# Full mode with Tello camera and flight control
python src/main.py --camera-source tello
```

### Option 2: Use the Demo Script

```bash
# Run the dedicated Tello vision demo
python examples/tello_vision_demo.py
```

## Setup Requirements

### 1. Hardware Setup
- ✅ Power on your Tello drone
- ✅ Wait for the LED to become solid (not blinking)
- ✅ Make sure Tello battery is > 20%

### 2. Network Connection
- ✅ Connect your computer to Tello's WiFi network
- ✅ Network name: `TELLO-XXXXXX` (check sticker on drone)
- ✅ Password: Usually none (open network)
- ✅ Wait for connection to establish

### 3. Test Connection
```bash
# Test if Tello is reachable
ping 192.168.10.1
```

## What You'll Get

### Vision Analysis Features
- 🎯 **Object Detection**: Identifies objects, people, and animals
- 📝 **Scene Description**: Natural language description of what Tello sees
- 🏷️ **Image Tags**: Detailed tags about scene content
- 📍 **Dense Captions**: Multiple descriptions of different image regions
- 🚨 **Safety Navigation**: Alerts for people, obstacles, and flight hazards

### Example Output
```
📋 ANALYSIS RESULTS:
   Description: a person standing in a room with furniture
   Objects: 2 detected
     - person (0.89)
     - chair (0.67)
   People: 1 detected
   Tags: person, indoor, furniture, room, standing
   🚨 Safety: Caution: 1 people detected - maintain safe distance
```

## Vision-Only vs Full Mode

### Vision-Only Mode (`--vision-only`)
- ✅ Connects to Tello camera for video
- ✅ Analyzes video frames with AI
- ✅ Shows analysis results
- ❌ No drone flight control
- ✅ **SAFE**: Won't move the drone

### Full Mode (default)
- ✅ All vision-only features
- ✅ Natural language flight commands
- ✅ Autonomous navigation based on vision
- ⚠️ **CAUTION**: Can control drone flight

## Troubleshooting

### Connection Issues
```
❌ TELLO CONNECTION FAILED
```

**Solutions:**
1. **Check Power**: LED should be solid, not blinking
2. **Check WiFi**: Connected to TELLO-XXXXXX network?
3. **Test Network**: `ping 192.168.10.1` should respond
4. **Close Other Apps**: DJI GO, other Tello apps
5. **Restart Drone**: Power off/on the Tello

### Low Battery Warning
```
⚠️ Low battery! Consider charging before extended use.
```
- Charge Tello battery before use
- Battery below 20% may cause connection issues

### Video Stream Issues
- Check if other applications are using Tello camera
- Restart the application
- Power cycle the Tello drone

## Camera Source Options

You can specify the camera source in several ways:

### Environment Variable (.env file)
```env
CAMERA_SOURCE=tello
```

### Command Line
```bash
python src/main.py --camera-source tello
```

### Available Sources
- `webcam`: Use computer's webcam
- `tello`: Use Tello drone camera

## Integration with Azure AI Vision

The system uses Azure AI Vision for analysis, providing:
- Advanced object detection
- Scene understanding
- People detection and tracking
- Safety recommendations for drone navigation

All analysis happens in real-time as Tello streams video.
