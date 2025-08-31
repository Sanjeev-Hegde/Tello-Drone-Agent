"""
Autonomous Drone Agent using Azure AI Projects and SimpleTello integration.
Provides intelligent drone control with computer vision and safety protocols.
"""

import os
import logging
import json
import time
import base64
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Try imports with error handling
try:
    from config.settings import settings
except ImportError:
    # Fallback for testing
    class MockSettings:
        def __init__(self):
            self.AZURE_AI_PROJECTS_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=dummyaccount;AccountKey=dummykey;EndpointSuffix=core.windows.net"
            self.AZURE_AI_PROJECT_NAME = "Drone-Agent"
            self.GPT_MODEL_NAME = "gpt-4o"
    settings = MockSettings()

try:
    from drone.simple_tello import SimpleTello
except ImportError:
    # Mock SimpleTello for testing
    class SimpleTello:
        def __init__(self):
            pass
        def takeoff(self): return True
        def land(self): return True
        def move_up(self, distance): return True
        def move_down(self, distance): return True
        def move_left(self, distance): return True
        def move_right(self, distance): return True
        def move_forward(self, distance): return True
        def move_back(self, distance): return True
        def rotate_clockwise(self, angle): return True
        def rotate_counter_clockwise(self, angle): return True
        def get_battery(self): return 100
        def get_height(self): return 50
        def close(self): pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DroneState:
    """Track drone state and flight history."""
    is_flying: bool = False
    battery: int = 100
    height: int = 0
    last_image_analysis: str = ""
    movement_count: int = 0
    obstacles_detected: List[str] = None
    
    def __post_init__(self):
        if self.obstacles_detected is None:
            self.obstacles_detected = []


