"""
Simple Tello SDK wrapper using djitellopy for reliable drone operations.
This provides a clean interface while leveraging the mature djitellopy library.
"""

import logging
import cv2
import numpy as np
from typing import Optional, Callable
try:
    from djitellopy import Tello
except ImportError:
    print("djitellopy not found. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "djitellopy"])
    from djitellopy import Tello


class SimpleTello:
    """Simple Tello drone controller using djitellopy."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tello = Tello()
        self.is_connected = False
        self.video_enabled = False
        
    def connect(self) -> bool:
        """Connect to Tello drone."""
        try:
            self.logger.info("Connecting to Tello...")
            self.tello.connect()
            self.is_connected = True
            self.logger.info("✅ Tello connected successfully!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Tello connection error: {e}")
            self.is_connected = False
            return False
    
    def close(self):
        """Close connection to Tello."""
        try:
            if self.video_enabled:
                self.streamoff()
            if self.is_connected:
                self.tello.end()
                self.is_connected = False
            self.logger.info("Tello connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Tello connection: {e}")
    
    def get_battery(self) -> int:
        """Get battery level."""
        try:
            if not self.is_connected:
                return 0
            return self.tello.get_battery()
        except Exception as e:
            self.logger.error(f"Error getting battery: {e}")
            return 0
    
    def streamon(self) -> bool:
        """Start video stream."""
        try:
            if not self.is_connected:
                return False
            self.tello.streamon()
            self.video_enabled = True
            self.logger.info("📹 Video stream started")
            return True
        except Exception as e:
            self.logger.error(f"Error starting video stream: {e}")
            return False
    
    def streamoff(self) -> bool:
        """Stop video stream."""
        try:
            if self.video_enabled:
                self.tello.streamoff()
                self.video_enabled = False
                self.logger.info("📹 Video stream stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping video stream: {e}")
            return False
    
    def get_frame_read(self):
        """Get frame reader for video stream."""
        if not self.video_enabled:
            return None
        return self.tello.get_frame_read()
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get a single frame from video stream."""
        try:
            if not self.video_enabled:
                return None
            frame_read = self.tello.get_frame_read()
            if frame_read and frame_read.frame is not None:
                return frame_read.frame
            return None
        except Exception as e:
            self.logger.error(f"Error getting frame: {e}")
            return None
    
    # Movement commands
    def takeoff(self) -> bool:
        """Take off."""
        try:
            if not self.is_connected:
                return False
            self.tello.takeoff()
            return True
        except Exception as e:
            self.logger.error(f"Takeoff error: {e}")
            return False
    
    def land(self) -> bool:
        """Land."""
        try:
            if not self.is_connected:
                return False
            self.tello.land()
            return True
        except Exception as e:
            self.logger.error(f"Land error: {e}")
            return False
    
    def move_forward(self, distance: int) -> bool:
        """Move forward by distance (cm)."""
        try:
            if not self.is_connected:
                return False
            self.tello.move_forward(distance)
            return True
        except Exception as e:
            self.logger.error(f"Move forward error: {e}")
            return False
    
    def move_back(self, distance: int) -> bool:
        """Move back by distance (cm)."""
        try:
            if not self.is_connected:
                return False
            self.tello.move_back(distance)
            return True
        except Exception as e:
            self.logger.error(f"Move back error: {e}")
            return False
    
    def move_left(self, distance: int) -> bool:
        """Move left by distance (cm)."""
        try:
            if not self.is_connected:
                return False
            self.tello.move_left(distance)
            return True
        except Exception as e:
            self.logger.error(f"Move left error: {e}")
            return False
    
    def move_right(self, distance: int) -> bool:
        """Move right by distance (cm)."""
        try:
            if not self.is_connected:
                return False
            self.tello.move_right(distance)
            return True
        except Exception as e:
            self.logger.error(f"Move right error: {e}")
            return False
    
    def move_up(self, distance: int) -> bool:
        """Move up by distance (cm)."""
        try:
            if not self.is_connected:
                return False
            self.tello.move_up(distance)
            return True
        except Exception as e:
            self.logger.error(f"Move up error: {e}")
            return False
    
    def move_down(self, distance: int) -> bool:
        """Move down by distance (cm)."""
        try:
            if not self.is_connected:
                return False
            self.tello.move_down(distance)
            return True
        except Exception as e:
            self.logger.error(f"Move down error: {e}")
            return False
    
    def rotate_clockwise(self, angle: int) -> bool:
        """Rotate clockwise by angle (degrees)."""
        try:
            if not self.is_connected:
                return False
            self.tello.rotate_clockwise(angle)
            return True
        except Exception as e:
            self.logger.error(f"Rotate clockwise error: {e}")
            return False
    
    def rotate_counter_clockwise(self, angle: int) -> bool:
        """Rotate counter-clockwise by angle (degrees)."""
        try:
            if not self.is_connected:
                return False
            self.tello.rotate_counter_clockwise(angle)
            return True
        except Exception as e:
            self.logger.error(f"Rotate counter-clockwise error: {e}")
            return False
    
    # Status commands
    def get_temperature(self) -> int:
        """Get drone temperature."""
        try:
            if not self.is_connected:
                return 0
            return self.tello.get_temperature()
        except Exception as e:
            self.logger.error(f"Error getting temperature: {e}")
            return 0
    
    def get_height(self) -> int:
        """Get current height (cm)."""
        try:
            if not self.is_connected:
                return 0
            return self.tello.get_height()
        except Exception as e:
            self.logger.error(f"Error getting height: {e}")
            return 0
    
    def get_speed_x(self) -> float:
        """Get X speed."""
        try:
            if not self.is_connected:
                return 0.0
            return float(self.tello.get_speed_x())
        except Exception as e:
            self.logger.error(f"Error getting speed X: {e}")
            return 0.0
    
    def get_speed_y(self) -> float:
        """Get Y speed."""
        try:
            if not self.is_connected:
                return 0.0
            return float(self.tello.get_speed_y())
        except Exception as e:
            self.logger.error(f"Error getting speed Y: {e}")
            return 0.0
    
    def get_speed_z(self) -> float:
        """Get Z speed."""
        try:
            if not self.is_connected:
                return 0.0
            return float(self.tello.get_speed_z())
        except Exception as e:
            self.logger.error(f"Error getting speed Z: {e}")
            return 0.0
    
    def emergency(self) -> bool:
        """Emergency stop."""
        try:
            if not self.is_connected:
                return False
            self.tello.emergency()
            return True
        except Exception as e:
            self.logger.error(f"Emergency error: {e}")
            return False
