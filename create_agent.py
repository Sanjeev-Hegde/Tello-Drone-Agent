#!/usr/bin/env python3
"""
Simple script to manually create a new Azure AI agent and save IDs to .env
"""
import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import agent
import importlib.util
spec = importlib.util.spec_from_file_location(
    "autonomous_drone_agent", 
    os.path.join(os.path.dirname(__file__), 'src', 'agents', 'autonomous_drone_agent.py')
)
autonomous_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(autonomous_module)

# Set up logging
logging.basicConfig(level=logging.INFO)

def create_agent():
    """Create a new agent and display the IDs."""
    print("🤖 Creating new Azure AI agent...")
    
    try:
        # Create agent
        agent = autonomous_module.AutonomousDroneAgent(vision_only=True)
        
        # Get context
        context = agent.get_conversation_context()
        agent_id = context['agent_id']
        thread_id = context['thread_id']
        
        print(f"\n✅ Agent created successfully!")
        print(f"🤖 Agent ID: {agent_id}")
        
        print(f"\n📝 Add this to your .env file:")
        print(f"DRONE_AGENT_ID={agent_id}")
        
        # Check if .env exists
        env_file = ".env"
        if os.path.exists(env_file):
            print(f"\n💡 Found existing .env file")
            choice = input("Do you want to append this value? (y/n): ").strip().lower()
            if choice == 'y':
                with open(env_file, 'a') as f:
                    f.write(f"\n# Agent ID (created {os.path.basename(__file__)})\n")
                    f.write(f"DRONE_AGENT_ID={agent_id}\n")
                print("✅ Agent ID added to .env file!")
        else:
            choice = input("Create .env file with this value? (y/n): ").strip().lower()
            if choice == 'y':
                with open(env_file, 'w') as f:
                    f.write(f"# Agent ID (created {os.path.basename(__file__)})\n")
                    f.write(f"DRONE_AGENT_ID={agent_id}\n")
                print("✅ .env file created!")
        
        print(f"\n✅ Agent created and ready for reuse!")
        print(f"🤖 Agent ID: {agent_id}")
        print("💡 The agent will be automatically reused in future sessions")
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")

if __name__ == "__main__":
    create_agent()
