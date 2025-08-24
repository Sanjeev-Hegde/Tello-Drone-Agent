"""
Basic tests for the Tello Drone AI Agent components.
"""

import unittest
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from drone.commands import DroneCommand, DroneAction, CommandValidator


class TestDroneCommands(unittest.TestCase):
    """Test drone command functionality."""
    
    def test_takeoff_command(self):
        """Test takeoff command creation."""
        cmd = DroneCommand(DroneAction.TAKEOFF, description="Taking off")
        self.assertEqual(cmd.action, DroneAction.TAKEOFF)
        self.assertTrue(cmd.safety_check)
        self.assertEqual(cmd.description, "Taking off")
    
    def test_move_command_validation(self):
        """Test move command parameter validation."""
        # Valid move command
        cmd = DroneCommand(
            DroneAction.MOVE,
            parameters={"direction": "forward", "distance": 100},
            description="Move forward"
        )
        self.assertEqual(cmd.parameters["direction"], "forward")
        self.assertEqual(cmd.parameters["distance"], 100)
        
        # Invalid direction should raise error
        with self.assertRaises(ValueError):
            DroneCommand(
                DroneAction.MOVE,
                parameters={"direction": "invalid", "distance": 100}
            )
        
        # Invalid distance should raise error
        with self.assertRaises(ValueError):
            DroneCommand(
                DroneAction.MOVE,
                parameters={"direction": "forward", "distance": 1000}
            )
    
    def test_rotate_command_validation(self):
        """Test rotate command parameter validation."""
        # Valid rotate command
        cmd = DroneCommand(
            DroneAction.ROTATE,
            parameters={"angle": 90},
            description="Rotate right"
        )
        self.assertEqual(cmd.parameters["angle"], 90)
        
        # Invalid angle should raise error
        with self.assertRaises(ValueError):
            DroneCommand(
                DroneAction.ROTATE,
                parameters={"angle": 400}
            )
    
    def test_command_serialization(self):
        """Test command to/from dictionary conversion."""
        original_cmd = DroneCommand(
            DroneAction.MOVE,
            parameters={"direction": "forward", "distance": 200},
            description="Move forward 2m",
            safety_check=True
        )
        
        # Convert to dict and back
        cmd_dict = original_cmd.to_dict()
        restored_cmd = DroneCommand.from_dict(cmd_dict)
        
        self.assertEqual(original_cmd.action, restored_cmd.action)
        self.assertEqual(original_cmd.parameters, restored_cmd.parameters)
        self.assertEqual(original_cmd.description, restored_cmd.description)
        self.assertEqual(original_cmd.safety_check, restored_cmd.safety_check)


class TestCommandValidator(unittest.TestCase):
    """Test command validation functionality."""
    
    def setUp(self):
        self.validator = CommandValidator()
    
    def test_safe_command_validation(self):
        """Test individual command safety validation."""
        # Safe takeoff command
        safe_cmd = DroneCommand(DroneAction.TAKEOFF, safety_check=True)
        self.assertTrue(self.validator.is_safe_command(safe_cmd))
        
        # Unsafe command (no safety check for non-emergency)
        unsafe_cmd = DroneCommand(DroneAction.MOVE, safety_check=False)
        self.assertFalse(self.validator.is_safe_command(unsafe_cmd))
        
        # Emergency command (allowed without safety check)
        emergency_cmd = DroneCommand(DroneAction.EMERGENCY, safety_check=False)
        self.assertTrue(self.validator.is_safe_command(emergency_cmd))
    
    def test_command_sequence_validation(self):
        """Test command sequence validation."""
        # Valid sequence: takeoff -> move -> land
        commands = [
            DroneCommand(DroneAction.TAKEOFF),
            DroneCommand(DroneAction.MOVE, parameters={"direction": "forward", "distance": 100}),
            DroneCommand(DroneAction.LAND)
        ]
        
        warnings = self.validator.validate_command_sequence(commands)
        # Should have no warnings for this valid sequence
        self.assertEqual(len(warnings), 0)
        
        # Invalid sequence: move without takeoff
        invalid_commands = [
            DroneCommand(DroneAction.MOVE, parameters={"direction": "forward", "distance": 100}),
            DroneCommand(DroneAction.LAND)
        ]
        
        warnings = self.validator.validate_command_sequence(invalid_commands)
        # Should have warning about movement without takeoff
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any("without takeoff" in warning for warning in warnings))


if __name__ == "__main__":
    # Run the tests
    print("Running Tello Drone AI Agent Tests...")
    unittest.main(verbosity=2)
