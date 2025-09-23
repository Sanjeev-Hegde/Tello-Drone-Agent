#!/usr/bin/env python3
"""
Drone Control Functions Module
Contains all drone movement and control functions for the realtime agent.
"""

import logging
from typing import Dict, Any


class DroneController:
    """Handles all drone movement and control operations."""
    
    def __init__(self, drone, drone_state, vision_only: bool = False):
        self.logger = logging.getLogger(f"{__name__}.DroneController")
        self.drone = drone
        self.drone_state = drone_state
        self.vision_only = vision_only
    
    async def takeoff(self, **kwargs) -> str:
        """Take off the drone."""
        self.logger.info("🚁 Taking off...")
        
        if self.drone_state.is_flying:
            return "Drone is already flying!"
        
        if self.vision_only:
            self.drone_state.is_flying = True
            self.drone_state.height = 80
            return "Takeoff successful - hovering at 80cm"
        
        try:
            success = self.drone.takeoff()
            if success:
                self.drone_state.is_flying = True
                self.drone_state.height = self.drone.get_height()
                self.drone_state.battery = self.drone.get_battery()
                return f"Takeoff successful - height: {self.drone_state.height}cm, battery: {self.drone_state.battery}%"
            else:
                return "Takeoff failed"
        except Exception as e:
            return f"Takeoff error: {str(e)}"
    
    async def land(self, **kwargs) -> str:
        """Land the drone."""
        self.logger.info("🛬 Landing...")
        
        if not self.drone_state.is_flying:
            return "Drone is already on the ground!"
        
        if self.vision_only:
            self.drone_state.is_flying = False
            self.drone_state.height = 0
            return "Landing successful"
        
        try:
            success = self.drone.land()
            if success:
                self.drone_state.is_flying = False
                self.drone_state.height = 0
                return "Landing successful"
            else:
                return "Landing failed"
        except Exception as e:
            return f"Landing error: {str(e)}"
    
    async def move_forward(self, distance: int, **kwargs) -> str:
        """Move drone forward."""
        self.logger.info(f"➡️ Moving forward {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Moved forward {distance}cm (Movement #{self.drone_state.movement_count})"
        
        try:
            success = self.drone.move_forward(distance)
            if success:
                self.drone_state.height = self.drone.get_height()
                self.drone_state.battery = self.drone.get_battery()
                return f"Moved forward {distance}cm - height: {self.drone_state.height}cm, battery: {self.drone_state.battery}%"
            else:
                return "Forward movement failed"
        except Exception as e:
            return f"Forward movement error: {str(e)}"
    
    async def move_backward(self, distance: int, **kwargs) -> str:
        """Move drone backward."""
        self.logger.info(f"⬅️ Moving backward {distance}cm...")
        
        if not self.drone_state.is_flying:
            return "Cannot move - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Moved backward {distance}cm"
        
        try:
            success = self.drone.move_back(distance)
            if success:
                return f"Moved backward {distance}cm"
            else:
                return "Backward movement failed"
        except Exception as e:
            return f"Backward movement error: {str(e)}"
    
    async def move_left(self, distance: int, **kwargs) -> str:
        """Move drone left."""
        if not self.drone_state.is_flying:
            return "Cannot move - drone is not flying!"
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Moved left {distance}cm"
        
        try:
            success = self.drone.move_left(distance)
            return f"Moved left {distance}cm" if success else "Left movement failed"
        except Exception as e:
            return f"Left movement error: {str(e)}"
    
    async def move_right(self, distance: int, **kwargs) -> str:
        """Move drone right."""
        if not self.drone_state.is_flying:
            return "Cannot move - drone is not flying!"
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Moved right {distance}cm"
        
        try:
            success = self.drone.move_right(distance)
            return f"Moved right {distance}cm" if success else "Right movement failed"
        except Exception as e:
            return f"Right movement error: {str(e)}"
    
    async def move_up(self, distance: int, **kwargs) -> str:
        """Move drone up."""
        if not self.drone_state.is_flying:
            return "Cannot move - drone is not flying!"
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            self.drone_state.height += distance
            return f"Moved up {distance}cm - height: {self.drone_state.height}cm"
        
        try:
            success = self.drone.move_up(distance)
            if success:
                self.drone_state.height = self.drone.get_height()
                return f"Moved up {distance}cm - height: {self.drone_state.height}cm"
            else:
                return "Up movement failed"
        except Exception as e:
            return f"Up movement error: {str(e)}"
    
    async def move_down(self, distance: int, **kwargs) -> str:
        """Move drone down."""
        if not self.drone_state.is_flying:
            return "Cannot move - drone is not flying!"
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            self.drone_state.height = max(0, self.drone_state.height - distance)
            return f"Moved down {distance}cm - height: {self.drone_state.height}cm"
        
        try:
            success = self.drone.move_down(distance)
            if success:
                self.drone_state.height = self.drone.get_height()
                return f"Moved down {distance}cm - height: {self.drone_state.height}cm"
            else:
                return "Down movement failed"
        except Exception as e:
            return f"Down movement error: {str(e)}"
    
    async def rotate_clockwise(self, angle: int, **kwargs) -> str:
        """Rotate drone clockwise."""
        if not self.drone_state.is_flying:
            return "Cannot rotate - drone is not flying!"
        
        if self.vision_only:
            return f"Rotated clockwise {angle}°"
        
        try:
            success = self.drone.rotate_clockwise(angle)
            return f"Rotated clockwise {angle}°" if success else "Clockwise rotation failed"
        except Exception as e:
            return f"Clockwise rotation error: {str(e)}"
    
    async def rotate_counter_clockwise(self, angle: int, **kwargs) -> str:
        """Rotate drone counter-clockwise."""
        if not self.drone_state.is_flying:
            return "Cannot rotate - drone is not flying!"
        
        if self.vision_only:
            return f"Rotated counter-clockwise {angle}°"
        
        try:
            success = self.drone.rotate_counter_clockwise(angle)
            return f"Rotated counter-clockwise {angle}°" if success else "Counter-clockwise rotation failed"
        except Exception as e:
            return f"Counter-clockwise rotation error: {str(e)}"
    
    # Curve movement functions
    async def curve_xyz_speed(self, x1: int, y1: int, z1: int, x2: int, y2: int, z2: int, speed: int, **kwargs) -> str:
        """Fly in a curve via waypoint to destination."""
        self.logger.info(f"🌊 Curve movement: waypoint({x1},{y1},{z1}) → destination({x2},{y2},{z2}) at {speed}cm/s")
        
        if not self.drone_state.is_flying:
            return "Cannot perform curve movement - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Curve movement completed: waypoint({x1},{y1},{z1}) → destination({x2},{y2},{z2})"
        
        try:
            success = self.drone.curve_xyz_speed(x1, y1, z1, x2, y2, z2, speed)
            if success:
                self.drone_state.height = self.drone.get_height()
                self.drone_state.battery = self.drone.get_battery()
                return f"Curve movement completed - height: {self.drone_state.height}cm, battery: {self.drone_state.battery}%"
            else:
                return "Curve movement failed"
        except Exception as e:
            return f"Curve movement error: {str(e)}"
    
    async def curve_right_arc(self, radius: int, angle: int = 90, speed: int = 30, **kwargs) -> str:
        """Fly in a rightward arc."""
        self.logger.info(f"🌊➡️ Right arc: radius={radius}cm, angle={angle}°, speed={speed}cm/s")
        
        if not self.drone_state.is_flying:
            return "Cannot perform arc movement - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Right arc completed: {angle}° arc with {radius}cm radius"
        
        try:
            success = self.drone.curve_right_arc(radius, angle, speed)
            if success:
                return f"Right arc completed: {angle}° arc with {radius}cm radius"
            else:
                return "Right arc movement failed"
        except Exception as e:
            return f"Right arc movement error: {str(e)}"
    
    async def curve_left_arc(self, radius: int, angle: int = 90, speed: int = 30, **kwargs) -> str:
        """Fly in a leftward arc."""
        self.logger.info(f"🌊⬅️ Left arc: radius={radius}cm, angle={angle}°, speed={speed}cm/s")
        
        if not self.drone_state.is_flying:
            return "Cannot perform arc movement - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Left arc completed: {angle}° arc with {radius}cm radius"
        
        try:
            success = self.drone.curve_left_arc(radius, angle, speed)
            if success:
                return f"Left arc completed: {angle}° arc with {radius}cm radius"
            else:
                return "Left arc movement failed"
        except Exception as e:
            return f"Left arc movement error: {str(e)}"
    
    async def curve_forward_right(self, forward: int, right: int, speed: int = 30, **kwargs) -> str:
        """Fly in a smooth curve forward and right."""
        self.logger.info(f"🌊↗️ Forward-right curve: forward={forward}cm, right={right}cm, speed={speed}cm/s")
        
        if not self.drone_state.is_flying:
            return "Cannot perform curve movement - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Forward-right curve completed: {forward}cm forward, {right}cm right"
        
        try:
            success = self.drone.curve_forward_right(forward, right, speed)
            if success:
                return f"Forward-right curve completed: {forward}cm forward, {right}cm right"
            else:
                return "Forward-right curve failed"
        except Exception as e:
            return f"Forward-right curve error: {str(e)}"
    
    async def curve_forward_left(self, forward: int, left: int, speed: int = 30, **kwargs) -> str:
        """Fly in a smooth curve forward and left."""
        self.logger.info(f"🌊↖️ Forward-left curve: forward={forward}cm, left={left}cm, speed={speed}cm/s")
        
        if not self.drone_state.is_flying:
            return "Cannot perform curve movement - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Forward-left curve completed: {forward}cm forward, {left}cm left"
        
        try:
            success = self.drone.curve_forward_left(forward, left, speed)
            if success:
                return f"Forward-left curve completed: {forward}cm forward, {left}cm left"
            else:
                return "Forward-left curve failed"
        except Exception as e:
            return f"Forward-left curve error: {str(e)}"
    
    async def go_xyz_speed(self, x: int, y: int, z: int, speed: int, **kwargs) -> str:
        """Fly directly to XYZ coordinates with specified speed."""
        self.logger.info(f"🎯 Direct movement: ({x},{y},{z}) at {speed}cm/s")
        
        if not self.drone_state.is_flying:
            return "Cannot perform direct movement - drone is not flying! Use takeoff first."
        
        self.drone_state.movement_count += 1
        
        if self.vision_only:
            return f"Direct movement completed to ({x},{y},{z})"
        
        try:
            success = self.drone.go_xyz_speed(x, y, z, speed)
            if success:
                self.drone_state.height = self.drone.get_height()
                self.drone_state.battery = self.drone.get_battery()
                return f"Direct movement completed - height: {self.drone_state.height}cm, battery: {self.drone_state.battery}%"
            else:
                return "Direct movement failed"
        except Exception as e:
            return f"Direct movement error: {str(e)}"
    
    async def get_drone_status(self, **kwargs) -> str:
        """Get current drone status."""
        if not self.vision_only:
            try:
                self.drone_state.battery = self.drone.get_battery()
                self.drone_state.height = self.drone.get_height()
            except:
                pass  # Ignore errors for mock testing
        
        status = {
            "flying": self.drone_state.is_flying,
            "battery": self.drone_state.battery,
            "height": self.drone_state.height,
            "movements_made": self.drone_state.movement_count,
            "mode": "VISION_ONLY" if self.vision_only else "REAL_DRONE"
        }
        
        return f"Drone Status: Flying={status['flying']}, Battery={status['battery']}%, Height={status['height']}cm, Movements={status['movements_made']}"
    
    async def emergency_stop(self, **kwargs) -> str:
        """Emergency stop all drone movement."""
        self.logger.warning("🚨 EMERGENCY STOP!")
        
        if self.vision_only:
            return "EMERGENCY STOP executed (simulation mode)"
        
        try:
            success = self.drone.emergency()
            return "EMERGENCY STOP executed - drone should hover in place" if success else "Emergency stop failed"
        except Exception as e:
            return f"Emergency stop error: {str(e)}"
