#!/usr/bin/env python3
"""
Simple Tello Vision Demo with Network Connectivity Check.

This demo connects to Tello and uses Azure AI Vision, 
but checks for proper network setup first.

NETWORK REQUIREMENTS:
- Internet access (for Azure AI Vision API)
- Tello WiFi access (for drone camera)
- See NETWORK_SOLUTIONS.md for setup instructions

Usage:
    python examples/tello_vision_simple.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import subprocess
import requests

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from vision.camera_manager import CameraManager
from agents.vision_agent import VisionAgent
from config.settings import setup_logging


def check_network_connectivity():
    """Check both internet and Tello connectivity."""
    results = {"internet": False, "tello": False}
    
    # Check internet
    try:
        response = requests.get("https://www.microsoft.com", timeout=5)
        results["internet"] = response.status_code == 200
    except:
        results["internet"] = False
    
    # Check Tello
    try:
        # Ping Tello
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2000", "192.168.10.1"], 
            capture_output=True, 
            timeout=5
        )
        results["tello"] = result.returncode == 0
    except:
        results["tello"] = False
    
    return results


async def main():
    """Main demo function."""
    
    # Setup logging
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("🚁 Simple Tello Vision Demo Starting...")
    
    # Check network connectivity
    logger.info("🔍 Checking network connectivity...")
    connectivity = check_network_connectivity()
    
    # Report results
    internet_status = "✅" if connectivity["internet"] else "❌"
    tello_status = "✅" if connectivity["tello"] else "❌"
    
    logger.info(f"   Internet access: {internet_status}")
    logger.info(f"   Tello access: {tello_status}")
    
    # Check if we can proceed
    if not connectivity["internet"]:
        logger.error("❌ No internet access - Azure AI Vision won't work")
        logger.error("💡 SOLUTIONS:")
        logger.error("   1. Use mobile hotspot + Tello WiFi")
        logger.error("   2. Use USB tethering + Tello WiFi")
        logger.error("   3. See NETWORK_SOLUTIONS.md for more options")
        return
    
    if not connectivity["tello"]:
        logger.error("❌ No Tello access")
        logger.error("💡 SOLUTIONS:")
        logger.error("   1. Power on Tello drone")
        logger.error("   2. Connect to TELLO-XXXXXX WiFi")
        logger.error("   3. Wait for connection to establish")
        return
    
    logger.info("🎉 Network setup is correct! Starting demo...")
    
    # Initialize components
    vision_agent = VisionAgent()
    camera_manager = None
    
    try:
        # Create camera manager for Tello
        camera_manager = CameraManager(source="tello")
        
        # Start camera
        await camera_manager.start()
        
        logger.info("✅ Demo running! Press Ctrl+C to stop")
        logger.info("📊 Analyzing frames from Tello camera...")
        
        frame_count = 0
        
        while True:
            try:
                # Capture frame
                frame = camera_manager.capture_single_frame()
                
                if frame is not None:
                    frame_count += 1
                    
                    # Analyze every 30th frame (roughly once per second)
                    if frame_count % 30 == 0:
                        logger.info(f"🔍 Analyzing frame {frame_count}...")
                        
                        analysis = await vision_agent.analyze_image(frame)
                        
                        if analysis and not analysis.get('error'):
                            # Print analysis results
                            objects = analysis.get('objects', [])
                            people = analysis.get('people', [])
                            description = analysis.get('description', 'No description')
                            tags = analysis.get('tags', [])
                            
                            logger.info("📋 ANALYSIS RESULTS:")
                            logger.info(f"   Description: {description}")
                            logger.info(f"   Objects: {len(objects)} detected")
                            for obj in objects[:3]:  # Show first 3 objects
                                logger.info(f"     - {obj['name']} ({obj['confidence']:.2f})")
                            logger.info(f"   People: {len(people)} detected")
                            logger.info(f"   Tags: {', '.join(tags[:5])}")  # Show first 5 tags
                            
                            # Navigation suggestions for safety
                            nav_suggestions = analysis.get('navigation_suggestions', [])
                            if nav_suggestions:
                                logger.info(f"   🚨 Safety: {nav_suggestions[0]}")
                        else:
                            logger.warning("⚠️  Frame analysis failed")
                
                # Small delay
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("👋 Demo stopped by user")
    
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        logger.error("💡 Check NETWORK_SOLUTIONS.md for troubleshooting")
    
    finally:
        # Cleanup
        if camera_manager:
            await camera_manager.stop()
        logger.info("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
