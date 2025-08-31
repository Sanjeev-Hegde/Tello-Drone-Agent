#!/usr/bin/env python3
"""
Quick Interactive Demo for Autonomous Drone Agent
Shorter version with just 3 key commands to demonstrate functionality.
"""

import sys
import os
import asyncio
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Direct import to avoid package issues
import importlib.util
spec = importlib.util.spec_from_file_location(
    "autonomous_drone_agent", 
    os.path.join(os.path.dirname(__file__), 'src', 'agents', 'autonomous_drone_agent.py')
)
autonomous_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(autonomous_module)

# Set up clean logging - suppress Azure noise
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enable only our agent logs
logging.getLogger('autonomous_drone_agent').setLevel(logging.INFO)
logging.getLogger('__main__').setLevel(logging.INFO)

# Suppress noisy Azure logs
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure.ai.agents').setLevel(logging.WARNING)

async def quick_interactive_demo():
    """Run a short interactive demo with just 3 key commands."""
    
    try:
        print("🚁" + "="*50)
        print("🚁  QUICK INTERACTIVE DEMO")
        print("🚁  3 Key Commands Demo")
        print("🚁" + "="*50)
        
        # Create agent (will reuse if DRONE_AGENT_ID is set)
        print("\n📡 Creating agent...")
        agent = autonomous_module.AutonomousDroneAgent(vision_only=True)
        print("✅ Agent ready!")
        
        # Show if we're reusing an agent
        agent_id = os.getenv('DRONE_AGENT_ID')
        if agent_id and agent.agent.id == agent_id:
            print(f"♻️  Reusing agent: {agent_id[:8]}...")
        else:
            print(f"🆕 New agent: {agent.agent.id[:8]}...")
        
        # Just 3 essential commands
        commands = [
            "Take off and check your status",
            "Capture an image and analyze what you see",
            "Land safely"
        ]
        
        for i, command in enumerate(commands, 1):
            print(f"\n📝 Command {i}/3: '{command}'")
            print("🔄 Processing...", end="", flush=True)
            
            try:
                response = await agent.process_user_command(command)
                print("\r🤖 Response:")
                print(f"   {response}")
                
                # Show status
                context = agent.get_conversation_context()
                state = context['drone_state']
                print(f"📊 Status: Flying={state['is_flying']}, Movements={state['movement_count']}")
                
            except Exception as e:
                print(f"\r❌ Error: {e}")
            
            print("─" * 40)
        
        print("\n🎉 Quick demo completed!")
        print("⏱️  Total time: ~30-60 seconds")
        print(f"💾 Agent ID for reuse: {agent.agent.id}")
        
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        
    finally:
        # Note: We DON'T cleanup the agent - it will be reused next time!
        print("\n💡 Agent preserved for next session!")
        print("🔄 Drone state will reset fresh on next restart")

def main():
    """Main entry point."""
    print("🚀 Choose Demo:")
    print("1. ⚡ Quick Interactive (3 commands, ~1 min)")
    print("2. 🎬 Full Interactive (13 commands, ~5 min)")
    print("3. 🔧 Quick Test (no commands, ~10 sec)")
    print("4. 🗑️  Force New Agent (cleanup + create new)")
    print("5. 📊 Agent Status")
    print("6. ❌ Exit")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        try:
            asyncio.run(quick_interactive_demo())
        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted")
    elif choice == "2":
        print("🔄 Running full demo...")
        os.system("venv\\Scripts\\python.exe demo_enhanced.py")
    elif choice == "3":
        print("🔄 Running quick test...")
        os.system("echo 1 | venv\\Scripts\\python.exe demo_enhanced.py")
    elif choice == "4":
        print("🗑️  Simplified agent management...")
        try:
            # Show current agent status
            agent_id = os.getenv('DRONE_AGENT_ID')
            if agent_id:
                print(f"📍 Current agent ID: {agent_id}")
                print("� To create a new agent:")
                print("   1. Remove DRONE_AGENT_ID from .env file")
                print("   2. Or run: python create_agent.py")
            else:
                print("✅ No agent ID set - next run will create new agent")
        except Exception as e:
            print(f"❌ Error: {e}")
    elif choice == "5":
        print("\n📊 Agent Status:")
        agent_id = os.getenv('DRONE_AGENT_ID')
        print(f"   DRONE_AGENT_ID: {'✅ Set' if agent_id else '❌ Not set'}")
        if agent_id:
            print(f"   Agent ID: {agent_id}")
            print("   Status: ♻️  Will be reused on next run")
        else:
            print("   Status: 🆕 Will create new agent on next run")
    elif choice == "6":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
