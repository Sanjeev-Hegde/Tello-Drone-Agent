"""
Tello Drone Controller.
Interfaces with the Tello drone using the djitellopy SDK.
"""

import logging
import asyncio
import cv2
import numpy as np
from typing import Optional, Callable, Dict, Any
from djitellopy import Tello
import threading
import time

from .commands import DroneCommand, DroneAction, CommandValidator
from config.settings import settings
from drone.commands import DroneCommand, DroneAction
from vision.camera_manager import CameraManager


class TelloController:
    """
    Controller for DJI Tello drone using djitellopy SDK.
    
    This class provides a high-level interface for drone control,
    video streaming, and safety management.
    """
    
    def __init__(self, enable_video: bool = True):
        self.logger = logging.getLogger(__name__)
        self.tello = None
        self.is_connected = False
        self.is_flying = False
        self.enable_video = enable_video
        self.video_thread = None
        self.frame_callback: Optional[Callable[[np.ndarray], None]] = None
        self.current_frame: Optional[np.ndarray] = None
        self._stop_video = False
        
        # Battery and status monitoring
        self.battery_level = 0
        self.temperature = 0
        
        # Command validator
        self.validator = CommandValidator()
    
    async def connect(self) -> bool:
        """
        Connect to the Tello drone.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info("Attempting to connect to Tello drone...")
            
            self.tello = Tello()
            self.tello.connect()
            
            # Check connection
            battery = self.tello.get_battery()
            if battery > 0:
                self.is_connected = True
                self.battery_level = battery
                self.logger.info(f"Connected to Tello drone. Battery: {battery}%")
                
                # Start video stream if enabled
                if self.enable_video:
                    await self.start_video_stream()
                
                return True
            else:
                self.logger.error("Failed to get battery level - connection failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Tello drone: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the Tello drone."""
        try:
            if self.enable_video:
                await self.stop_video_stream()
            
            if self.is_flying:
                self.logger.warning("Drone is still flying - attempting emergency landing")
                await self.emergency_land()
            
            if self.tello:
                self.tello.end()
            
            self.is_connected = False
            self.logger.info("Disconnected from Tello drone")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    async def execute_command(self, command: DroneCommand) -> bool:
        """
        Execute a drone command.
        
        Args:
            command: DroneCommand to execute
            
        Returns:
            True if command executed successfully, False otherwise
        """
        if not self.is_connected:
            self.logger.error("Cannot execute command - drone not connected")
            return False
        
        # Safety check
        if not self.validator.is_safe_command(command):
            self.logger.warning(f"Command failed safety check: {command.description}")
            return False
        
        try:
            self.logger.info(f"Executing command: {command.description}")
            
            if command.action == DroneAction.TAKEOFF:
                return await self._takeoff()
            elif command.action == DroneAction.LAND:
                return await self._land()
            elif command.action == DroneAction.MOVE:
                return await self._move(command.parameters)
            elif command.action == DroneAction.ROTATE:
                return await self._rotate(command.parameters)
            elif command.action == DroneAction.HOVER:
                return await self._hover(command.parameters)
            elif command.action == DroneAction.SCAN:
                return await self._scan(command.parameters)
            elif command.action == DroneAction.EMERGENCY:
                return await self._emergency()
            else:
                self.logger.error(f"Unknown command action: {command.action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return False
    
    async def _takeoff(self) -> bool:
        """Execute takeoff command."""
        try:
            if self.is_flying:
                self.logger.warning("Drone is already flying")
                return True
            
            # Check battery level
            if self.battery_level < 20:
                self.logger.error(f"Battery too low for takeoff: {self.battery_level}%")
                return False
            
            self.tello.takeoff()
            self.is_flying = True
            self.logger.info("Takeoff successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Takeoff failed: {e}")
            return False
    
    async def _land(self) -> bool:
        """Execute land command."""
        try:
            if not self.is_flying:
                self.logger.warning("Drone is not flying")
                return True
            
            self.tello.land()
            self.is_flying = False
            self.logger.info("Landing successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Landing failed: {e}")
            return False
    
    async def _move(self, parameters: Dict[str, Any]) -> bool:
        """Execute move command."""
        try:
            direction = parameters["direction"]
            distance = parameters["distance"]
            
            if not self.is_flying:
                self.logger.error("Cannot move - drone is not flying")
                return False
            
            if direction == "forward":
                self.tello.move_forward(distance)
            elif direction == "back":
                self.tello.move_back(distance)
            elif direction == "left":
                self.tello.move_left(distance)
            elif direction == "right":
                self.tello.move_right(distance)
            elif direction == "up":
                self.tello.move_up(distance)
            elif direction == "down":
                self.tello.move_down(distance)
            
            self.logger.info(f"Moved {direction} {distance}cm")
            return True
            
        except Exception as e:
            self.logger.error(f"Move command failed: {e}")
            return False
    
    async def _rotate(self, parameters: Dict[str, Any]) -> bool:
        """Execute rotate command."""
        try:
            angle = parameters["angle"]
            
            if not self.is_flying:
                self.logger.error("Cannot rotate - drone is not flying")
                return False
            
            if angle > 0:
                self.tello.rotate_clockwise(angle)
            else:
                self.tello.rotate_counter_clockwise(abs(angle))
            
            self.logger.info(f"Rotated {angle} degrees")
            return True
            
        except Exception as e:
            self.logger.error(f"Rotate command failed: {e}")
            return False
    
    async def _hover(self, parameters: Dict[str, Any]) -> bool:
        """Execute hover command."""
        try:
            duration = parameters.get("duration", 3)
            
            if not self.is_flying:
                self.logger.error("Cannot hover - drone is not flying")
                return False
            
            # Hover by sending stop command and waiting
            await asyncio.sleep(duration)
            self.logger.info(f"Hovered for {duration} seconds")
            return True
            
        except Exception as e:
            self.logger.error(f"Hover command failed: {e}")
            return False
    
    async def _scan(self, parameters: Dict[str, Any]) -> bool:
        """Execute scan command - rotate slowly for vision analysis."""
        try:
            duration = parameters.get("duration", 10)
            
            if not self.is_flying:
                self.logger.error("Cannot scan - drone is not flying")
                return False
            
            # Perform 360-degree scan over the duration
            total_angle = 360
            steps = 8  # 45-degree increments
            angle_per_step = total_angle // steps
            sleep_time = duration / steps
            
            for i in range(steps):
                self.tello.rotate_clockwise(angle_per_step)
                await asyncio.sleep(sleep_time)
            
            self.logger.info(f"Scan completed in {duration} seconds")
            return True
            
        except Exception as e:
            self.logger.error(f"Scan command failed: {e}")
            return False
    
    async def _emergency(self) -> bool:
        """Execute emergency command."""
        try:
            self.tello.emergency()
            self.is_flying = False
            self.logger.warning("Emergency stop executed")
            return True
            
        except Exception as e:
            self.logger.error(f"Emergency command failed: {e}")
            return False
    
    async def emergency_land(self):
        """Emergency landing procedure."""
        try:
            if self.is_flying:
                self.logger.warning("Performing emergency landing")
                self.tello.emergency()
                self.is_flying = False
        except Exception as e:
            self.logger.error(f"Emergency landing failed: {e}")
    
    async def start_video_stream(self):
        """Start video streaming from drone."""
        try:
            if not self.tello:
                self.logger.error("Cannot start video - drone not connected")
                return
            
            self.tello.streamon()
            self._stop_video = False
            
            # Start video processing thread
            self.video_thread = threading.Thread(target=self._video_loop, daemon=True)
            self.video_thread.start()
            
            self.logger.info("Video stream started")
            
        except Exception as e:
            self.logger.error(f"Failed to start video stream: {e}")
    
    async def stop_video_stream(self):
        """Stop video streaming."""
        try:
            self._stop_video = True
            
            if self.video_thread and self.video_thread.is_alive():
                self.video_thread.join(timeout=5)
            
            if self.tello:
                self.tello.streamoff()
            
            self.logger.info("Video stream stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop video stream: {e}")
    
    def _video_loop(self):
        """Video processing loop (runs in separate thread)."""
        while not self._stop_video:
            try:
                frame = self.tello.get_frame_read().frame
                if frame is not None:
                    self.current_frame = frame
                    
                    # Call frame callback if set
                    if self.frame_callback:
                        self.frame_callback(frame)
                
                time.sleep(1/30)  # 30 FPS
                
            except Exception as e:
                self.logger.error(f"Video loop error: {e}")
                break
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Set callback function for video frames."""
        self.frame_callback = callback
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current video frame."""
        return self.current_frame
    
    def get_status(self) -> Dict[str, Any]:
        """Get current drone status."""
        status = {
            "connected": self.is_connected,
            "flying": self.is_flying,
            "battery": self.battery_level,
            "temperature": self.temperature
        }
        
        if self.tello and self.is_connected:
            try:
                status["battery"] = self.tello.get_battery()
                status["temperature"] = self.tello.get_temperature()
                status["height"] = self.tello.get_height()
                status["speed"] = self.tello.get_speed_x(), self.tello.get_speed_y(), self.tello.get_speed_z()
            except Exception as e:
                self.logger.debug(f"Failed to get extended status: {e}")
        
        return status
