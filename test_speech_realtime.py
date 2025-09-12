#!/usr/bin/env python3
"""
Basic Speech-to-Speech Test using GPT-4o Realtime API
Simple test to verify microphone input and speech output work.
"""

import asyncio
import json
import base64
import logging
import os
from typing import Optional
import websockets
import pyaudio
import wave
import threading
import queue
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasicSpeechAgent:
    """Basic speech-to-speech agent for testing GPT-4o Realtime API."""
    
    def __init__(self):
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
        
        # Audio queues
        self.input_audio_queue = queue.Queue()
        self.output_audio_queue = queue.Queue()
        
        # Control flags
        self.recording = False
        self.playing = False
        
        # Azure OpenAI settings - UPDATE THESE WITH YOUR VALUES
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY', 'your-api-key')
        self.deployment_name = os.getenv('AZURE_OPENAI_REALTIME_DEPLOYMENT', 'gpt-4o-realtime-preview')
        
    async def connect_realtime(self):
        """Connect to Azure OpenAI Realtime API."""
        try:
            # Convert HTTPS to WSS for WebSocket connection
            endpoint = self.endpoint.replace('https://', 'wss://').replace('http://', 'ws://')
            
            # WebSocket URL for Azure OpenAI Realtime
            ws_url = f"{endpoint}/openai/realtime?api-version=2024-10-01-preview&deployment={self.deployment_name}"
            
            headers = {
                "api-key": self.api_key,
                "OpenAI-Beta": "realtime=v1"
            }
            
            logger.info(f"🔌 Connecting to: {ws_url}")
            
            self.websocket = await websockets.connect(
                ws_url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.is_connected = True
            logger.info("✅ Connected to GPT-4o Realtime API")
            
            # Configure session
            await self._configure_session()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def _configure_session(self):
        """Configure the realtime session."""
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """You are a helpful voice assistant. Have natural conversations with the user. 
                
Keep responses conversational and friendly. You can discuss any topic the user is interested in.
When responding, speak naturally as if you're having a face-to-face conversation.""",
                "voice": "alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",  # Voice Activity Detection
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }
        
        await self.websocket.send(json.dumps(session_config))
        logger.info("🔧 Session configured")
    
    def start_audio_input(self):
        """Start audio input stream from microphone."""
        try:
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.recording = True
            logger.info("🎤 Microphone started")
            
            # Start audio input thread
            threading.Thread(target=self._audio_input_worker, daemon=True).start()
            
        except Exception as e:
            logger.error(f"❌ Failed to start microphone: {e}")
    
    def start_audio_output(self):
        """Start audio output stream to speakers."""
        try:
            self.output_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.playing = True
            logger.info("🔊 Speakers started")
            
            # Start audio output thread
            threading.Thread(target=self._audio_output_worker, daemon=True).start()
            
        except Exception as e:
            logger.error(f"❌ Failed to start speakers: {e}")
    
    def _audio_input_worker(self):
        """Worker thread for audio input."""
        while self.recording:
            try:
                if self.input_stream:
                    data = self.input_stream.read(self.CHUNK, exception_on_overflow=False)
                    self.input_audio_queue.put(data)
            except Exception as e:
                logger.error(f"❌ Audio input error: {e}")
                time.sleep(0.1)
    
    def _audio_output_worker(self):
        """Worker thread for audio output."""
        while self.playing:
            try:
                if not self.output_audio_queue.empty():
                    audio_data = self.output_audio_queue.get()
                    if self.output_stream:
                        self.output_stream.write(audio_data)
            except Exception as e:
                logger.error(f"❌ Audio output error: {e}")
                time.sleep(0.1)
    
    async def _send_audio_to_api(self):
        """Send microphone audio to the realtime API."""
        while self.is_connected:
            try:
                if not self.input_audio_queue.empty():
                    audio_chunk = self.input_audio_queue.get()
                    
                    # Convert to base64
                    audio_base64 = base64.b64encode(audio_chunk).decode()
                    
                    # Send to API
                    message = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_base64
                    }
                    
                    await self.websocket.send(json.dumps(message))
                
                await asyncio.sleep(0.01)  # Small delay
                
            except Exception as e:
                logger.error(f"❌ Audio send error: {e}")
                await asyncio.sleep(0.1)
    
    async def _handle_realtime_messages(self):
        """Handle messages from the realtime API."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._process_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
            self.is_connected = False
    
    async def _process_message(self, data):
        """Process individual message from the API."""
        msg_type = data.get("type")
        
        if msg_type == "session.created":
            logger.info("🎉 Session created successfully")
            
        elif msg_type == "input_audio_buffer.speech_started":
            logger.info("🗣️  Speech detected - listening...")
            
        elif msg_type == "input_audio_buffer.speech_stopped":
            logger.info("⏸️  Speech ended - processing...")
            
        elif msg_type == "conversation.item.input_audio_transcription.completed":
            transcript = data.get("transcript", "")
            logger.info(f"📝 You said: {transcript}")
            
        elif msg_type == "response.audio.delta":
            # Audio response from the assistant
            if "delta" in data:
                audio_data = base64.b64decode(data["delta"])
                self.output_audio_queue.put(audio_data)
                
        elif msg_type == "response.audio.done":
            logger.info("🔊 Response audio complete")
            
        elif msg_type == "error":
            logger.error(f"❌ API Error: {data}")
    
    async def start_conversation(self):
        """Start the voice conversation loop."""
        logger.info("🚀 Starting voice conversation...")
        logger.info("💡 Speak into your microphone! The assistant will respond with speech.")
        logger.info("💡 Press Ctrl+C to stop")
        
        try:
            # Start audio streams
            self.start_audio_input()
            self.start_audio_output()
            
            # Start audio processing and message handling
            await asyncio.gather(
                self._send_audio_to_api(),
                self._handle_realtime_messages()
            )
            
        except KeyboardInterrupt:
            logger.info("👋 Conversation stopped by user")
        except Exception as e:
            logger.error(f"❌ Conversation error: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("🧹 Cleaning up...")
        
        self.recording = False
        self.playing = False
        self.is_connected = False
        
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            
        self.audio.terminate()
        
        logger.info("✅ Cleanup complete")

async def main():
    """Main function to run the speech test."""
    
    # Check environment variables
    if not os.getenv('AZURE_OPENAI_ENDPOINT'):
        logger.error("❌ Please set AZURE_OPENAI_ENDPOINT environment variable")
        logger.info("💡 Example: export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
        return
    
    if not os.getenv('AZURE_OPENAI_API_KEY'):
        logger.error("❌ Please set AZURE_OPENAI_API_KEY environment variable")
        logger.info("💡 Example: export AZURE_OPENAI_API_KEY='your-api-key'")
        return
    
    agent = BasicSpeechAgent()
    
    try:
        # Connect to realtime API
        if await agent.connect_realtime():
            # Start conversation
            await agent.start_conversation()
        else:
            logger.error("❌ Failed to connect to realtime API")
            
    except Exception as e:
        logger.error(f"❌ Main error: {e}")
    finally:
        agent.cleanup()

if __name__ == "__main__":
    print("🎙️  GPT-4o Realtime Speech Test")
    print("=" * 40)
    print()
    print("📋 SETUP INSTRUCTIONS:")
    print("1. Install dependencies: pip install websockets pyaudio")
    print("2. Set environment variables:")
    print("   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
    print("   export AZURE_OPENAI_API_KEY='your-api-key'")
    print("   export AZURE_OPENAI_REALTIME_DEPLOYMENT='gpt-4o-realtime-preview'")
    print("3. Make sure you have a microphone and speakers connected")
    print("4. Run this script and start talking!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
