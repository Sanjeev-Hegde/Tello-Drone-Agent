"""
Azure OpenAI Control Agent.
Converts natural language commands to drone control JSON using Azure OpenAI.
"""

import json
import logging
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

from config.settings import settings, config_manager


class ControlAgent:
    """
    Azure OpenAI-powered control agent for natural language drone commands.
    
    This agent converts natural language instructions into structured JSON
    commands that can be executed by the drone controller.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._setup_azure_openai()
        
        # Define the command schema for the drone
        self.command_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["takeoff", "land", "move", "rotate", "hover", "scan", "emergency"]
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["forward", "back", "left", "right", "up", "down"]},
                        "distance": {"type": "number", "minimum": 0, "maximum": 500},
                        "angle": {"type": "number", "minimum": -360, "maximum": 360},
                        "duration": {"type": "number", "minimum": 0, "maximum": 30},
                        "speed": {"type": "number", "minimum": 10, "maximum": 100}
                    }
                },
                "description": {"type": "string"},
                "safety_check": {"type": "boolean"}
            },
            "required": ["action", "description", "safety_check"]
        }
    
    def _setup_azure_openai(self):
        """Setup Azure OpenAI client with secure authentication."""
        try:
            # Get API key securely from Key Vault or environment
            api_key = config_manager.get_azure_openai_key()
            
            if not api_key:
                raise ValueError("Azure OpenAI API key not found in Key Vault or environment")
            
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            
            self.logger.info("Azure OpenAI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def process_command(self, natural_language_input: str) -> Dict[str, Any]:
        """
        Process natural language input and convert to drone command JSON.
        
        Args:
            natural_language_input: User's natural language command
            
        Returns:
            Structured JSON command for drone execution
            
        Raises:
            Exception: If command processing fails
        """
        try:
            system_prompt = self._get_system_prompt()
            
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": natural_language_input}
                ],
                temperature=0.1,  # Low temperature for consistent outputs
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            command_json = json.loads(response.choices[0].message.content)
            
            # Validate the command structure
            if not self._validate_command(command_json):
                raise ValueError("Generated command does not match expected schema")
            
            self.logger.info(f"Successfully processed command: {natural_language_input}")
            self.logger.debug(f"Generated command: {command_json}")
            
            return command_json
            
        except Exception as e:
            self.logger.error(f"Failed to process command '{natural_language_input}': {e}")
            return self._get_error_command(str(e))
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Azure OpenAI model."""
        return f"""You are a drone control agent that converts natural language commands into JSON commands for a Tello drone.

IMPORTANT: You must ALWAYS respond with valid JSON that matches this exact schema:

{json.dumps(self.command_schema, indent=2)}

Guidelines:
1. Safety first - set safety_check to false only for emergency commands
2. Reasonable defaults: speed=50, distance=100cm for movements
3. For scan/search commands, use "scan" action with hover parameters
4. For navigation commands, use "move" action with direction and distance
5. Emergency stop always uses "emergency" action
6. Rotate commands use "rotate" action with angle parameter

Examples:
- "take off" → {{"action": "takeoff", "description": "Taking off", "safety_check": true}}
- "fly forward 2 meters" → {{"action": "move", "parameters": {{"direction": "forward", "distance": 200}}, "description": "Moving forward 2 meters", "safety_check": true}}
- "turn right 90 degrees" → {{"action": "rotate", "parameters": {{"angle": 90}}, "description": "Rotating right 90 degrees", "safety_check": true}}
- "scan the room" → {{"action": "scan", "parameters": {{"duration": 10}}, "description": "Scanning room for objects", "safety_check": true}}

Convert the user's command to valid JSON following these guidelines."""
    
    def _validate_command(self, command: Dict[str, Any]) -> bool:
        """
        Validate command structure against schema.
        
        Args:
            command: Command dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic structure validation
            if not isinstance(command, dict):
                return False
            
            required_fields = ["action", "description", "safety_check"]
            if not all(field in command for field in required_fields):
                return False
            
            # Validate action
            valid_actions = ["takeoff", "land", "move", "rotate", "hover", "scan", "emergency"]
            if command["action"] not in valid_actions:
                return False
            
            # Validate safety_check
            if not isinstance(command["safety_check"], bool):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Command validation error: {e}")
            return False
    
    def _get_error_command(self, error_message: str) -> Dict[str, Any]:
        """
        Generate error command when processing fails.
        
        Args:
            error_message: Error description
            
        Returns:
            Error command structure
        """
        return {
            "action": "emergency",
            "description": f"Command processing failed: {error_message}",
            "safety_check": False,
            "error": True
        }
    
    async def process_audio_command(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process audio input and convert to drone command.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Structured JSON command for drone execution
        """
        try:
            # Use Azure Speech Service to convert audio to text
            # This is a placeholder - implement speech-to-text integration
            text_command = await self._speech_to_text(audio_data)
            return self.process_command(text_command)
            
        except Exception as e:
            self.logger.error(f"Failed to process audio command: {e}")
            return self._get_error_command(f"Audio processing failed: {e}")
    
    async def _speech_to_text(self, audio_data: bytes) -> str:
        """
        Convert audio to text using Azure Speech Service.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Transcribed text
        """
        # Placeholder for Azure Speech Service integration
        # In a real implementation, use Azure Cognitive Services Speech SDK
        self.logger.info("Audio to text conversion (placeholder)")
        return "take off"  # Placeholder return
