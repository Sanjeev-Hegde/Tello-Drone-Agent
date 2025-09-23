#!/usr/bin/env python3
"""
Hybrid Drone Agent - Combines GPT-4o Realtime API for Speech I/O 
with Autonomous Drone Agent for Command Processing

Architecture:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Realtime API  │    │   Hybrid Agent   │    │ Autonomous Agent│
│                 │    │                  │    │                 │
│ • Speech Input  │◄──►│ • Speech Bridge  │◄──►│ • Command       │
│ • Speech Output │    │ • Text Conversion│    │   Processing    │
│ • Audio Stream  │    │ • Result Routing │    │ • Multi-step    │
│                 │    │                  │    │   Execution     │
└─────────────────┘    └──────────────────┘    │ • Function Calls│
                                               └─────────────────┘
"""

import asyncio
import json
import base64
import logging
import os
import sys
import time
import threading
import queue
import argparse
from typing import Dict, Any, List, Optional
import websockets
import pyaudio
import cv2
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Environment settings
class EnvironmentSettings:
    def __init__(self):
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com')
        self.azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY', 'your-api-key')
        self.realtime_deployment_name = os.getenv('AZURE_OPENAI_REALTIME_DEPLOYMENT', 'gpt-4o-realtime-preview')
        self.gpt4o_deployment_name = os.getenv('AZURE_OPENAI_GPT4O_DEPLOYMENT', 'gpt-4o')

settings = EnvironmentSettings()

# Import the real autonomous drone agent - fail if not available
try:
    from agents.autonomous_drone_agent import AutonomousDroneAgent
    from drone.simple_tello import SimpleTello
    print("✅ Full autonomous agent imported successfully")
