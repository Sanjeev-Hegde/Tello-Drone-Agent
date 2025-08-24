"""
Camera Manager for Tello Drone AI Agent.
Handles camera input from webcam or Tello drone.
"""

import cv2
import numpy as np
import asyncio
import threading
import logging
from typing import Optional, Callable
from drone.simple_tello import SimpleTello
from PIL import Image


class CameraManager:
    """Simple camera manager that supports both webcam and Tello drone cameras."""
    
    def __init__(self, source: str = "webcam", frame_callback: Optional[Callable] = None):
        self.source = source
        self.frame_callback = frame_callback
        self.running = False
        self.capture_thread = None
        self.logger = logging.getLogger(__name__)
        
        # Camera objects
        self.webcam = None
        self.tello = None
        
        # Frame dimensions
        self.frame_width = 640
        self.frame_height = 480

    async def start(self):
        """Start the camera based on source type."""
        try:
            self.logger.info(f"Starting camera with source: {self.source}")
            
            if self.source == "tello":
                await self._start_tello_camera()
            else:
                await self._start_webcam()
                
            self.running = True
            self.logger.info("Camera started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start camera: {e}")
            raise

    async def _start_tello_camera(self):
        """Start Tello drone camera."""
        try:
            self.logger.info("🚁 Connecting to Tello drone...")
            self.logger.info("📋 TELLO SETUP CHECKLIST:")
            self.logger.info("   1. Power on your Tello drone")
            self.logger.info("   2. Connect your computer to the Tello WiFi network (TELLO-XXXXXX)")
            self.logger.info("   3. Wait for the WiFi connection to establish")
            self.logger.info("   4. Make sure no other apps are connected to the Tello")
            
            self.tello = SimpleTello()
            connected = self.tello.connect()
            
            # Check battery level
            battery = self.tello.get_battery()
            self.logger.info(f"✅ Tello connected! Battery level: {battery}%")
            
            if battery < 20:
                self.logger.warning("⚠️  Low battery! Consider charging before extended use.")
            
            # Start video stream
            self.tello.streamon()
            self.logger.info("📹 Tello video stream started")
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._tello_capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
        except Exception as e:
            self.logger.error("❌ TELLO CONNECTION FAILED")
            self.logger.error("🔧 TROUBLESHOOTING STEPS:")
            self.logger.error("   1. Check if Tello is powered on (LED should be solid)")
            self.logger.error("   2. Connect to Tello WiFi: TELLO-XXXXXX (check drone sticker)")
            self.logger.error("   3. Verify network connection: ping 192.168.10.1")
            self.logger.error("   4. Close other Tello apps (DJI GO, etc.)")
            self.logger.error("   5. Try restarting the Tello drone")
            self.logger.error(f"   Error details: {e}")
            raise RuntimeError(f"Failed to connect to Tello drone: {e}")

    async def _start_webcam(self):
        """Start real webcam."""
        try:
            # Try to open the default camera (index 0)
            self.webcam = cv2.VideoCapture(0)
            
            if not self.webcam.isOpened():
                self.logger.error("❌ CAMERA ACCESS DENIED")
                self.logger.error("📋 TO FIX THIS:")
                self.logger.error("   1. Go to System Preferences > Security & Privacy > Privacy > Camera")
                self.logger.error("   2. Enable camera access for Terminal or your Python IDE")
                self.logger.error("   3. Restart this application")
                self.logger.error("   4. Or use CAMERA_SOURCE=tello in .env to use Tello drone camera")
                raise RuntimeError("Webcam access denied. Please enable camera permissions.")
            
            # Set resolution
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            
            self.logger.info("✅ Webcam started successfully")
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._webcam_capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
        except Exception as e:
            if "denied" in str(e).lower() or "access" in str(e).lower():
                # Already logged detailed instructions above
                pass
            else:
                self.logger.error(f"Failed to start webcam: {e}")
            raise

    def _tello_capture_loop(self):
        """Main capture loop for Tello camera."""
        # Start the frame reader
        frame_reader = self.tello.get_frame_read()
        frame_reader.start()
        
        while self.running:
            try:
                if frame_reader and frame_reader.frame is not None:
                    # Get frame from Tello
                    frame = frame_reader.frame
                    
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame)
                    
                    # Call frame callback if provided
                    if self.frame_callback:
                        asyncio.run_coroutine_threadsafe(
                            self.frame_callback(pil_image), 
                            asyncio.get_event_loop()
                        )
            
                # Small delay to prevent excessive CPU usage
                import time
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.logger.error(f"Error in Tello capture loop: {e}")
                break
        
        # Stop frame reader
        if frame_reader:
            frame_reader.stop()

    def _webcam_capture_loop(self):
        """Main capture loop for webcam."""
        while self.running:
            try:
                if self.webcam and self.webcam.isOpened():
                    ret, frame = self.webcam.read()
                    if ret and frame is not None:
                        # Convert BGR to RGB
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Convert to PIL Image
                        pil_image = Image.fromarray(rgb_frame)
                        
                        # Call frame callback if provided
                        if self.frame_callback:
                            try:
                                # Get or create event loop
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        asyncio.run_coroutine_threadsafe(
                                            self.frame_callback(pil_image), loop
                                        )
                                    else:
                                        asyncio.run(self.frame_callback(pil_image))
                                except RuntimeError:
                                    # No event loop in current thread, create one
                                    asyncio.run(self.frame_callback(pil_image))
                            except Exception as e:
                                self.logger.error(f"Error in frame callback: {e}")
                
                # Small delay to prevent excessive CPU usage
                import time
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.logger.error(f"Error in webcam capture loop: {e}")
                break

    def capture_single_frame(self):
        """Capture a single frame (for testing)."""
        try:
            if self.source == "tello" and self.tello:
                frame_reader = self.tello.get_frame_read()
                if frame_reader and frame_reader.frame is not None:
                    return Image.fromarray(frame_reader.frame)
            
            elif self.source == "webcam" and self.webcam and self.webcam.isOpened():
                ret, frame = self.webcam.read()
                if ret and frame is not None:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    return Image.fromarray(rgb_frame)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error capturing single frame: {e}")
            return None

    async def stop(self):
        """Stop the camera capture."""
        self.logger.info("Stopping camera...")
        self.running = False
        
        # Wait for capture thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        # Clean up camera resources
        if self.webcam:
            self.webcam.release()
            self.webcam = None
        
        if self.tello:
            try:
                self.tello.streamoff()
                self.tello.close()
            except:
                pass
            self.tello = None
        
        self.logger.info("Camera stopped")

    def is_running(self) -> bool:
        """Check if camera is running."""
        return self.running