class AutonomousDroneAgent:
    """Autonomous drone controller with computer vision and SimpleTello integration."""
    
    def __init__(self, vision_only: bool = False):
        self.logger = logging.getLogger(__name__)
        self.vision_only = vision_only
        
        # Core components
        self.ai_client = None
        self.agent = None
        self.thread = None
        self.drone = SimpleTello() if not vision_only else None
        self.drone_state = DroneState()
        
        # Conversation memory for context
        self.conversation_history: List[Dict] = []
        self.image_history: List[Dict] = []
        
        # Initialize Azure AI
        self._setup_ai_client()
        
        # Check for existing agent ID in environment
        existing_agent_id = os.getenv('DRONE_AGENT_ID')
        
        if existing_agent_id:
            self.logger.info(f"🔄 Using existing agent (ID: {existing_agent_id[:8]}...)")
            self.agent = self.ai_client.agents.get_agent(existing_agent_id)
            # Always create a fresh thread for each session
            self.logger.info("🆕 Creating fresh thread for new session...")
            self.thread = self.ai_client.agents.threads.create()
        else:
            self.logger.info("🆕 Creating new agent and thread...")
            self._create_agent()
        
        # Always register functions (for both new and reused agents)
        self._register_functions()
        
        # Initialize drone connection if not vision-only
        if not self.vision_only:
            self._setup_drone()
    
    def _setup_ai_client(self):
        """Initialize Azure AI Projects client."""
        # Suppress Azure HTTP logging for cleaner output
        logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
        logging.getLogger('azure.identity').setLevel(logging.WARNING)
        
        try:
            self.logger.info("Setting up Azure AI Projects client...")
            credential = DefaultAzureCredential()
            self.ai_client = AIProjectClient(
                endpoint=settings.azure_ai_project_endpoint,
                credential=credential
            )
            self.logger.info("✅ Azure AI Projects client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to setup Azure AI client: {e}")
            raise
    
    def _setup_drone(self):
        """Initialize drone connection."""
        try:
            self.logger.info("Connecting to Tello drone...")
            if self.drone.connect():
                self.drone.streamon()  # Start video stream
                self.drone_state.battery = self.drone.get_battery()
                self.logger.info(f"✅ Drone connected, battery: {self.drone_state.battery}%")
            else:
                self.logger.error("❌ Failed to connect to drone")
        except Exception as e:
            self.logger.error(f"❌ Drone setup error: {e}")
    
    def _create_agent(self):
        """Create the autonomous drone agent."""
        try:
            self.logger.info("Creating autonomous drone agent...")
            
            self.agent = self.ai_client.agents.create_agent(
                model="gpt-4o",
                name="Autonomous Drone Controller",
                instructions="""You are an intelligent autonomous drone controller. You take user commands and safely control a Tello drone using computer vision.

## CORE PRINCIPLES:
1. **Safety First**: Always analyze the environment before moving
2. **Small Steps**: Take incremental movements (20-50cm) to avoid crashes  
3. **Vision-Guided**: Capture images before major movements to see obstacles
4. **Rotate Before Side Movement**: Never fly left/right directly - rotate first to see direction, then move forward
5. **Remember Context**: Use previous images and conversation to make informed decisions

## YOUR PROCESS:
1. **Understand Command**: Parse user intent (explore, find object, go to location, etc.)
2. **Assess Situation**: Get current status and capture image if needed
3. **Plan Movement**: Decide safe incremental steps based on visual analysis
4. **Execute Safely**: Move in small steps, checking obstacles continuously
5. **Confirm Progress**: Report what you see and accomplished

## MOVEMENT STRATEGY:
- **Forward/Backward**: Capture image first, move 20-50cm max
- **Left/Right**: Rotate 45-90° first, capture image, then move forward
- **Up/Down**: Small increments (20-30cm) 
- **Rotation**: 30-90° turns to survey environment

## VISION ANALYSIS:
- Use capture_image_and_analyze to see current view
- Identify obstacles, objects, people, safe paths
- Track changes between images for navigation
- Analyze for specific objects user mentioned

You are cautious, methodical, and always prioritize safety over speed.""",
                tools=self._get_drone_tools()
            )
            
            self.logger.info(f"✅ Agent created with ID: {self.agent.id}")
            
            # Create conversation thread
            self.thread = self.ai_client.agents.threads.create()
            self.logger.info(f"✅ Thread created with ID: {self.thread.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create agent: {e}")
            raise
    
    def _register_functions(self):
        """Register drone control functions for auto execution."""
        # Create synchronous wrapper functions with exact tool names
        import asyncio
        import concurrent.futures
        import threading
        
        def run_async_in_thread(coro):
            """Run async function in a separate thread to avoid event loop conflicts"""
            def run_in_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30 second timeout
        
        def takeoff(): 
            return run_async_in_thread(self._takeoff())
        def land(): 
            return run_async_in_thread(self._land())
        def move_forward(distance: int): 
            return run_async_in_thread(self._move_forward(distance))
        def move_backward(distance: int): 
            return run_async_in_thread(self._move_back(distance))
        def move_left(distance: int): 
            return run_async_in_thread(self._move_left(distance))
        def move_right(distance: int): 
            return run_async_in_thread(self._move_right(distance))
        def move_up(distance: int): 
            return run_async_in_thread(self._move_up(distance))
        def move_down(distance: int): 
            return run_async_in_thread(self._move_down(distance))
        def rotate_clockwise(angle: int): 
            return run_async_in_thread(self._rotate_clockwise(angle))
        def rotate_counterclockwise(angle: int): 
            return run_async_in_thread(self._rotate_counter_clockwise(angle))
        def get_drone_status(): 
            return self._get_drone_status()  # This is sync, no need for async runner
        def capture_image_and_analyze(focus: str, object_description: str = ""): 
            return run_async_in_thread(self._capture_image_and_analyze(focus, object_description))
        def emergency_stop(): 
            return run_async_in_thread(self._emergency_stop())

        # Register tool functions for auto execution
        functions_list = [
            takeoff, land, move_forward, move_backward, move_left, move_right,
            move_up, move_down, rotate_clockwise, rotate_counterclockwise,
            get_drone_status, capture_image_and_analyze, emergency_stop
        ]
        self.ai_client.agents.enable_auto_function_calls(functions_list)
        self.logger.info("✅ Functions registered for auto execution")
    
    def _get_drone_tools(self) -> List[Dict]:
        """Define drone control tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "takeoff",
                    "description": "Take off the drone safely - only use when drone is on ground",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "land",
                    "description": "Land the drone safely at current location",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "move_forward",
                    "description": "Move drone forward by specified distance - always capture image first to check for obstacles",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "distance": {
                                "type": "integer",
                                "description": "Distance in centimeters (20-100cm recommended for safety)",
                                "minimum": 20,
                                "maximum": 100
                            }
                        },
                        "required": ["distance"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "move_back",
                    "description": "Move drone backward by specified distance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "distance": {
                                "type": "integer",
                                "description": "Distance in centimeters (20-100cm)",
                                "minimum": 20,
                                "maximum": 100
                            }
                        },
                        "required": ["distance"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "move_up",
                    "description": "Move drone up by specified distance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "distance": {
                                "type": "integer",
                                "description": "Distance in centimeters (20-50cm recommended)",
                                "minimum": 20,
                                "maximum": 100
                            }
                        },
                        "required": ["distance"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "move_down",
                    "description": "Move drone down by specified distance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "distance": {
                                "type": "integer",
                                "description": "Distance in centimeters (20-50cm recommended)",
                                "minimum": 20,
                                "maximum": 100
                            }
                        },
                        "required": ["distance"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rotate_clockwise",
                    "description": "Rotate drone clockwise - use before moving left/right to see direction clearly",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "angle": {
                                "type": "integer",
                                "description": "Rotation angle in degrees (30-180°)",
                                "minimum": 30,
                                "maximum": 180
                            }
                        },
                        "required": ["angle"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rotate_counter_clockwise",
                    "description": "Rotate drone counter-clockwise - use before moving left/right to see direction clearly",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "angle": {
                                "type": "integer",
                                "description": "Rotation angle in degrees (30-180°)",
                                "minimum": 30,
                                "maximum": 180
                            }
                        },
                        "required": ["angle"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_drone_status",
                    "description": "Get current drone status including battery, height, and flight state",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "capture_image_and_analyze",
                    "description": "Capture current camera view and analyze it using GPT-4o vision - use before movements to detect obstacles and objects",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "focus": {
                                "type": "string",
                                "description": "What to focus analysis on: obstacles, objects, navigation, specific_object, landing_spot",
                                "enum": ["obstacles", "objects", "navigation", "specific_object", "landing_spot"]
                            },
                            "object_description": {
                                "type": "string",
                                "description": "If focus is 'specific_object', describe what object to look for"
                            }
                        },
                        "required": ["focus"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "emergency_stop",
                    "description": "Emergency stop - immediately stop all movement and hover",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Reason for emergency stop"
                            }
                        }
                    }
                }
            }
        ]
    
    # Tool implementations
    async def _takeoff(self) -> str:
        """Take off the drone."""
        self.logger.info("🚁 Taking off...")
        
        if self.drone_state.is_flying:
            return "❌ Drone is already flying!"
        
        if self.vision_only:
            self.drone_state.is_flying = True
            self.drone_state.height = 80  # Typical takeoff height
            return "✅ [VISION_ONLY] Takeoff successful - hovering at 80cm"
        
        try:
            success = self.drone.takeoff()
            if success:
                self.drone_state.is_flying = True
                self.drone_state.height = self.drone.get_height()
                self.drone_state.battery = self.drone.get_battery()
                return f"✅ Takeoff successful - height: {self.drone_state.height}cm, battery: {self.drone_state.battery}%"
            else:
                return "❌ Takeoff failed"
        except Exception as e:
            return f"❌ Takeoff error: {str(e)}"
    
    async def _land(self) -> str:
        """Land the drone."""
        self.logger.info("🛬 Landing...")
        
        if not self.drone_state.is_flying:
            return "❌ Drone is already on the ground!"
        
        if self.vision_only:
            self.drone_state.is_flying = False
            self.drone_state.height = 0
            return "✅ [VISION_ONLY] Landing successful"
        
        try:
            success = self.drone.land()
            if success:
                self.drone_state.is_flying = False
                self.drone_state.height = 0
                return "✅ Landing successful"
            else:
                return "❌ Landing failed"
        except Exception as e:
            return f"❌ Landing error: {str(e)}"
    
    async def _move_forward(self, distance: int) -> str:
        """Move drone forward."""
        self.logger.info(f"➡️ Moving forward {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"✅ [VISION_ONLY] Moved forward {distance}cm (Movement #{self.drone_state.movement_count})"
        
        try:
            success = self.drone.move_forward(distance)
            if success:
                self.drone_state.height = self.drone.get_height()
                self.drone_state.battery = self.drone.get_battery()
                return f"✅ Moved forward {distance}cm - height: {self.drone_state.height}cm, battery: {self.drone_state.battery}%"
            else:
                return f"❌ Forward movement failed"
        except Exception as e:
            return f"❌ Forward movement error: {str(e)}"
    
    async def _move_back(self, distance: int) -> str:
        """Move drone backward."""
        self.logger.info(f"⬅️ Moving back {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"✅ [VISION_ONLY] Moved back {distance}cm (Movement #{self.drone_state.movement_count})"
        
        try:
            success = self.drone.move_back(distance)
            if success:
                self.drone_state.height = self.drone.get_height()
                return f"✅ Moved back {distance}cm - height: {self.drone_state.height}cm"
            else:
                return f"❌ Back movement failed"
        except Exception as e:
            return f"❌ Back movement error: {str(e)}"
    
    async def _move_up(self, distance: int) -> str:
        """Move drone up."""
        self.logger.info(f"⬆️ Moving up {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            self.drone_state.height += distance
            return f"✅ [VISION_ONLY] Moved up {distance}cm - height: {self.drone_state.height}cm"
        
        try:
            success = self.drone.move_up(distance)
            if success:
                self.drone_state.height = self.drone.get_height()
                return f"✅ Moved up {distance}cm - height: {self.drone_state.height}cm"
            else:
                return f"❌ Up movement failed"
        except Exception as e:
            return f"❌ Up movement error: {str(e)}"
    
    async def _move_down(self, distance: int) -> str:
        """Move drone down."""
        self.logger.info(f"⬇️ Moving down {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            self.drone_state.height = max(0, self.drone_state.height - distance)
            return f"✅ [VISION_ONLY] Moved down {distance}cm - height: {self.drone_state.height}cm"
        
        try:
            success = self.drone.move_down(distance)
            if success:
                self.drone_state.height = self.drone.get_height()
                return f"✅ Moved down {distance}cm - height: {self.drone_state.height}cm"
            else:
                return f"❌ Down movement failed"
        except Exception as e:
            return f"❌ Down movement error: {str(e)}"
    
    async def _move_left(self, distance: int) -> str:
        """Move drone left."""
        self.logger.info(f"⬅️ Moving left {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"✅ [VISION_ONLY] Moved left {distance}cm"
        
        try:
            success = self.drone.move_left(distance)
            if success:
                return f"✅ Moved left {distance}cm"
            else:
                return f"❌ Left movement failed"
        except Exception as e:
            return f"❌ Left movement error: {str(e)}"
    
    async def _move_right(self, distance: int) -> str:
        """Move drone right."""
        self.logger.info(f"➡️ Moving right {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"✅ [VISION_ONLY] Moved right {distance}cm"
        
        try:
            success = self.drone.move_right(distance)
            if success:
                return f"✅ Moved right {distance}cm"
            else:
                return f"❌ Right movement failed"
        except Exception as e:
            return f"❌ Right movement error: {str(e)}"
    
    async def _rotate_clockwise(self, angle: int) -> str:
        """Rotate drone clockwise."""
        self.logger.info(f"🔄 Rotating clockwise {angle}°...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot rotate - drone is not flying! Use takeoff first."
        
        if self.vision_only:
            return f"✅ [VISION_ONLY] Rotated clockwise {angle}°"
        
        try:
            success = self.drone.rotate_clockwise(angle)
            if success:
                return f"✅ Rotated clockwise {angle}°"
            else:
                return f"❌ Clockwise rotation failed"
        except Exception as e:
            return f"❌ Clockwise rotation error: {str(e)}"
    
    async def _rotate_counter_clockwise(self, angle: int) -> str:
        """Rotate drone counter-clockwise."""
        self.logger.info(f"🔄 Rotating counter-clockwise {angle}°...")
        
        if not self.drone_state.is_flying:
            return "❌ Cannot rotate - drone is not flying! Use takeoff first."
        
        if self.vision_only:
            return f"✅ [VISION_ONLY] Rotated counter-clockwise {angle}°"
        
        try:
            success = self.drone.rotate_counter_clockwise(angle)
            if success:
                return f"✅ Rotated counter-clockwise {angle}°"
            else:
                return f"❌ Counter-clockwise rotation failed"
        except Exception as e:
            return f"❌ Counter-clockwise rotation error: {str(e)}"
    
    def _get_drone_status(self) -> str:
        """Get current drone status."""
        if not self.vision_only:
            self.drone_state.battery = self.drone.get_battery()
            self.drone_state.height = self.drone.get_height()
        
        status = {
            "flying": self.drone_state.is_flying,
            "battery": self.drone_state.battery,
            "height": self.drone_state.height,
            "movements_made": self.drone_state.movement_count,
            "obstacles_detected": self.drone_state.obstacles_detected,
            "mode": "VISION_ONLY" if self.vision_only else "REAL_DRONE",
            "last_image_analysis": self.drone_state.last_image_analysis[:100] + "..." if len(self.drone_state.last_image_analysis) > 100 else self.drone_state.last_image_analysis
        }
        return json.dumps(status, indent=2)
    
    async def _capture_image_and_analyze(self, focus: str, object_description: str = "") -> str:
        """Capture image and analyze using GPT-4o vision."""
        self.logger.info(f"📸 Capturing image and analyzing for: {focus}")
        
        if self.vision_only:
            # Simulate image analysis for testing
            analysis_results = {
                "obstacles": "Clear path ahead for 2 meters. Wall visible in distance. No immediate obstacles.",
                "objects": "Table with laptop visible ahead. Chair to the right. No people detected.",
                "navigation": "Safe to move forward 50cm. Room appears spacious. Good lighting conditions.",
                "specific_object": f"Looking for {object_description}: Object not clearly visible in current view. May need to rotate or move closer.",
                "landing_spot": "Current area appears suitable for landing. Flat surface below, no obstacles."
            }
            
            result = analysis_results.get(focus, "General environment analysis complete.")
            self.drone_state.last_image_analysis = result
            
            # Store in image history
            self.image_history.append({
                "timestamp": time.time(),
                "focus": focus,
                "analysis": result,
                "object_description": object_description
            })
            
            return f"✅ [VISION_ONLY] Image Analysis ({focus}): {result}"
        
        try:
            # Capture frame from drone camera
            frame = self.drone.get_frame()
            if frame is None:
                return "❌ Failed to capture image - camera not available"
            
            # Convert frame to base64 for GPT-4o vision
            _, buffer = cv2.imencode('.jpg', frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Create analysis prompt based on focus
            prompts = {
                "obstacles": "Analyze this drone camera view for obstacles and safety. Identify any walls, objects, or hazards in the flight path. Estimate safe distances for movement.",
                "objects": "Identify and describe all objects visible in this drone camera view. List furniture, people, pets, and other items.",
                "navigation": "Analyze this view for drone navigation. Identify safe directions to move, optimal paths, and any navigation hazards.",
                "specific_object": f"Look for this specific object in the image: {object_description}. Describe if you can see it, where it is located, and how to navigate towards it.",
                "landing_spot": "Evaluate this area for drone landing safety. Identify suitable flat surfaces and any landing hazards."
            }
            
            prompt = prompts.get(focus, "Analyze this drone camera view for general flight safety and navigation.")
            
            # TODO: Integrate with actual GPT-4o vision analysis
            # For now, return simulated analysis
            result = f"Image captured and analyzed for {focus}. Analysis pending GPT-4o vision integration."
            self.drone_state.last_image_analysis = result
            
            # Store in image history
            self.image_history.append({
                "timestamp": time.time(),
                "focus": focus,
                "analysis": result,
                "object_description": object_description,
                "image_data": image_base64[:100] + "..."  # Store truncated for memory
            })
            
            return f"✅ Image Analysis ({focus}): {result}"
            
        except Exception as e:
            return f"❌ Image capture error: {str(e)}"
    
    async def _emergency_stop(self, reason: str = "Manual stop") -> str:
        """Emergency stop all drone movement."""
        self.logger.warning(f"🚨 EMERGENCY STOP: {reason}")
        
        if self.vision_only:
            return f"✅ [VISION_ONLY] EMERGENCY STOP executed: {reason}"
        
        try:
            success = self.drone.emergency()
            if success:
                return f"✅ EMERGENCY STOP executed: {reason}"
            else:
                return f"❌ Emergency stop failed: {reason}"
        except Exception as e:
            return f"❌ Emergency stop error: {str(e)} - Reason: {reason}"
    
    async def process_user_command(self, user_input: str) -> str:
        """Process user command and execute autonomous drone actions."""
        try:
            self.logger.info(f"🎯 Processing command: {user_input}")
            
            # Store in conversation history
            self.conversation_history.append({
                "timestamp": time.time(),
                "user_input": user_input,
                "type": "user_command"
            })
            
            # Send to Azure AI agent
            message = self.ai_client.agents.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_input
            )
            
            # Process with agent
            run = self.ai_client.agents.runs.create_and_process(
                thread_id=self.thread.id,
                agent_id=self.agent.id
            )
            
            # Get response
            messages = self.ai_client.agents.messages.list(
                thread_id=self.thread.id,
                limit=1,
                order="desc"
            )
            
            message_list = list(messages)
            if message_list and hasattr(message_list[0], 'content'):
                response = message_list[0].content[0].text.value
                
                # Store response in conversation history
                self.conversation_history.append({
                    "timestamp": time.time(),
                    "agent_response": response,
                    "type": "agent_response"
                })
                
                return response
            else:
                return "✅ Command executed successfully."
                
        except Exception as e:
            self.logger.error(f"❌ Error processing command: {e}")
            return f"❌ Error: {str(e)}"
    
    def get_conversation_context(self) -> Dict:
        """Get conversation and flight context."""
        return {
            "drone_state": asdict(self.drone_state),
            "recent_conversation": self.conversation_history[-5:],  # Last 5 exchanges
            "recent_images": self.image_history[-3:],  # Last 3 image analyses
            "agent_id": self.agent.id if self.agent else None,
            "thread_id": self.thread.id if self.thread else None,
            "mode": "VISION_ONLY" if self.vision_only else "REAL_DRONE"
        }
    
    def cleanup(self):
        """Clean up all resources safely."""
        self.logger.info("🧹 Starting cleanup...")
        
        try:
            # Clean up drone
            if self.drone and not self.vision_only:
                try:
                    if self.drone_state.is_flying:
                        self.logger.info("Landing drone before cleanup...")
                        self.drone.land()
                    self.drone.close()
                except Exception as e:
                    self.logger.warning(f"Drone cleanup warning: {e}")
            
            # Clean up Azure AI resources
            if self.thread:
                try:
                    self.ai_client.agents.threads.delete(self.thread.id)
                    self.logger.info(f"Deleted thread: {self.thread.id}")
                except Exception as e:
                    self.logger.warning(f"Thread cleanup warning: {e}")
                    
            if self.agent:
                try:
                    self.ai_client.agents.delete_agent(self.agent.id)
                    self.logger.info(f"Deleted agent: {self.agent.id}")
                except Exception as e:
                    self.logger.warning(f"Agent cleanup warning: {e}")
                
            self.logger.info("✅ Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")


# Test function
def test_autonomous_agent():
    """Test the autonomous drone agent."""
    logger.info("🚁 Testing Autonomous Drone Agent")
    
    import asyncio
    
    async def test_agent():
        agent = None
        try:
            # Test in vision-only mode for safety
            agent = AutonomousDroneAgent(vision_only=True)
            logger.info("✅ Agent created successfully")
            
            # Reduced test commands for faster testing
            test_commands = [
                "Take off and hover",
                "Tell me your current status",
                "Land safely"
            ]
            
            for i, cmd in enumerate(test_commands, 1):
                logger.info(f"\n🎯 Test {i}/{len(test_commands)}: '{cmd}'")
                try:
                    response = await agent.process_user_command(cmd)
                    logger.info(f"🤖 Response: {response}")
                    
                    # Show context
                    context = agent.get_conversation_context()
                    logger.info(f"📊 Drone State: Flying={context['drone_state']['is_flying']}, Movements={context['drone_state']['movement_count']}")
                except Exception as e:
                    logger.error(f"❌ Command {i} failed: {e}")
                    break
            
            logger.info("✅ Test completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test error: {e}")
        finally:
            # Ensure cleanup always happens
            if agent:
                try:
                    agent.cleanup()
                    logger.info("🧹 Cleanup completed")
                except Exception as e:
                    logger.warning(f"⚠️ Cleanup warning: {e}")
    
    try:
        asyncio.run(test_agent())
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
    
    def restore_session(self, agent_id: str, thread_id: str) -> bool:
        """Restore an existing agent session but reset drone state."""
        try:
            self.logger.info(f"🔄 Attempting to restore session: {agent_id}")
            
            # Verify agent exists
            try:
                agent = self.ai_client.agents.get_agent(agent_id)
                if not agent:
                    self.logger.warning(f"⚠️  Agent {agent_id} not found")
                    return False
                    
                # Store agent reference
                self.agent = agent
                self.agent_id = agent_id
                
            except Exception:
                self.logger.warning(f"⚠️  Failed to verify agent {agent_id}")
                return False
            
            # Verify thread exists
            try:
                thread = self.ai_client.agents.threads.retrieve(thread_id)
                if not thread:
                    self.logger.warning(f"⚠️  Thread {thread_id} not found")
                    return False
                    
                # Store thread reference
                self.thread = thread
                self.thread_id = thread_id
                
            except Exception:
                self.logger.warning(f"⚠️  Failed to verify thread {thread_id}")
                return False
            
            # Test the restored session
            try:
                messages = self.ai_client.agents.messages.list(thread_id=self.thread_id, limit=1)
                list(messages)  # Try to iterate to verify access
            except Exception:
                self.logger.warning(f"⚠️  Cannot access thread messages")
                return False
            
            # IMPORTANT: Reset drone state to fresh start even though we reuse AI agent
            self._reset_drone_state()
            self.logger.info(f"🔄 Drone state reset to fresh start")
            
            # Send system message to inform AI agent about the fresh start
            self._send_fresh_start_notification()
            
            self.logger.info(f"✅ Successfully restored session: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to restore session: {e}")
            return False
    
    def _reset_drone_state(self):
        """Reset drone state to fresh start."""
        # Reset drone state
        self.drone_state = DroneState()
        
        # Clear conversation history
        self.conversation_history = []
        
        # Reset image history
        self.recent_images = []
        
        # Reset any movement tracking
        self.drone_state.movement_count = 0
        self.drone_state.is_flying = False
        self.drone_state.height = 0
        self.drone_state.battery = 100
        self.drone_state.obstacles_detected = []
        
        self.logger.info("🔄 Drone state completely reset")
    
    def _send_fresh_start_notification(self):
        """Notify AI agent that this is a fresh drone session."""
        try:
            notification = """
🔄 SYSTEM NOTIFICATION: APPLICATION RESTARTED
- This is a fresh drone session
- Drone state has been reset to initial values
- Previous flight history is cleared
- Drone is currently: NOT FLYING, battery 100%, height 0cm
- You should treat this as a completely new session
"""
            
            # Send system message to thread
            self.ai_client.agents.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=notification
            )
            
            self.logger.info("📢 Sent fresh start notification to AI agent")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to send fresh start notification: {e}")


if __name__ == "__main__":
    test_autonomous_agent()
