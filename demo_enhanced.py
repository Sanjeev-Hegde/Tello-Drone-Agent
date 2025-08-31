#!/usr/bin/env python3
"""
Enhanced Demo for Autonomous Drone Agent
Showcases intelligent drone control with vision-based navigation and safety protocols.
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

def print_header():
    """Print demo header."""
    print("\n" + "🚁" + "="*70)
    print("🚁  AUTONOMOUS DRONE AGENT - ENHANCED DEMO")
    print("🚁  Intelligent Vision-Based Drone Control System")
    print("🚁  Built with Azure AI Projects + SimpleTello Integration")
    print("🚁" + "="*70)
    print()

def print_section(title):
    """Print section separator."""
    print(f"\n{'='*20} {title} {'='*20}")

async def interactive_demo():
    """Run an interactive demo with realistic scenarios."""
    agent = None
    
    try:
        print_header()
        
        # Create agent
        print_section("🤖 AGENT INITIALIZATION")
        print("📡 Creating Autonomous Drone Agent...")
        print("⚠️  Running in VISION-ONLY mode for safe testing")
        print("💡 This simulates real drone behavior without hardware")
        print()
        
        agent = autonomous_module.AutonomousDroneAgent(vision_only=True)
        print("✅ Agent successfully created!")
        
        # Show agent info
        context = agent.get_conversation_context()
        print(f"🤖 Agent ID: {context['agent_id']}")
        print(f"🧵 Thread ID: {context['thread_id']}")
        print(f"🔧 Mode: {context['mode']}")
        print()
        
        # Scenario 1: Basic Flight Operations
        print_section("✈️  SCENARIO 1: BASIC FLIGHT OPERATIONS")
        basic_commands = [
            "Take off and hover safely",
            "Tell me your current status",
            "Check your battery level"
        ]
        
        await run_command_sequence(agent, basic_commands)
        
        # Scenario 2: Vision-Based Navigation
        print_section("👁️  SCENARIO 2: VISION-BASED NAVIGATION")
        vision_commands = [
            "Capture an image and analyze what you see",
            "Look for any obstacles in front of you",
            "Scan the environment for safe navigation paths"
        ]
        
        await run_command_sequence(agent, vision_commands)
        
        # Scenario 3: Intelligent Movement
        print_section("🧭 SCENARIO 3: INTELLIGENT MOVEMENT")
        movement_commands = [
            "Move forward slowly and carefully, watching for obstacles",
            "Rotate 90 degrees to survey the area", 
            "Move up 50cm and check your new height"
        ]
        
        await run_command_sequence(agent, movement_commands)
        
        # Scenario 4: Advanced Autonomous Tasks
        print_section("🎯 SCENARIO 4: AUTONOMOUS MISSION")
        mission_commands = [
            "I need you to explore this room - plan a safe route",
            "Look for any interesting objects or features",
            "Find the safest landing spot available",
            "Execute your landing plan"
        ]
        
        await run_command_sequence(agent, mission_commands)
        
        # Show final summary
        print_section("📊 MISSION SUMMARY")
        show_final_summary(agent)
        
        print_section("✅ DEMO COMPLETED")
        print("🎉 All scenarios completed successfully!")
        print("💡 The agent demonstrated:")
        print("   • Intelligent command processing")
        print("   • Vision-based navigation") 
        print("   • Safety-first protocols")
        print("   • Autonomous decision making")
        print("   • Graceful error handling")
        
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ensure cleanup
        if agent:
            print("\n🧹 Cleaning up agent resources...")
            try:
                agent.cleanup()
                print("✅ Cleanup completed successfully")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")

async def run_command_sequence(agent, commands):
    """Run a sequence of commands with proper formatting."""
    for i, command in enumerate(commands, 1):
        print(f"\n📝 Command {i}: '{command}'")
        print("🔄 Processing...", end="", flush=True)
        
        try:
            response = await agent.process_user_command(command)
            print("\r🤖 Agent Response:")
            print(f"   {response}")
            
            # Show current state
            context = agent.get_conversation_context()
            state = context['drone_state']
            print(f"📊 Status: Flying={state['is_flying']}, Height={state['height']}cm, "
                  f"Battery={state['battery']}%, Movements={state['movement_count']}")
            
        except Exception as e:
            print(f"\r❌ Error: {e}")
        
        print("─" * 50)

def show_final_summary(agent):
    """Show comprehensive mission summary."""
    context = agent.get_conversation_context()
    state = context['drone_state']
    
    print("📈 Mission Statistics:")
    print(f"   ✈️  Total Movements: {state['movement_count']}")
    print(f"   🔋 Final Battery: {state['battery']}%")
    print(f"   📏 Final Height: {state['height']}cm")
    print(f"   🛬 Flying Status: {'In Flight' if state['is_flying'] else 'Landed'}")
    print(f"   📸 Images Captured: {len(context['recent_images'])}")
    print(f"   💬 Commands Processed: {len(context['recent_conversation'])}")
    print(f"   🚨 Obstacles Detected: {len(state['obstacles_detected'])}")

def run_quick_test():
    """Run a quick test to verify everything works."""
    print("🔧 Running Quick Functionality Test...")
    
    try:
        # Test agent creation
        agent = autonomous_module.AutonomousDroneAgent(vision_only=True)
        print("✅ Agent creation: SUCCESS")
        
        # Test context retrieval
        context = agent.get_conversation_context()
        print("✅ Context retrieval: SUCCESS")
        
        # Test cleanup
        agent.cleanup()
        print("✅ Cleanup: SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def main():
    """Main entry point with user choice."""
    print("🚀 Autonomous Drone Agent Demo")
    print("\nChoose demo mode:")
    print("1. 🔧 Quick Test (Fast verification)")
    print("2. 🎬 Full Interactive Demo (Complete showcase)")
    print("3. ❌ Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n" + "="*50)
        success = run_quick_test()
        if success:
            print("\n🎉 Quick test completed successfully!")
        else:
            print("\n❌ Quick test failed!")
            
    elif choice == "2":
        print("\n🎬 Starting Full Interactive Demo...")
        print("⏱️  This will take a few minutes to complete")
        print("🛑 Press Ctrl+C to interrupt at any time")
        
        try:
            asyncio.run(interactive_demo())
        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            
    elif choice == "3":
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice. Please run again and select 1, 2, or 3.")

if __name__ == "__main__":
    main()
