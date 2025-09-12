#!/usr/bin/env python3
"""
Vision Analysis Module for Drone Agent
Handles GPT-4o vision analysis with focus-specific prompts and image processing.
"""

import asyncio
import json
import base64
import logging
import os
import time
import threading
from typing import Dict, Any, Optional
import cv2
import numpy as np


class VisionAnalyzer:
    """Handles image capture, analysis, and GPT-4o vision integration."""
    
    def __init__(self, websocket=None):
        self.logger = logging.getLogger(f"{__name__}.VisionAnalyzer")
        self.websocket = websocket
        
        # Focus-specific prompts for different analysis types
        self.focus_prompts = {
            "obstacles": "Analyze this drone camera view for navigation safety. Identify any obstacles, walls, or hazards that could interfere with drone movement. Provide specific distances if possible and suggest safe movement directions.",
            "objects": "Describe all objects, furniture, and items visible in this drone camera view. Focus on identifying what's in the scene and their approximate positions relative to the drone.",
            "navigation": "Evaluate this view for drone navigation. Assess the available space, lighting conditions, ceiling height, and provide recommendations for safe flight paths.",
            "landing_spot": "Analyze the area below and around the drone for suitable landing spots. Identify flat surfaces, potential hazards, and recommend the best landing approach."
        }
        
        # Simulation responses for vision-only mode
        self.simulation_analyses = {
            "obstacles": "a chair 200 cm ahead.",
            "objects": "I can see a desk with computer monitor and laptop. Some cables and office equipment visible. No people in view.",
            "navigation": "Room appears spacious with good lighting. Safe to move forward up to 1.5 meters before encountering furniture.",
            "landing_spot": "Current area has flat surface suitable for landing. No obstacles directly below."
        }
    
    def set_websocket(self, websocket):
        """Update the WebSocket connection for real analysis."""
        self.websocket = websocket
    
    async def capture_and_analyze_image(self, drone, focus: str = "objects", vision_only: bool = False, **kwargs) -> str:
        """Capture and analyze image from drone camera."""
        self.logger.info(f"📸 Capturing image for: {focus}")
        
        if vision_only:
            return self._get_simulation_analysis(focus)
        
        try:
            # Capture real frame from drone with retries
            frame = None
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    frame = drone.get_frame()
                    if frame is not None:
                        break
                    self.logger.warning(f"⚠️ Frame capture attempt {attempt + 1} failed, retrying...")
                except Exception as e:
                    self.logger.warning(f"⚠️ Frame capture error on attempt {attempt + 1}: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5)  # Wait before retry
            
            if frame is None:
                return "Failed to capture image - camera not available after multiple attempts. Check video stream connection."
            
            # Save image asynchronously (non-blocking)
            self._save_image_async(frame, focus)
            
            # Convert frame to base64 for GPT-4o
            image_base64 = self._frame_to_base64(frame)
            
            # Get analysis from GPT-4o Vision
            analysis_result = await self._analyze_image_with_gpt4o(image_base64, focus)
            
            self.logger.info(f"✅ Image analysis completed: {analysis_result[:100]}...")
            return analysis_result
            
        except Exception as e:
            error_msg = f"Image capture/analysis error: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return error_msg
    
    def _get_simulation_analysis(self, focus: str) -> str:
        """Return simulation analysis for vision-only mode."""
        return self.simulation_analyses.get(focus, "Image captured and analyzed - environment looks good.")
    
    def _frame_to_base64(self, frame: np.ndarray, quality: int = 80) -> str:
        """Convert OpenCV frame to base64 string for API (BGR -> RGB conversion)."""
        try:
            # Convert BGR (OpenCV) to RGB (what most vision APIs expect)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', frame_rgb, [cv2.IMWRITE_JPEG_QUALITY, quality])
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            self.logger.error(f"❌ Frame encoding error: {e}")
            raise
    
    def _save_image_async(self, frame: np.ndarray, focus: str):
        """Save image asynchronously in background thread."""
        def save_image():
            try:
                timestamp = int(time.time())
                image_path = f"images/drone_capture_{focus}_{timestamp}.jpg"
                os.makedirs("images", exist_ok=True)
                
                # Debug: Log frame info
                self.logger.debug(f"🔍 Frame shape: {frame.shape}, dtype: {frame.dtype}")
                
                # Save the frame directly - cv2.imwrite expects BGR format which is what the drone should provide
                # If colors are still wrong, the drone might be giving us RGB instead of BGR
                cv2.imwrite(image_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                self.logger.debug(f"💾 Image saved: {image_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to save debug image: {e}")
        
        # Start background thread for image saving
        threading.Thread(target=save_image, daemon=True).start()
    
    async def _analyze_image_with_gpt4o(self, image_base64: str, focus: str) -> str:
        """Send image to GPT-4o for analysis via the realtime WebSocket connection."""
        if not self.websocket:
            return "WebSocket connection not available for real analysis"
        
        try:
            prompt = self.focus_prompts.get(focus, "Analyze this drone camera view and describe what you see.If image is blank say 'No image captured' and retry.")

            # Send image analysis request through the realtime connection
            # Azure OpenAI Realtime API format - image_url should be a string
            image_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"{prompt}"
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    ]
                }
            }
            
            await self.websocket.send(json.dumps(image_message))
            
            # Request a response with audio modality so the user hears the analysis
            response_request = {
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],  # Include audio so user hears the analysis
                    "instructions": f"Analyze the provided image focusing on {focus}. Be specific, practical, and concise. Provide actionable information for drone navigation and safety. Speak your analysis aloud in 1 or max 2 sentences."
                }
            }
            
            await self.websocket.send(json.dumps(response_request))
            
            # Return a message that indicates the response is already being handled
            # Use a special prefix to signal no additional speech response needed
            return f"[PROCESSING] Image analysis in progress - GPT-4o will provide audio response directly"
            
        except Exception as e:
            self.logger.error(f"❌ GPT-4o image analysis error: {e}")
            return f"Failed to analyze image: {str(e)}"
    
    def get_analysis_prompt(self, focus: str) -> str:
        """Get the analysis prompt for a specific focus type."""
        return self.focus_prompts.get(focus, "Analyze this drone camera view and describe what you see.")
    
    def add_custom_focus(self, focus_name: str, prompt: str, simulation_response: str = None):
        """Add a custom focus type with its prompt and simulation response."""
        self.focus_prompts[focus_name] = prompt
        if simulation_response:
            self.simulation_analyses[focus_name] = simulation_response
        self.logger.info(f"✅ Added custom focus: {focus_name}")
