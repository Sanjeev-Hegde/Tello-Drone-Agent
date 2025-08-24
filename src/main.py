"""
Main application entry point for Tello Drone AI Agent.
"""

import asyncio
import logging
import signal
import sys
import os
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
from PIL import Image
import numpy as np

from config.settings import settings, setup_logging
from agents.control_agent import ControlAgent
from agents.vision_agent import VisionAgent
from drone.tello_controller import TelloController
from drone.commands import DroneCommand, DroneAction
from vision.camera_manager import CameraManager


class TelloDroneAgent:
    """Main application class for the Tello Drone AI Agent."""
    
    def __init__(self, vision_only: bool = False):
        self.logger = logging.getLogger(__name__)
        self.vision_only = vision_only
        self.running = False
        
        # Initialize components
        self.control_agent = None
        self.vision_agent = None
        self.tello_controller = None
        self.camera_manager = None
        
    async def initialize(self):
        """Initialize all components."""
        try:
            self.logger.info("Initializing Tello Drone AI Agent...")
            
            # Initialize vision agent
            self.vision_agent = VisionAgent()
            self.logger.info("Vision agent initialized")
            
            # Initialize camera manager
            # Use the configured camera source (can be webcam or tello)
            camera_source = settings.camera_source
            self.camera_manager = CameraManager(
                source=camera_source,
                frame_callback=self.process_frame
            )
            self.logger.info(f"Camera manager initialized with source: {camera_source}")
            
            if not self.vision_only:
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
        """Process a single frame from the camera."""
        try:
            if self.vision_agent:
                # Handle both numpy arrays and PIL Images
                if isinstance(frame, Image.Image):
                    # Frame is already a PIL Image from camera manager
                    image = frame
                else:
                    # Frame is a numpy array, convert to PIL Image
                    if frame.dtype != np.uint8:
                        frame = (frame * 255).astype(np.uint8)
                    
                    # Convert BGR to RGB if needed
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame_rgb = frame[:, :, ::-1]  # BGR to RGB
                    else:
                        frame_rgb = frame
                    
                    image = Image.fromarray(frame_rgb)
                
                # Analyze the frame
                analysis = await self.vision_agent.analyze_image(image)
                
                if analysis:
                    self.logger.info(f"Vision analysis: {analysis}")
                    
                    # If not vision-only mode, process commands
                    if not self.vision_only and self.control_agent and analysis.get('navigation_suggestions'):
                        suggestions = analysis['navigation_suggestions']
                        if suggestions and len(suggestions) > 0:
                            # Process the first suggestion as a command
                            command_text = suggestions[0]
                            try:
                                command = await self.control_agent.process_command(command_text)
                                if command and self.tello_controller:
                                    await self.tello_controller.execute_command(command)
                            except Exception as cmd_error:
                                self.logger.error(f"Failed to process command '{command_text}': {cmd_error}")
                
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
    
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
            
            # Main processing loop
            frame_count = 0
            while self.running:
                try:
                    # Capture and process frame
                    frame = self.camera_manager.capture_single_frame()
                    if frame is not None:
                        await self.process_frame(frame)
                        frame_count += 1
                        
                        # Log every 30 frames (roughly once per second)
                        if frame_count % 30 == 0:
                            self.logger.info(f"Processed {frame_count} frames")
                    
                    # Small delay to maintain frame rate
                    await asyncio.sleep(0.033)  # ~30 FPS
                    
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(1)  # Wait before retrying
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up...")
        self.running = False
        
        if self.camera_manager:
            await self.camera_manager.stop()
            
        if self.tello_controller:
            await self.tello_controller.disconnect()
        
        self.logger.info("Cleanup completed")
    
    def handle_signal(self, signum, frame):
        """Handle system signals."""
        self.logger.info(f"Received signal {signum}")
        self.running = False


@click.command()
@click.option('--vision-only', is_flag=True, help='Run in vision-only mode (no drone control)')
@click.option('--camera-source', default=None, help='Camera source: webcam or tello')
@click.option('--log-level', default='INFO', help='Log level: DEBUG, INFO, WARNING, ERROR')
def main(vision_only: bool, camera_source: Optional[str], log_level: str):
    """
    Tello Drone AI Agent - Natural language drone control with computer vision.
    
    This application provides:
    - Natural language to drone command conversion using Azure OpenAI
    - Real-time computer vision analysis using Azure AI Vision
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
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
