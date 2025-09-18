# 🚁🌐 Tello Drone Agent Web UI Setup Guide

This guide will help you set up and run the comprehensive web interface for your Tello drone agent.

## 📋 What You Get

- **Real-time Video Stream**: Live camera feed from the drone
- **Manual Controls**: Direct drone movement controls via web interface
- **Voice Commands**: Continue using speech input while monitoring via web
- **System Logs**: Real-time display of all drone operations
- **Drone Status**: Battery, height, flight status, movement tracking
- **Vision Analysis**: AI-powered image analysis with results display

## 🚀 Quick Start

### 1. Install Additional Python Dependencies

```bash
# Install web server dependencies
pip install -r webui_requirements.txt
```

### 2. Install Node.js Dependencies

```bash
# Navigate to webui directory
cd webui

# Install React dependencies
npm install
```

### 3. Start the System

**Option A: Full Setup (2 terminals)**

Terminal 1 - Start Drone Agent:
```bash
# Vision-only mode (safe simulation)
python web_drone_agent.py

# Real drone mode
python web_drone_agent.py --real-drone
```

Terminal 2 - Start Web UI:
```bash
cd webui
npm start
```

**Option B: Easy Startup (Windows)**

```bash
# Start drone agent
python web_drone_agent.py

# In another terminal, use the startup script
cd webui
start.bat
```

### 4. Access the Interface

- **Web UI**: http://localhost:3000
- **Drone Agent**: Running on port 8080 (WebSocket server)

## 🎮 Usage Modes

### Hybrid Mode (Default)
- Voice commands via microphone + Web UI controls
- Best of both worlds - hands-free and visual control

```bash
python web_drone_agent.py
```

### Web UI Only Mode
- Pure web interface, no speech processing
- Good for environments where microphone isn't available

```bash
python web_drone_agent.py --web-only
```

### Voice Only Mode  
- Original speech-only interface
- No web UI server running

```bash
python web_drone_agent.py --no-web-ui
```

## 🌐 Web Interface Features

### Main Panel - Video & Controls
- **Live Video Stream**: Real-time camera feed
- **Movement Controls**: Forward, back, left, right, up, down
- **Flight Controls**: Take off, land, emergency stop
- **Rotation**: Clockwise/counter-clockwise turns
- **Vision Analysis**: AI-powered image analysis

### Side Panel - Status & Logs
- **Drone Status**: Battery %, height, flight state, movement count
- **Connection Status**: WebSocket connection indicator
- **System Logs**: Real-time operation logs with timestamps
- **Last Analysis**: Most recent vision analysis results

### Safety Features
- **Conservative Limits**: 30cm movement increments for safety
- **Status Monitoring**: Real-time battery and height tracking
- **Emergency Stop**: Always available regardless of flight state
- **Connection Monitoring**: Clear indication of system status

## 🔧 Troubleshooting

### Web UI Won't Connect
1. Ensure drone agent is running: `python web_drone_agent.py`
2. Check port 8080 is not blocked by firewall
3. Verify WebSocket connection in browser developer tools

### Video Stream Issues
1. For real drone: Check Tello is connected and camera is working
2. For simulation: Video shows "SIMULATION MODE" with status overlay
3. Refresh browser page to restart video connection

### Command Timeouts
1. Commands have 15-second timeout
2. Check drone battery level (low battery affects performance)
3. Ensure drone has sufficient space for movements

### Audio Issues (Hybrid Mode)
1. Check microphone permissions in browser
2. Verify Azure OpenAI credentials are set
3. Switch to `--web-only` mode if speech isn't needed

## 📱 Mobile Compatibility

The web interface is responsive and works on mobile devices:
- **Portrait Mode**: Stacked layout for small screens
- **Landscape Mode**: Side-by-side layout for tablets
- **Touch Controls**: All buttons are touch-friendly

## 🔐 Security Notes

- Web UI runs on localhost only (not exposed to internet)
- WebSocket connections are local network only
- No external API calls from the frontend
- Azure OpenAI credentials only used in Python backend

## 🎯 Advanced Usage

### Custom Movement Distances
Modify the control buttons in `webui/src/App.js` to change movement distances:

```javascript
// Change from 30cm to different value
onClick={() => executeCommand('move_forward', { distance: 50 })}
```

### Extended Logging
The system maintains the last 100 log entries. Logs automatically scroll to show latest entries.

### Video Quality
Video stream is optimized for real-time display at ~10 FPS with 80% JPEG quality for performance.

## 🚨 Emergency Procedures

1. **Emergency Stop**: Always available via red "Emergency Stop" button
2. **Manual Land**: Use "Land" button if drone becomes unresponsive
3. **Power Off**: Physically power off Tello if all else fails
4. **System Restart**: Restart both drone agent and web UI if needed

## 💡 Tips for Best Experience

1. **Use Chrome/Edge**: Best WebSocket and video performance
2. **Local Network**: Keep drone close to WiFi for stable connection
3. **Battery Monitoring**: Land when battery drops below 20%
4. **Clear Space**: Ensure 2+ meters clearance in all directions
5. **Lighting**: Good lighting improves vision analysis accuracy

## 📞 Support

If you encounter issues:
1. Check the system logs in the web interface
2. Look at terminal output from the drone agent
3. Verify all dependencies are installed correctly
4. Test with `--vision-only` mode first before using real drone