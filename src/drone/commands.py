"""
Drone command definitions and validation.
"""

from typing import Dict, Any, List
from enum import Enum


class DroneAction(Enum):
    """Available drone actions."""
    TAKEOFF = "takeoff"
    LAND = "land"
    MOVE = "move"
    ROTATE = "rotate"
    HOVER = "hover"
    SCAN = "scan"
    EMERGENCY = "emergency"


class DroneCommand:
    """
    Represents a validated drone command.
    """
    
    def __init__(self, action: DroneAction, parameters: Dict[str, Any] = None, 
                 description: str = "", safety_check: bool = True):
        self.action = action
        self.parameters = parameters or {}
        self.description = description
        self.safety_check = safety_check
        self.validate()
    
    def validate(self):
        """Validate command parameters."""
        if self.action == DroneAction.MOVE:
            self._validate_move_command()
        elif self.action == DroneAction.ROTATE:
            self._validate_rotate_command()
        elif self.action == DroneAction.SCAN:
            self._validate_scan_command()
    
    def _validate_move_command(self):
        """Validate move command parameters."""
        direction = self.parameters.get("direction")
        distance = self.parameters.get("distance", 100)
        
        valid_directions = ["forward", "back", "left", "right", "up", "down"]
        if direction not in valid_directions:
            raise ValueError(f"Invalid direction: {direction}")
        
        if not (20 <= distance <= 500):
            raise ValueError(f"Distance must be between 20-500cm: {distance}")
        
        self.parameters["distance"] = int(distance)
    
    def _validate_rotate_command(self):
        """Validate rotate command parameters."""
        angle = self.parameters.get("angle", 90)
        
        if not (-360 <= angle <= 360):
            raise ValueError(f"Angle must be between -360 and 360 degrees: {angle}")
        
        self.parameters["angle"] = int(angle)
    
    def _validate_scan_command(self):
        """Validate scan command parameters."""
        duration = self.parameters.get("duration", 5)
        
        if not (1 <= duration <= 30):
            raise ValueError(f"Scan duration must be between 1-30 seconds: {duration}")
        
        self.parameters["duration"] = int(duration)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary."""
        return {
            "action": self.action.value,
            "parameters": self.parameters,
            "description": self.description,
            "safety_check": self.safety_check
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DroneCommand':
        """Create command from dictionary."""
        action = DroneAction(data["action"])
        return cls(
            action=action,
            parameters=data.get("parameters", {}),
            description=data.get("description", ""),
            safety_check=data.get("safety_check", True)
        )


class CommandValidator:
    """
    Validates and sanitizes drone commands for safety.
    """
    
    @staticmethod
    def validate_command_sequence(commands: List[DroneCommand]) -> List[str]:
        """
        Validate a sequence of commands for safety issues.
        
        Args:
            commands: List of drone commands
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for takeoff before movement
        has_takeoff = False
        for i, cmd in enumerate(commands):
            if cmd.action == DroneAction.TAKEOFF:
                has_takeoff = True
            elif cmd.action in [DroneAction.MOVE, DroneAction.ROTATE, DroneAction.SCAN]:
                if not has_takeoff:
                    warnings.append(f"Command {i+1}: Movement command without takeoff")
        
        # Check for excessive movements
        total_distance = 0
        for cmd in commands:
            if cmd.action == DroneAction.MOVE:
                total_distance += cmd.parameters.get("distance", 0)
        
        if total_distance > 1000:  # 10 meters
            warnings.append(f"Total movement distance ({total_distance}cm) exceeds safe limit")
        
        # Check for landing at end
        if commands and commands[-1].action != DroneAction.LAND:
            warnings.append("Command sequence should end with landing")
        
        return warnings
    
    @staticmethod
    def is_safe_command(command: DroneCommand) -> bool:
        """
        Check if a single command is safe to execute.
        
        Args:
            command: Drone command to check
            
        Returns:
            True if safe, False otherwise
        """
        if not command.safety_check and command.action != DroneAction.EMERGENCY:
            return False
        
        if command.action == DroneAction.MOVE:
            distance = command.parameters.get("distance", 0)
            if distance > 300:  # 3 meters max per command
                return False
        
        return True
