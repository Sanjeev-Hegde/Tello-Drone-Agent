import React, { useState, useEffect, useRef } from 'react';
import { 
  Plane, 
  Camera, 
  Terminal, 
  Square, 
  Mic, 
  MicOff, 
  Wifi, 
  WifiOff, 
  Activity,
  PlayCircle,
  Video,
  VideoOff
} from 'lucide-react';
import io from 'socket.io-client';

// Custom Drone Icon Component
const DroneIcon = ({ className }) => (
  <svg 
    className={className} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="0.8" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    {/* Main drone body - thinner */}
    <rect x="10" y="11" width="4" height="2" rx="1" fill="currentColor" stroke="white" strokeWidth="0.3" />
    
    {/* Battery indicator on top */}
    <rect x="11.2" y="11.3" width="1.6" height="0.5" rx="0.1" fill="white" stroke="none" />
    
    {/* Drone arms - thinner but visible */}
    <line x1="10" y1="11.5" x2="5" y2="6.5" strokeWidth="1.2" strokeLinecap="round" />
    <line x1="14" y1="11.5" x2="19" y2="6.5" strokeWidth="1.2" strokeLinecap="round" />
    <line x1="10" y1="12.5" x2="5" y2="17.5" strokeWidth="1.2" strokeLinecap="round" />
    <line x1="14" y1="12.5" x2="19" y2="17.5" strokeWidth="1.2" strokeLinecap="round" />
    
    {/* Motor housings - smaller */}
    <circle cx="5" cy="6.5" r="1.2" fill="currentColor" stroke="white" strokeWidth="0.3" />
    <circle cx="19" cy="6.5" r="1.2" fill="currentColor" stroke="white" strokeWidth="0.3" />
    <circle cx="5" cy="17.5" r="1.2" fill="currentColor" stroke="white" strokeWidth="0.3" />
    <circle cx="19" cy="17.5" r="1.2" fill="currentColor" stroke="white" strokeWidth="0.3" />
    
    {/* Propellers - thinner but more visible */}
    <g strokeWidth="0.8" stroke="white" fill="rgba(255,255,255,0.2)">
      {/* Top-left propeller */}
      <ellipse cx="5" cy="6.5" rx="2.5" ry="0.5" transform="rotate(20 5 6.5)" />
      <ellipse cx="5" cy="6.5" rx="2.5" ry="0.5" transform="rotate(-20 5 6.5)" />
      
      {/* Top-right propeller */}
      <ellipse cx="19" cy="6.5" rx="2.5" ry="0.5" transform="rotate(20 19 6.5)" />
      <ellipse cx="19" cy="6.5" rx="2.5" ry="0.5" transform="rotate(-20 19 6.5)" />
      
      {/* Bottom-left propeller */}
      <ellipse cx="5" cy="17.5" rx="2.5" ry="0.5" transform="rotate(20 5 17.5)" />
      <ellipse cx="5" cy="17.5" rx="2.5" ry="0.5" transform="rotate(-20 5 17.5)" />
      
      {/* Bottom-right propeller */}
      <ellipse cx="19" cy="17.5" rx="2.5" ry="0.5" transform="rotate(20 19 17.5)" />
      <ellipse cx="19" cy="17.5" rx="2.5" ry="0.5" transform="rotate(-20 19 17.5)" />
    </g>
    
    {/* Motor centers */}
    <circle cx="5" cy="6.5" r="0.4" fill="white" stroke="none" />
    <circle cx="19" cy="6.5" r="0.4" fill="white" stroke="none" />
    <circle cx="5" cy="17.5" r="0.4" fill="white" stroke="none" />
    <circle cx="19" cy="17.5" r="0.4" fill="white" stroke="none" />
    
    {/* Front camera gimbal - more visible */}
    <ellipse cx="12" cy="9.5" rx="1.3" ry="0.8" fill="currentColor" stroke="white" strokeWidth="0.3" />
    <circle cx="12" cy="9.5" r="0.8" fill="rgba(0,0,0,0.4)" stroke="none" />
    <circle cx="12" cy="9.5" r="0.6" fill="currentColor" stroke="white" strokeWidth="0.2" />
    <circle cx="12" cy="9.5" r="0.4" fill="rgba(0,0,0,0.7)" stroke="none" />
    <circle cx="11.8" cy="9.3" r="0.1" fill="white" stroke="none" opacity="0.9" />
    
    {/* Landing gear - thinner */}
    <rect x="10.5" y="13.2" width="0.4" height="1" rx="0.2" fill="currentColor" stroke="none" />
    <rect x="13.1" y="13.2" width="0.4" height="1" rx="0.2" fill="currentColor" stroke="none" />
    <rect x="10" y="14" width="1.4" height="0.2" rx="0.1" fill="currentColor" stroke="none" />
    <rect x="12.6" y="14" width="1.4" height="0.2" rx="0.1" fill="currentColor" stroke="none" />
    
    {/* Status LED - more visible */}
    <circle cx="12" cy="12" r="0.25" fill="lime" stroke="none" opacity="0.9" />
    
    {/* Antenna */}
    <line x1="12" y1="8.5" x2="12" y2="7.5" strokeWidth="0.3" />
    <circle cx="12" cy="7.5" r="0.15" fill="white" stroke="none" />
  </svg>
);

