"""
Example usage of the Control Agent with simulated drone commands.

This example demonstrates how to use the Azure OpenAI-powered control agent
to convert natural language commands into structured drone commands.
"""

import asyncio
import sys
import os
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.control_agent import ControlAgent
from drone.commands import DroneCommand, CommandValidator


async def control_agent_demo():
    """
    Demonstrate the control agent functionality.
    """
    print("Starting Control Agent Demo...")
    
    try:
        # Initialize control agent
        control_agent = ControlAgent()
        validator = CommandValidator()
        
        print("Control agent initialized successfully")
        print("This demo will convert natural language to drone commands")
        print("Available command examples:")
        print("  - 'take off'")
        print("  - 'fly forward 2 meters'")
        print("  - 'turn right 90 degrees'")
        print("  - 'scan the room'")
        print("  - 'land'")
        print("  - 'quit' - Exit")
        
        command_history = []
        
        while True:
            try:
                # Get user input
                user_input = input("\nEnter drone command: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                # Process command
                print(f"Processing: {user_input}")
                command_json = control_agent.process_command(user_input)
                
                # Display results
                if command_json.get("error"):
                    print(f"Error: {command_json.get('description')}")
                else:
                    print(f"Generated command:")
                    print(json.dumps(command_json, indent=2))
                    
                    try:
                        # Validate command
                        drone_command = DroneCommand.from_dict(command_json)
                        print(f"✓ Command validation successful")
                        
                        # Add to history for sequence validation
                        command_history.append(drone_command)
                        
                        # Check command safety
                        if validator.is_safe_command(drone_command):
                            print(f"✓ Safety check passed")
                        else:
                            print(f"⚠ Safety check failed")
                        
                        # Check sequence if we have multiple commands
                        if len(command_history) > 1:
                            warnings = validator.validate_command_sequence(command_history)
                            if warnings:
                                print(f"Sequence warnings:")
                                for warning in warnings:
                                    print(f"  - {warning}")
                        
                    except Exception as e:
                        print(f"✗ Command validation failed: {e}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error processing command: {e}")
        
        print("Demo completed")
        
        # Show command history summary
        if command_history:
            print(f"\nCommand History Summary:")
            for i, cmd in enumerate(command_history, 1):
                print(f"{i}. {cmd.action.value}: {cmd.description}")
        
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    # Note: This example requires Azure OpenAI to be configured
    print("Control Agent Demo")
    print("Make sure to configure Azure OpenAI credentials in .env file")
    
    try:
        asyncio.run(control_agent_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted")
    except Exception as e:
        print(f"Demo error: {e}")