except Exception as e:
    print(f"❌ Failed to import autonomous drone agent: {e}")
    print("💡 Make sure your .env file has the correct Azure configuration")
    print("💡 Check that all required packages are installed")
    raise SystemExit(f"Cannot start hybrid agent without autonomous drone agent: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechProcessor:
    """Handles speech input/output via OpenAI Realtime API."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SpeechProcessor")
        
        # Audio configuration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 24000  # GPT-4o Realtime expects 24kHz
        
        # Audio streams
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        
        # WebSocket connection
        self.websocket = None
        self.is_connected = False
        
        # Response state tracking to prevent concurrent response errors
        self.response_active = False
        self.pending_speech_queue = asyncio.Queue()
        
        # Audio queues
        self.input_audio_queue = queue.Queue()
        self.output_audio_queue = queue.Queue()
        
        # Control flags
        self.recording = False
        self.playing = False
        self.running = False
        
        # Communication with main agent
        self.text_received_callback = None
        self.waiting_for_speech = False
        
    async def connect_realtime(self):
        """Connect to Azure OpenAI Realtime API."""
        try:
            # Convert HTTPS to WSS for WebSocket connection
            endpoint = settings.azure_openai_endpoint.replace('https://', 'wss://').replace('http://', 'ws://')
            
            # WebSocket URL for Azure OpenAI Realtime
            ws_url = f"{endpoint}/openai/realtime?api-version=2024-10-01-preview&deployment={settings.realtime_deployment_name}"
            
            headers = {
                "api-key": settings.azure_openai_api_key,
                "OpenAI-Beta": "realtime=v1"
            }
            
            self.logger.info(f"🔌 Connecting to realtime API for speech...")
            
            self.websocket = await websockets.connect(
                ws_url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.is_connected = True
            self.logger.info("✅ Connected to GPT-4o Realtime API for speech")
            
            # Configure session for speech only (no function calling)
            await self._configure_speech_session()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Speech connection failed: {e}")
            return False
    
    async def _configure_speech_session(self):
        """Configure the realtime session for speech processing only."""
        
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """You are a text-to-speech converter for a drone control system.

Your ONLY job is to speak the exact text you receive from this drone system- nothing more, nothing less.

Rules:
- When given text to speak, speak it exactly as you receive it
- Do NOT add any commentary, explanations, or extra words  
- Do NOT mention other agents or systems
- Do NOT explain how the drone system works
- Do NOT provide any additional context or information
- Do NOT tell users about the internal workings of the system
- Do NOT tell your role to anyone
- Do NOT tell that you speak what text you receive
- Just convert the text to clear, natural speech

You are the voice output for drone command results.""",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [],  # No function calling - speech only
                "temperature": 0.7
            }
        }
        
        await self.websocket.send(json.dumps(session_config))
        self.logger.info("🔧 Speech session configured")
    
    def start_audio_streams(self):
        """Start audio input and output streams."""
        try:
            # Input stream (microphone)
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            # Output stream (speakers)
            self.output_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.recording = True
            self.playing = True
            
            self.logger.info("🎤🔊 Speech audio streams started")
            
            # Start audio worker threads
            threading.Thread(target=self._audio_input_worker, daemon=True).start()
            threading.Thread(target=self._audio_output_worker, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start audio streams: {e}")
    
    def _audio_input_worker(self):
        """Worker thread for audio input."""
        while self.recording and self.running:
            try:
                if self.input_stream:
                    data = self.input_stream.read(self.CHUNK, exception_on_overflow=False)
                    self.input_audio_queue.put(data)
            except Exception as e:
                self.logger.error(f"❌ Audio input error: {e}")
                time.sleep(0.1)
    
    def _audio_output_worker(self):
        """Worker thread for audio output."""
        while self.playing and self.running:
            try:
                if not self.output_audio_queue.empty():
                    audio_data = self.output_audio_queue.get(timeout=0.1)
                    if self.output_stream:
                        self.output_stream.write(audio_data)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ Audio output error: {e}")
                time.sleep(0.1)
    
    async def _send_audio_to_api(self):
        """Send microphone audio to the realtime API."""
        while self.is_connected and self.running:
            try:
                if not self.input_audio_queue.empty():
                    audio_chunk = self.input_audio_queue.get_nowait()
                    
                    # Convert to base64
                    audio_base64 = base64.b64encode(audio_chunk).decode()
                    
                    # Send to API
                    message = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_base64
                    }
                    
                    await self.websocket.send(json.dumps(message))
                
                await asyncio.sleep(0.01)  # Small delay
                
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                self.logger.error(f"❌ Audio send error: {e}")
                await asyncio.sleep(0.1)
    
    async def _handle_realtime_messages(self):
        """Handle messages from the realtime API."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._process_speech_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("🔌 Speech WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"❌ Speech message handling error: {e}")
            self.is_connected = False
    
    async def _process_speech_message(self, data):
        """Process individual message from the realtime API."""
        msg_type = data.get("type")
        
        if msg_type == "session.created":
            self.logger.info("🎉 Speech session created")
            
        elif msg_type == "input_audio_buffer.speech_started":
            self.logger.info("🗣️  Speech detected - listening...")
            
        elif msg_type == "input_audio_buffer.speech_stopped": 
            self.logger.info("⏸️  Speech ended - processing...")
            
        elif msg_type == "conversation.item.input_audio_transcription.completed":
            transcript = data.get("transcript", "")
            self.logger.info(f"📝 You said: {transcript}")
            
            # Send transcribed text to main agent
            if self.text_received_callback:
                await self.text_received_callback(transcript)
        
        elif msg_type == "response.created":
            # Response generation started
            self.response_active = True
            
        elif msg_type == "response.done":
            # Response generation finished - we can create new responses now
            self.response_active = False
            # Process any pending speech requests
            if not self.pending_speech_queue.empty():
                try:
                    pending_text = self.pending_speech_queue.get_nowait()
                    self.logger.info(f"🔓 Processing queued speech: {pending_text[:50]}...")
                    await self._do_speak_text(pending_text)
                except asyncio.QueueEmpty:
                    pass
            
        elif msg_type == "response.audio.delta":
            # Stream audio response to speakers
            if "delta" in data:
                audio_data = base64.b64decode(data["delta"])
                self.output_audio_queue.put(audio_data)
                
        elif msg_type == "error":
            self.logger.error(f"❌ Speech API Error: {data}")
    
    async def speak_text(self, text: str):
        """Convert text to speech via realtime API with response state management."""
        try:
            if not self.is_connected:
                self.logger.warning("⚠️ Not connected to speech API, cannot speak")
                return
            
            # If a response is already active, queue this speech request
            if self.response_active:
                self.logger.info(f"⏳ Queuing speech (response active): {text}")
                await self.pending_speech_queue.put(text)
                return
            
            # Proceed with immediate speech generation
            await self._do_speak_text(text)
            
        except Exception as e:
            self.logger.error(f"❌ Text-to-speech error: {e}")
    
    async def _do_speak_text(self, text: str):
        """Actually perform the text-to-speech conversion."""
        try:
            self.logger.info(f"🗣️ Speaking: {text}")
            
            # Create conversation item with text to speak
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text
                        }
                    ]
                }
            }
            await self.websocket.send(json.dumps(message))
            
            # Small delay before requesting response
            await asyncio.sleep(0.05)
            
            # Request speech generation
            response_request = {
                "type": "response.create"
            }
            await self.websocket.send(json.dumps(response_request))
            
        except Exception as e:
            self.logger.error(f"❌ Internal text-to-speech error: {e}")
    
    def set_text_callback(self, callback):
        """Set callback function to receive transcribed text."""
        self.text_received_callback = callback
    
    async def start_speech_processing(self):
        """Start speech input/output processing."""
        self.running = True
        
        try:
            self.start_audio_streams()
            
            # Start main communication loops
            await asyncio.gather(
                self._send_audio_to_api(),
                self._handle_realtime_messages()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Speech processing error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up speech processor resources."""
        self.logger.info("🧹 Cleaning up speech processor...")
        
        self.running = False
        self.recording = False
        self.playing = False
        self.is_connected = False
        
        # Clean up audio
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
                
        if self.output_stream:
            try:
                self.output_stream.stop_stream() 
                self.output_stream.close()
            except:
                pass
                
        try:
            self.audio.terminate()
        except:
            pass
        
        # Close WebSocket
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass


class HybridDroneAgent:
    """
    Hybrid drone agent that combines:
    - OpenAI Realtime API for speech input/output
    - Autonomous Drone Agent for command processing
    """
    
    def __init__(self, vision_only: bool = False):
        self.logger = logging.getLogger(__name__)
        self.vision_only = vision_only
        
        # Initialize components
        self.speech_processor = SpeechProcessor()
        self.command_processor = None
        
        # Control flags
        self.running = False
    
    async def initialize(self):
        """Initialize all components."""
        try:
            # Initialize speech processor
            if not await self.speech_processor.connect_realtime():
                raise Exception("Failed to connect speech processor")
            
            # Initialize autonomous drone agent
            self.logger.info("🤖 Initializing autonomous drone agent...")
            self.command_processor = AutonomousDroneAgent(vision_only=self.vision_only)
            self.logger.info("✅ Autonomous drone agent ready")
            
            # Set up communication bridge
            self.speech_processor.set_text_callback(self._process_voice_command)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def _process_voice_command(self, voice_text: str):
        """Process voice command through autonomous agent and speak the result."""
        try:
            start_time = time.time()
            self.logger.info(f"🎯 Processing command: {voice_text}")
            
            # Send command to autonomous drone agent for processing
            result = await self.command_processor.process_user_command(voice_text)
            
            processing_time = time.time() - start_time
            self.logger.info(f"⏱️ Command processed in {processing_time:.2f} seconds")
            
            if result:
                # Convert result to speech
                await self.speech_processor.speak_text(result)
            else:
                await self.speech_processor.speak_text("Command processed but no response generated")
                
        except Exception as e:
            self.logger.error(f"❌ Command processing error: {e}")
            await self.speech_processor.speak_text(f"Sorry, there was an error processing your command: {str(e)}")
    
    async def start(self):
        """Start the hybrid drone agent."""
        self.running = True
        
        try:
            self.logger.info("🚁🎙️ Starting Hybrid Drone Agent!")
            self.logger.info("💡 Speak your commands! Examples:")
            self.logger.info("   • 'Take off'")
            self.logger.info("   • 'Move forward 50 centimeters then turn right'")
            self.logger.info("   • 'What do you see?'")
            self.logger.info("   • 'Get status'")
            self.logger.info("   • 'Land'")
            self.logger.info("💡 Press Ctrl+C to stop")
            
            # Start speech processing
            await self.speech_processor.start_speech_processing()
            
        except KeyboardInterrupt:
            self.logger.info("👋 Hybrid drone agent stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Hybrid agent error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up all resources."""
        self.logger.info("🧹 Cleaning up hybrid agent...")
        
        self.running = False
        
        # Clean up speech processor
        if self.speech_processor:
            await self.speech_processor.cleanup()
        
        # Clean up command processor
        if self.command_processor:
            self.command_processor.cleanup()
        
        self.logger.info("✅ Hybrid agent cleanup completed")


async def main():
    """Main function to run the hybrid drone agent."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hybrid Drone Agent - Realtime Speech + Autonomous Commands')
    parser.add_argument('--vision-only', action='store_true', default=True,
                        help='Run in vision-only mode (simulation) - default: True')
    parser.add_argument('--real-drone', action='store_true', default=False,
                        help='Connect to real drone (overrides --vision-only)')
    
    args = parser.parse_args()
    
    # Determine vision_only mode
    vision_only = not args.real_drone  # If real_drone is True, vision_only is False
    
    print(f"🤖 Mode: {'VISION ONLY (Simulation)' if vision_only else 'REAL DRONE'}")
    
    # Check environment variables
    required_vars = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        logger.info("💡 Set them in your .env file:")
        for var in missing_vars:
            logger.info(f"   {var}=your-value")
        return
    
    # Create hybrid agent
    agent = HybridDroneAgent(vision_only=vision_only)
    
    try:
        # Initialize all components
        if await agent.initialize():
            # Start hybrid processing
            await agent.start()
        else:
            logger.error("❌ Failed to initialize hybrid agent")
            
    except Exception as e:
        logger.error(f"❌ Main error: {e}")


if __name__ == "__main__":
    print("🚁🎙️ Hybrid Drone Agent")
    print("=" * 50)
    print()
    print("🏗️ ARCHITECTURE:")
    print("   • Realtime API: Speech input/output")
    print("   • Autonomous Agent: Command processing") 
    print("   • Best of both worlds!")
    print()
    print("📋 FEATURES:")
    print("   ✅ Natural speech conversation")
    print("   ✅ Multi-step command sequences")
    print("   ✅ No pauses between commands")
    print("   ✅ Proven drone control logic")
    print()
    print("🚀 USAGE:")
    print("   • Vision Only:  python hybrid_drone_agent.py")
    print("   • Real Drone:   python hybrid_drone_agent.py --real-drone")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