function App() {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(true);
  const [videoStreamingEnabled, setVideoStreamingEnabled] = useState(false);
  const [isExecutingCommand, setIsExecutingCommand] = useState(false);
  const [videoFrame, setVideoFrame] = useState(null);
  
  const [droneStatus, setDroneStatus] = useState({
    isFlying: false,
    battery: 100,
    height: 0,
    movementCount: 0,
    speechEnabled: true,
    videoStreamingEnabled: false
  });
  
  const [logs, setLogs] = useState([
    { message: "System initialized", timestamp: new Date().toLocaleTimeString(), level: "info" },
    { message: "Waiting for drone connection", timestamp: new Date().toLocaleTimeString(), level: "warning" }
  ]);
  
  const logsRef = useRef(null);

  useEffect(() => {
    const newSocket = io('http://localhost:8080');
    
    newSocket.on('connect', () => {
      console.log('Connected to drone agent');
      setConnected(true);
      addLog('Connected to drone agent', 'success');
    });
    
    newSocket.on('disconnect', () => {
      console.log('Disconnected from drone agent');
      setConnected(false);
      addLog('Disconnected from drone agent', 'error');
    });
    
    newSocket.on('drone_status', (status) => {
      setDroneStatus(status);
      if (status.speechEnabled !== undefined) {
        setSpeechEnabled(status.speechEnabled);
      }
      if (status.videoStreamingEnabled !== undefined) {
        setVideoStreamingEnabled(status.videoStreamingEnabled);
      }
    });
    
    newSocket.on('log', (logData) => {
      addLog(logData.message, logData.level);
    });
    
    newSocket.on('command_complete', (data) => {
      setIsExecutingCommand(false);
      addLog(`Command ${data.command} completed`, 'success');
    });

    newSocket.on('video_frame', (frameData) => {
      // Revoke previous URL to prevent memory leaks
      if (videoFrame) {
        URL.revokeObjectURL(videoFrame);
      }
      
      const blob = new Blob([frameData], { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      setVideoFrame(url);
    });
    
    setSocket(newSocket);
    
    return () => {
      newSocket.close();
      // Clean up video frame URL on unmount
      if (videoFrame) {
        URL.revokeObjectURL(videoFrame);
      }
    };
  }, []);

  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (message, level = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { message, level, timestamp }]);
  };

  const executeCommand = async (command, params = {}) => {
    if (!socket || !connected || isExecutingCommand) return;
    
    setIsExecutingCommand(true);
    addLog(`Executing: ${command}`, 'info');
    
    socket.emit('drone_command', { command, params });
  };

  const toggleSpeech = () => {
    setSpeechEnabled(!speechEnabled);
    const action = !speechEnabled ? 'enabled' : 'disabled';
    addLog(`Speech control ${action}`, 'info');
    
    if (socket && connected) {
      socket.emit('speech_toggle', { enabled: !speechEnabled });
    }
  };

  const toggleVideoStream = () => {
    setVideoStreamingEnabled(!videoStreamingEnabled);
    const action = !videoStreamingEnabled ? 'enabled' : 'disabled';
    addLog(`Video streaming ${action}`, 'info');
    
    if (socket && connected) {
      socket.emit('video_toggle', { enabled: !videoStreamingEnabled });
    }
  };

  const getStatusIcon = () => {
    if (!connected) return <WifiOff className="w-5 h-5 text-red-500" />;
    if (droneStatus.isFlying) return <Activity className="w-5 h-5 text-green-500 animate-pulse" />;
    return <Wifi className="w-5 h-5 text-blue-500" />;
  };

  const getLogLevelStyle = (level) => {
    switch (level) {
      case 'error': return 'text-red-400';
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      default: return 'text-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <DroneIcon className="w-10 h-10 text-white" />
            <h1 className="text-4xl font-bold text-white">Agentic Drone</h1>
          </div>
        </div>

        {/* Top Row: Video Stream and System Logs */}
        <div className={`grid gap-6 mb-6 ${videoStreamingEnabled ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
          
          {/* Video Stream - conditionally rendered */}
          {videoStreamingEnabled && (
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <div className="flex items-center space-x-2 mb-4">
                <Camera className="w-5 h-5 text-white" />
                <h2 className="text-xl font-semibold text-white">Live Video Stream</h2>
              </div>
              <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '4/3' }}>
                {videoStreamingEnabled && videoFrame ? (
                  <img 
                    src={videoFrame} 
                    alt="Drone video stream" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-white/60">
                    <div className="text-center">
                      <Camera className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Waiting for video stream...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* System Logs */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="flex items-center space-x-2 mb-4">
              <Terminal className="w-5 h-5 text-white" />
              <h2 className="text-xl font-semibold text-white">System Logs</h2>
            </div>
            <div 
              ref={logsRef}
              className="bg-black/30 rounded-lg p-4 font-mono text-sm overflow-y-auto" 
              style={{ height: '400px' }}
            >
              {logs.length === 0 ? (
                <div className="text-white/40 text-center py-8">
                  <Terminal className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>System logs will appear here...</p>
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-white/40 text-xs">[{log.timestamp}]</span>
                    <span className={`ml-2 ${getLogLevelStyle(log.level)}`}>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Bottom Row: Drone Status and Quick Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Drone Status */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-white" />
                <h2 className="text-xl font-semibold text-white">Drone Status</h2>
              </div>
              <div className="flex items-center space-x-2 text-white/80">
                {getStatusIcon()}
                <span className="text-sm">
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-white">
              <div>
                <p className="text-white/60 text-sm">Flying</p>
                <p className="text-xl font-semibold">
                  {droneStatus.isFlying ? '✈️ Yes' : '🔴 No'}
                </p>
              </div>
              <div>
                <p className="text-white/60 text-sm">Battery</p>
                <p className="text-xl font-semibold">
                  🔋 {droneStatus.battery}%
                </p>
              </div>
              <div>
                <p className="text-white/60 text-sm">Height</p>
                <p className="text-xl font-semibold">
                  📏 {droneStatus.height}cm
                </p>
              </div>
              <div>
                <p className="text-white/60 text-sm">Movements</p>
                <p className="text-xl font-semibold">
                  🎯 {droneStatus.movementCount}
                </p>
              </div>
            </div>
          </div>

          {/* Quick Controls */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="flex items-center space-x-2 mb-4">
              <PlayCircle className="w-5 h-5 text-white" />
              <h2 className="text-xl font-semibold text-white">Quick Controls</h2>
            </div>
            
            <div className="space-y-3">
              {/* Flight Controls and Analysis in one row */}
              <div className="flex space-x-2">
                <button
                  onClick={() => executeCommand('takeoff')}
                  disabled={droneStatus.isFlying || isExecutingCommand}
                  className={`flex-1 flex items-center justify-center space-x-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    droneStatus.isFlying || isExecutingCommand
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  <Plane className="w-3 h-3" />
                  <span>Take Off</span>
                </button>
                <button
                  onClick={() => executeCommand('land')}
                  disabled={!droneStatus.isFlying || isExecutingCommand}
                  className={`flex-1 flex items-center justify-center space-x-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    !droneStatus.isFlying || isExecutingCommand
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-red-600 hover:bg-red-700 text-white'
                  }`}
                >
                  <Square className="w-3 h-3" />
                  <span>Land</span>
                </button>
                <button
                  onClick={() => executeCommand('capture_and_analyze_image', { focus: 'objects' })}
                  disabled={isExecutingCommand}
                  className={`flex-1 flex items-center justify-center space-x-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isExecutingCommand
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  <Camera className="w-3 h-3" />
                  <span>Analyze</span>
                </button>
              </div>

              {/* Control Toggles */}
              <div className="pt-2 border-t border-white/20 space-y-3">
                {/* Speech Control */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {speechEnabled ? (
                      <Mic className="w-4 h-4 text-green-400" />
                    ) : (
                      <MicOff className="w-4 h-4 text-red-400" />
                    )}
                    <span className="text-white font-medium">Speech Control</span>
                  </div>
                  <button
                    onClick={toggleSpeech}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors min-w-[60px] ${
                      speechEnabled
                        ? 'bg-green-600 hover:bg-green-700 text-white'
                        : 'bg-red-600 hover:bg-red-700 text-white'
                    }`}
                  >
                    {speechEnabled ? 'ON' : 'OFF'}
                  </button>
                </div>

                {/* Video Streaming */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {videoStreamingEnabled ? (
                      <Video className="w-4 h-4 text-green-400" />
                    ) : (
                      <VideoOff className="w-4 h-4 text-red-400" />
                    )}
                    <span className="text-white font-medium">Video Stream</span>
                  </div>
                  <button
                    onClick={toggleVideoStream}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors min-w-[60px] ${
                      videoStreamingEnabled
                        ? 'bg-green-600 hover:bg-green-700 text-white'
                        : 'bg-red-600 hover:bg-red-700 text-white'
                    }`}
                  >
                    {videoStreamingEnabled ? 'ON' : 'OFF'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;