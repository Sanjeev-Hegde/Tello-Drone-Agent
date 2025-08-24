#!/usr/bin/env python3
"""
Tello Vision Demo - Use Tello camera for vision-only analysis.

This demo shows how to:
1. Connect to Tello drone 
2. Stream video from Tello camera
3. Analyze frames with Azure AI Vision
4. Display results without controlling the drone

SETUP REQUIREMENTS:
1. Power on your Tello drone
2. Connect your computer to Tello WiFi (TELLO-XXXXXX)
3. Run this script

Usage:
    python examples/tello_vision_demo.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from vision.camera_manager import CameraManager
from agents.vision_agent import VisionAgent
from config.settings import setup_logging


async def main():
    """Main demo function."""
    
    # Setup logging
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("🚁 Tello Vision Demo Starting...")
    logger.info("📹 This demo will connect to Tello camera and analyze video frames")
    
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
        logger.error("💡 Make sure you're connected to Tello WiFi and drone is powered on")
    
    finally:
        # Cleanup
        if camera_manager:
            await camera_manager.stop()
        logger.info("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
