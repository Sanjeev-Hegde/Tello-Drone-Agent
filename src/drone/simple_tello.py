"""
Simple Tello SDK wrapper using djitellopy for reliable drone operations.
This provides a clean interface while leveraging the mature djitellopy library.
"""

import logging
import cv2
import numpy as np
import threading
import time
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
        
        # Keepalive thread management
        self.keepalive_thread = None
        self.keepalive_stop_event = threading.Event()
        
    def connect(self) -> bool:
        """Connect to Tello drone."""
        try:
            self.logger.info("Connecting to Tello...")
            self.tello.connect()
            self.is_connected = True
            
            # Start keepalive thread
            self._start_keepalive_thread()
            
            self.logger.info("✅ Tello connected successfully!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Tello connection error: {e}")
            self.is_connected = False
            return False
    
    def close(self):
        """Close connection to Tello."""
        try:
            # Stop keepalive thread first
            self._stop_keepalive_thread()
            
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
    
    # Curve movement commands
    def curve_xyz_speed(self, x1: int, y1: int, z1: int, x2: int, y2: int, z2: int, speed: int) -> bool:
        """Fly to x2 y2 z2 in a curve via x1 y1 z1. Speed defines the traveling speed in cm/s.
        
        Both points are relative to the current position.
        The current position and both points must form a circle arc.
        If the arc radius is not within the range of 0.5-10 meters, it raises an Exception.
        x1/x2, y1/y2, z1/z2 can't both be between -20-20 at the same time, but can both be 0.
        
        Args:
            x1: -500 to 500 (cm) - First waypoint X
            y1: -500 to 500 (cm) - First waypoint Y  
            z1: -500 to 500 (cm) - First waypoint Z
            x2: -500 to 500 (cm) - Final destination X
            y2: -500 to 500 (cm) - Final destination Y
            z2: -500 to 500 (cm) - Final destination Z
            speed: 10-60 (cm/s) - Travel speed
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_connected:
                return False
            self.tello.curve_xyz_speed(x1, y1, z1, x2, y2, z2, speed)
            return True
        except Exception as e:
            self.logger.error(f"Curve movement error: {e}")
            return False
    
    def curve_right_arc(self, radius: int, angle: int = 90, speed: int = 30) -> bool:
        """Fly in a rightward curve arc.
        
        Args:
            radius: Arc radius in cm (50-500)
            angle: Arc angle in degrees (45-180), default 90°
            speed: Travel speed in cm/s (10-60), default 30
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate curve points for a right arc
            import math
            angle_rad = math.radians(angle)
            
            # Waypoint (middle of arc)
            x1 = int(radius * math.sin(angle_rad / 2))
            y1 = int(radius * (1 - math.cos(angle_rad / 2)))
            z1 = 0
            
            # Final point (end of arc)
            x2 = int(radius * math.sin(angle_rad))
            y2 = int(radius * (1 - math.cos(angle_rad)))
            z2 = 0
            
            return self.curve_xyz_speed(x1, y1, z1, x2, y2, z2, speed)
        except Exception as e:
            self.logger.error(f"Right arc curve error: {e}")
            return False
    
    def curve_left_arc(self, radius: int, angle: int = 90, speed: int = 30) -> bool:
        """Fly in a leftward curve arc.
        
        Args:
            radius: Arc radius in cm (50-500)
            angle: Arc angle in degrees (45-180), default 90°
            speed: Travel speed in cm/s (10-60), default 30
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate curve points for a left arc (mirror of right arc)
            import math
            angle_rad = math.radians(angle)
            
            # Waypoint (middle of arc)
            x1 = int(-radius * math.sin(angle_rad / 2))
            y1 = int(radius * (1 - math.cos(angle_rad / 2)))
            z1 = 0
            
            # Final point (end of arc)
            x2 = int(-radius * math.sin(angle_rad))
            y2 = int(radius * (1 - math.cos(angle_rad)))
            z2 = 0
            
            return self.curve_xyz_speed(x1, y1, z1, x2, y2, z2, speed)
        except Exception as e:
            self.logger.error(f"Left arc curve error: {e}")
            return False
    
    def curve_forward_right(self, forward: int, right: int, speed: int = 30) -> bool:
        """Fly in a smooth curve forward and to the right.
        
        Args:
            forward: Forward distance in cm (50-400)
            right: Right distance in cm (50-400)
            speed: Travel speed in cm/s (10-60), default 30
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Simple curve: waypoint at 1/3, final at full distance
            x1 = right // 3
            y1 = forward // 3
            z1 = 0
            
            x2 = right
            y2 = forward
            z2 = 0
            
            return self.curve_xyz_speed(x1, y1, z1, x2, y2, z2, speed)
        except Exception as e:
            self.logger.error(f"Forward-right curve error: {e}")
            return False
    
    def curve_forward_left(self, forward: int, left: int, speed: int = 30) -> bool:
        """Fly in a smooth curve forward and to the left.
        
        Args:
            forward: Forward distance in cm (50-400)
            left: Left distance in cm (50-400)
            speed: Travel speed in cm/s (10-60), default 30
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Simple curve: waypoint at 1/3, final at full distance
            x1 = -left // 3  # Negative for left
            y1 = forward // 3
            z1 = 0
            
            x2 = -left  # Negative for left
            y2 = forward
            z2 = 0
            
            return self.curve_xyz_speed(x1, y1, z1, x2, y2, z2, speed)
        except Exception as e:
            self.logger.error(f"Forward-left curve error: {e}")
            return False
    
    # Advanced movement commands
    def go_xyz_speed(self, x: int, y: int, z: int, speed: int) -> bool:
        """Fly to x y z relative to the current position with specified speed.
        
        Args:
            x: -500 to 500 (cm) - X displacement
            y: -500 to 500 (cm) - Y displacement  
            z: -500 to 500 (cm) - Z displacement
            speed: 10-100 (cm/s) - Travel speed
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_connected:
                return False
            self.tello.go_xyz_speed(x, y, z, speed)
            return True
        except Exception as e:
            self.logger.error(f"Go XYZ error: {e}")
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
    
    def _start_keepalive_thread(self):
        """Start the keepalive thread to send periodic keepalive commands."""
        try:
            if self.keepalive_thread is not None and self.keepalive_thread.is_alive():
                return  # Thread already running
            
            self.keepalive_stop_event.clear()
            self.keepalive_thread = threading.Thread(target=self._keepalive_worker, daemon=True)
            self.keepalive_thread.start()
        except Exception as e:
            self.logger.error(f"❌ Error starting keepalive thread: {e}")
    
    def _stop_keepalive_thread(self):
        """Stop the keepalive thread."""
        try:
            if self.keepalive_thread is not None:
                self.keepalive_stop_event.set()
                self.keepalive_thread.join(timeout=1.0)  # Wait up to 1 second
                self.keepalive_thread = None
        except Exception as e:
            self.logger.error(f"❌ Error stopping keepalive thread: {e}")
    
    def _keepalive_worker(self):
        """Worker function for the keepalive thread."""
        
        while not self.keepalive_stop_event.is_set():
            try:
                if self.is_connected:
                    self.logger.info(f"Current Battery Percentage:{self.tello.send_command_with_return('battery?')}%")
                else:
                    break  # Connection lost, exit thread
            except Exception as e:
                self.logger.warning(f"⚠️ Keepalive error: {e}")
                # Continue trying even if there's an error
            
            # Wait 10 seconds or until stop event is set
            if self.keepalive_stop_event.wait(timeout=12.0):
                break  # Stop event was set
