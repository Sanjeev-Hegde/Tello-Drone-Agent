#!/usr/bin/env python3
"""
Main entry point for the Tello Drone Agent.
Uses Azure AI Agents for autonomous drone control with vision tools.
"""

import asyncio
import logging
import time
import sys
import os
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for vision-only mode
vision_only = "--vision-only" in sys.argv

# Always import vision components
from agents.vision_agent import VisionAgent
from vision.camera_manager import CameraManager
from config.settings import settings, setup_logging

# Import the new hybrid agent
from agents.hybrid_drone_agent import HybridDroneAgent

# Conditionally import drone components for integration
if not vision_only:
    from drone.tello_controller import TelloController


class TelloDroneAgent:
    """Main application class using Azure AI Agents for autonomous control."""
    
    def __init__(self, vision_analysis_enabled: bool = True):
        self.logger = logging.getLogger(__name__)
        self.vision_analysis_enabled = vision_analysis_enabled
        self.running = False
        
        # Initialize components
        self.camera_manager = CameraManager()
        self.vision_agent = VisionAgent() if vision_analysis_enabled else None
        
        # Initialize the hybrid AI agent
        self.hybrid_agent = HybridDroneAgent(vision_only=vision_only)
        
        # Drone controller (conditional)
        if not vision_only:
            self.tello_controller = TelloController()
        else:
            self.tello_controller = None
            self.logger.info("Running in VISION-ONLY mode - no drone will be controlled")
    
    async def run_interactive_mode(self):
        """Run the agent in interactive mode with AI autonomy."""
        self.logger.info("Starting Tello Drone Agent with Azure AI Agents...")
        self.running = True
        
        try:
            # Start camera
            await self.camera_manager.start()
            
            print("\n🤖 Autonomous Tello Drone Agent Ready!")
            print("💡 Give natural language commands - the AI will handle the details")
            print("🎯 Examples:")
            print("   • 'Take off and look around for people'")
            print("   • 'Move forward carefully avoiding obstacles'") 
            print("   • 'Find the best angle to view the room'")
            print("   • 'Land safely'")
            if vision_only:
                print("⚠️  VISION-ONLY MODE: Using simulated drone and webcam")
            print("=" * 70)
            
            while self.running:
                try:
                    # Get user input
                    user_input = input("\n🎤 Tell me what to do: ").strip()
                    
                    if not user_input:
                        continue
                        
                    if user_input.lower() in ['quit', 'exit', 'q', 'stop']:
                        print("👋 Shutting down...")
                        break
                    
                    # Process through AI agent
                    await self.process_ai_command(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interrupted! Emergency landing...")
                    break
                except Exception as e:
                    self.logger.error(f"Error in interactive loop: {e}")
                    print(f"❌ Error: {e}")
                    
        finally:
            await self.cleanup()
    
    async def process_ai_command(self, user_input: str):
        """Process command through the autonomous AI agent."""
        start_time = time.time()
        
        try:
            print(f"\n🧠 AI Agent processing: '{user_input}'")
            print("⏳ Thinking...")
            
            # Let the AI agent handle everything autonomously
            response = await self.hybrid_agent.process_user_request(user_input)
            
            # Display the AI's response
            print(f"\n🤖 AI Agent: {response}")
                
            # Show timing
            elapsed = time.time() - start_time
            print(f"⏱️  Completed in {elapsed:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Error processing AI command '{user_input}': {e}")
            print(f"❌ AI Agent failed: {e}")
    
    async def cleanup(self):
        """Clean up all resources."""
        self.running = False
        
        try:
            # Emergency landing through AI agent if needed
            if not vision_only:
                print("🚨 Requesting emergency landing...")
                await self.hybrid_agent.process_user_request("Emergency land now for safety")
            
            # Stop camera
            if self.camera_manager:
                await self.camera_manager.stop()
            
            # Cleanup hybrid agent
            if self.hybrid_agent:
                self.hybrid_agent.cleanup()
            
            # Cleanup drone controller
            if self.tello_controller:
                self.tello_controller.cleanup()
                
            print("🧹 Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


async def main():
    """Main entry point."""
    # Setup logging first
    setup_logging()
    
    # Check for vision-only mode
    vision_analysis_enabled = "--no-vision" not in sys.argv
    
    # Create and run agent
    agent = TelloDroneAgent(vision_analysis_enabled=vision_analysis_enabled)
    await agent.run_interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
    
    async def initialize(self):
        """Initialize all components."""
        try:
            self.logger.info("Initializing Tello Drone AI Agent...")
            
            # Initialize vision agent
            self.vision_agent = VisionAgent()
            self.logger.info("Vision agent initialized")
            
            # Initialize camera manager
            camera_source = settings.camera_source
            self.camera_manager = CameraManager(
                source=camera_source,
                frame_callback=self.process_frame
            )
            self.logger.info(f"Camera manager initialized with source: {camera_source}")
            
            if not self.vision_only:
                # Import drone-related modules only when needed
                global ControlAgent, TelloController, DroneCommand, DroneAction
                from agents.control_agent import ControlAgent
                from drone.tello_controller import TelloController
                from drone.commands import DroneCommand, DroneAction
                
                # Initialize control agent for full drone control mode
                self.control_agent = ControlAgent()
                self.logger.info("Control agent initialized")
                
                # Initialize Tello controller for drone commands
                self.tello_controller = TelloController()
                self.logger.info("Tello controller initialized")
            else:
                self.logger.info("Vision-only mode: skipping control agent and drone controller initialization")
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def process_frame(self, frame) -> None:
        """Process a single frame from the camera (only when vision analysis is enabled)."""
        try:
            # Always store the latest frame
            if isinstance(frame, Image.Image):
                self.latest_frame = frame
            else:
                # Convert numpy array to PIL Image
                if frame.dtype != np.uint8:
                    frame = (frame * 255).astype(np.uint8)
                
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame_rgb = frame[:, :, ::-1]  # BGR to RGB
                else:
                    frame_rgb = frame
                
                self.latest_frame = Image.fromarray(frame_rgb)
            
            # Only analyze if vision analysis is enabled (during specific tasks)
            if self.vision_analysis_enabled and self.vision_agent:
                analysis = await self.vision_agent.analyze_image(self.latest_frame)
                if analysis:
                    self.latest_analysis = analysis
                    self.logger.debug(f"Vision analysis updated: {len(analysis.get('objects', []))} objects detected")
                
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
    
    def add_command(self, command_text: str):
        """Add a user command to the queue."""
        self.command_queue.put(command_text)
        self.logger.info(f"Command queued: {command_text}")
    
    async def execute_user_commands(self):
        """Execute user commands from the queue."""
        while self.running:
            try:
                # Check for new commands (non-blocking)
                try:
                    command_text = self.command_queue.get_nowait()
                    self.logger.info(f"🎮 Executing command: {command_text}")
                    
                    # Enable vision analysis for commands that might need it
                    # Let the control agent decide if vision is needed
                    if any(keyword in command_text.lower() for keyword in 
                           ['analyze', 'detect', 'find', 'scan', 'rotate', 'capture', 'search', 'look']):
                        self.vision_analysis_enabled = True
                        self.logger.info("📹 Vision analysis enabled for this command")
                    
                    # Use control agent for ALL commands (natural language processing)
                    if self.control_agent:
                        command = await self.control_agent.process_command(command_text)
                        if command and self.tello_controller:
                            # Track takeoff/landing state
                            if command.action == DroneAction.TAKEOFF:
                                self.drone_is_flying = True
                                self.logger.info("🛫 Drone state: FLYING")
                            elif command.action == DroneAction.LAND:
                                self.drone_is_flying = False
                                self.logger.info("🛬 Drone state: LANDED")
                            
                            # Check if this is a 360-degree scan command
                            if (command.action == DroneAction.ROTATE_CLOCKWISE and 
                                "360" in command_text.lower() and "analyze" in command_text.lower()):
                                await self._execute_360_scan()
                            else:
                                # Execute the command normally
                                await self.tello_controller.execute_command(command)
                        else:
                            self.logger.warning("⚠️  Control agent couldn't process the command")
                    else:
                        # Vision-only mode: handle basic vision commands
                        if any(keyword in command_text.lower() for keyword in ['analyze', 'capture', 'detect', 'look']):
                            await self._execute_image_analysis()
                        else:
                            self.logger.info("ℹ️  Vision-only mode: Only vision analysis commands are supported")
                            self.logger.info("     Try: 'analyze image', 'capture and analyze', 'detect objects'")
                    
                    # Disable vision analysis after command (unless it's a continuous scan)
                    if "continuous" not in command_text.lower() and "monitor" not in command_text.lower():
                        self.vision_analysis_enabled = False
                        self.logger.info("📹 Vision analysis disabled")
                    
                    self.command_queue.task_done()
                    
                except queue.Empty:
                    # No commands in queue, wait
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Error executing command: {e}")
                await asyncio.sleep(1)
    
    async def _execute_360_scan(self):
        """Execute 360-degree rotation with continuous image capture and analysis."""
        self.logger.info("🔄 Starting 360-degree scan with image analysis...")
        
        if not self.tello_controller:
            self.logger.error("❌ No drone controller available")
            return
        
        # Enable vision analysis
        self.vision_analysis_enabled = True
        
        # Rotate in 45-degree increments (8 positions)
        angles_per_step = 45
        total_steps = 8
        detected_objects = {}
        
        for step in range(total_steps):
            current_angle = step * angles_per_step
            self.logger.info(f"📐 Rotating to {current_angle}° ({step + 1}/{total_steps})")
            
            # Rotate
            command = DroneCommand(action=DroneAction.ROTATE_CLOCKWISE, value=angles_per_step)
            await self.tello_controller.execute_command(command)
            
            # Wait for rotation to complete and image to stabilize
            await asyncio.sleep(2)
            
            # Capture and analyze current view
            if self.latest_analysis:
                objects = self.latest_analysis.get('objects', [])
                if objects:
                    self.logger.info(f"🔍 At {current_angle}°: Found {len(objects)} objects")
                    for i, obj in enumerate(objects):
                        obj_key = f"{current_angle}°_object_{i}"
                        detected_objects[obj_key] = {
                            'angle': current_angle,
                            'description': str(obj),
                            'confidence': getattr(obj, 'confidence', 0.0)
                        }
        
        # Summary of 360-degree scan
        self.logger.info("🎯 360-degree scan complete!")
        self.logger.info(f"📊 Total objects detected: {len(detected_objects)}")
        
        for obj_key, obj_data in detected_objects.items():
            self.logger.info(f"  • {obj_data['angle']}°: {obj_data['description']}")
        
        # Disable continuous vision analysis
        self.vision_analysis_enabled = False
    
    async def _execute_image_analysis(self):
        """Execute single image capture and analysis."""
        self.logger.info("📸 Capturing and analyzing current view...")
        
        # Enable vision analysis temporarily
        self.vision_analysis_enabled = True
        await asyncio.sleep(1)  # Wait for analysis to process current frame
        
        if self.latest_analysis:
            self.logger.info("🔍 Image Analysis Results:")
            
            # Objects
            objects = self.latest_analysis.get('objects', [])
            if objects:
                self.logger.info(f"  📦 Objects detected: {len(objects)}")
                for i, obj in enumerate(objects[:5]):  # Show top 5
                    self.logger.info(f"    {i+1}. {obj}")
            
            # People
            people = self.latest_analysis.get('people', [])
            if people:
                self.logger.info(f"  👥 People detected: {len(people)}")
            
            # Description
            description = self.latest_analysis.get('description', '')
            if description:
                self.logger.info(f"  📝 Description: {description}")
            
            # Tags
            tags = self.latest_analysis.get('tags', [])
            if tags:
                self.logger.info(f"  🏷️  Tags: {', '.join(tags[:10])}")  # Show top 10 tags
            
            if not any([objects, people, description, tags]):
                self.logger.info("  ℹ️  No objects or features detected in current view")
        else:
            self.logger.warning("⚠️  No analysis data available - make sure camera is working")
        
        self.vision_analysis_enabled = False
    
    def start_command_interface(self):
        """Start the command input interface in a separate thread."""
        def command_input():
            self.logger.info("🎮 Command interface started. Type commands or 'quit' to exit:")
            if self.vision_only:
                self.logger.info("📋 Vision-only mode - Available commands:")
                self.logger.info("  - analyze image")
                self.logger.info("  - capture and analyze")
                self.logger.info("  - detect objects")
                self.logger.info("  - look at current view")
            else:
                self.logger.info("📋 Example commands (all processed by Azure OpenAI):")
                self.logger.info("  - take off")
                self.logger.info("  - land")
                self.logger.info("  - rotate 360 degrees and analyze images")
                self.logger.info("  - move forward 50 centimeters")
                self.logger.info("  - move up 30cm then rotate left 90 degrees")
                self.logger.info("  - capture and analyze the current image")
                self.logger.info("  - fly in a square pattern")
                self.logger.info("  - Any other natural language command!")
            
            while self.running:
                try:
                    command = input("🎮 Enter command: ").strip()
                    if command.lower() in ['quit', 'exit', 'stop']:
                        self.running = False
                        break
                    elif command:
                        self.add_command(command)
                except (EOFError, KeyboardInterrupt):
                    self.running = False
                    break
        
        # Start input thread
        input_thread = threading.Thread(target=command_input, daemon=True)
        input_thread.start()
    
    async def run(self):
        """Main application loop."""
        try:
            await self.initialize()
            
            self.running = True
            self.logger.info("Starting Tello Drone AI Agent...")
            
            if self.vision_only:
                self.logger.info("Running in vision-only mode")
            else:
                self.logger.info("Running in full drone control mode")
            
            # Start camera
            await self.camera_manager.start()
            self.logger.info("Camera started")
            
            # Start command interface
            self.start_command_interface()
            
            # Start command executor
            command_task = asyncio.create_task(self.execute_user_commands())
            
            # Main loop - just keep camera running and process frames
            frame_count = 0
            while self.running:
                try:
                    # Capture frame (always capture, but only analyze when needed)
                    frame = self.camera_manager.capture_single_frame()
                    if frame is not None:
                        await self.process_frame(frame)
                        frame_count += 1
                        
                        # Log less frequently since we're not analyzing every frame
                        if frame_count % 300 == 0:  # Every 10 seconds at 30 FPS
                            self.logger.debug(f"Camera running: {frame_count} frames captured")
                    
                    # Reduce loop frequency since we're not processing every frame
                    await asyncio.sleep(0.1)  # 10 Hz main loop
                    
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(1)
            
            # Wait for command task to complete
            command_task.cancel()
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources with emergency landing if needed."""
        self.logger.info("Cleaning up...")
        self.running = False
        
        # Emergency landing if drone is still flying
        if self.drone_is_flying and self.tello_controller and not self.vision_only:
            self.logger.warning("🚨 EMERGENCY: Drone is flying! Attempting emergency landing...")
            try:
                # First try normal landing
                landing_command = DroneCommand(action=DroneAction.LAND)
                success = await asyncio.wait_for(
                    self.tello_controller.execute_command(landing_command), 
                    timeout=10.0
                )
                if success:
                    self.logger.info("✅ Emergency landing successful!")
                else:
                    # If normal landing fails, try emergency stop
                    self.logger.warning("⚠️  Normal landing failed, trying emergency stop...")
                    emergency_command = DroneCommand(action=DroneAction.EMERGENCY_STOP)
                    await self.tello_controller.execute_command(emergency_command)
                    self.logger.info("🛑 Emergency stop executed!")
            except asyncio.TimeoutError:
                self.logger.error("❌ Emergency landing timed out!")
            except Exception as e:
                self.logger.error(f"❌ Emergency landing error: {e}")
            finally:
                self.drone_is_flying = False
        
        if self.camera_manager:
            await self.camera_manager.stop()
            
        if self.tello_controller:
            await self.tello_controller.disconnect()
        
        self.logger.info("Cleanup completed")
    
    def handle_signal(self, signum, frame):
        """Handle system signals with emergency landing."""
        self.logger.warning(f"🚨 Received signal {signum} - initiating emergency shutdown!")
        if self.drone_is_flying:
            self.logger.warning("🚨 DRONE IS FLYING - Emergency landing will be attempted during cleanup!")
        self.running = False


@click.command()
@click.option('--vision-only', is_flag=True, help='Run in vision-only mode (no drone control)')
@click.option('--camera-source', default=None, help='Camera source: webcam or tello')
@click.option('--log-level', default='INFO', help='Log level: DEBUG, INFO, WARNING, ERROR')
def main(vision_only: bool, camera_source: Optional[str], log_level: str):
    """
    Tello Drone AI Agent - User-commanded drone control with computer vision.
    
    This application provides:
    - User command interface for drone control
    - Natural language to drone command conversion using Azure OpenAI
    - Vision-assisted command execution using Azure AI Vision
    - Tello drone integration for autonomous flight
    - Vision-only mode for testing without drone
    """
    
    # Setup logging
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # Override camera source if provided
    if camera_source:
        settings.camera_source = camera_source
    
    # Create and run the application
    app = TelloDroneAgent(vision_only=vision_only)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)
    
    try:
        # Run the application
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("🚨 Received keyboard interrupt - emergency shutdown initiated")
    except Exception as e:
        logger.error(f"Application failed: {e}")
    finally:
        # Ensure emergency cleanup runs even if there's an exception
        logger.info("Running final cleanup...")
        try:
            asyncio.run(app.cleanup())
        except Exception as cleanup_error:
            logger.error(f"Error during final cleanup: {cleanup_error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
