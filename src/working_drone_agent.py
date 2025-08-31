"""Working Azure AI Projects Agent Implementation"""
import logging
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DronePosition:
    """Track drone position and orientation."""
    x: float = 0.0
    y: float = 0.0 
    z: float = 0.0
    heading: float = 0.0  # degrees
    is_flying: bool = False


class WorkingDroneAgent:
    """Simple working Azure AI Projects agent for drone control."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.position = DronePosition()
        self.conversation_count = 0
        
        # Initialize Azure AI client
        self._setup_ai_client()
        self._create_agent()
        
    def _setup_ai_client(self):
        """Initialize Azure AI Projects client."""
        try:
            self.logger.info("Setting up Azure AI Projects client...")
            
            credential = DefaultAzureCredential()
            
            self.ai_client = AIProjectClient(
                endpoint=settings.azure_ai_project_endpoint,
                credential=credential
            )
            
            self.logger.info("Azure AI Projects client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI client: {e}")
            raise
    
    def _create_agent(self):
        """Create the drone control agent."""
        try:
            # Simple agent without complex tools for now
            self.agent = self.ai_client.agents.create_agent(
                model="gpt-4o",  # Using gpt-4o which is deployed
                name="Simple Drone Controller",
                instructions="""You are a helpful drone control assistant. 
                
                You help users understand drone operations and provide guidance on:
                - Basic flight commands (takeoff, land, hover)
                - Safety considerations 
                - Simple movements (forward, backward, up, down, rotate)
                
                Always prioritize safety and provide clear, step-by-step guidance.
                Keep responses concise and helpful."""
            )
            
            # Create conversation thread
            self.thread = self.ai_client.agents.threads.create()
            
            self.logger.info("Drone agent and thread created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}")
            raise
    
    def process_message(self, user_input: str) -> str:
        """Process user input and return agent response."""
        try:
            # Add user message to thread
            self.ai_client.agents.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_input
            )
            
            # Create and execute run
            run = self.ai_client.agents.runs.create(
                thread_id=self.thread.id,
                body={"assistant_id": self.agent.id}
            )
            
            # Wait for completion
            max_attempts = 30
            attempts = 0
            while run.status in ["queued", "in_progress"] and attempts < max_attempts:
                time.sleep(1)
                run = self.ai_client.agents.runs.get(
                    thread_id=self.thread.id, 
                    run_id=run.id
                )
                attempts += 1
            
            if run.status == "failed":
                self.logger.error(f"Run failed: {run}")
                return "I'm sorry, I encountered an error processing your request. Please try again."
            
            if attempts >= max_attempts:
                self.logger.error("Run timed out")
                return "I'm taking longer than expected to process your request. Please try again."
            
            # Get messages and find assistant response
            messages = self.ai_client.agents.messages.list(thread_id=self.thread.id)
            message_list = list(messages)
            
            # Find the latest assistant message
            for message in message_list:
                if message.role == "assistant" and message.content:
                    for content_item in message.content:
                        if hasattr(content_item, 'text') and hasattr(content_item.text, 'value'):
                            self.conversation_count += 1
                            return content_item.text.value
            
            return "I understand your request. How can I help you with the drone?"
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"Error: {str(e)}"
    
    def get_context(self) -> Dict[str, Any]:
        """Get current conversation context."""
        return {
            "current_position": asdict(self.position),
            "conversation_count": self.conversation_count,
            "agent_id": self.agent.id if self.agent else None,
            "thread_id": self.thread.id if self.thread else None
        }
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.thread:
                self.ai_client.agents.threads.delete(self.thread.id)
                self.logger.info("Thread deleted")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def test_working_agent():
    """Test the working agent implementation."""
    try:
        logger.info("🚁 Testing Working Azure AI Projects Drone Agent")
        
        # Create agent
        agent = WorkingDroneAgent()
        logger.info("✅ Agent created successfully")
        
        # Test conversations
        test_messages = [
            "Hello! Can you help me control my drone?",
            "What safety checks should I perform before takeoff?",
            "How do I make the drone hover at 2 meters height?",
            "What should I do if I lose control of the drone?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            logger.info(f"\n🧠 Test {i}: '{message}'")
            response = agent.process_message(message)
            logger.info(f"🤖 Agent Response: {response}")
            
            # Show context
            context = agent.get_context()
            logger.info(f"📊 Context: {context}")
        
        logger.info("\n✅ All tests completed successfully!")
        
        # Cleanup
        agent.cleanup()
        logger.info("🧹 Cleanup completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_working_agent()
