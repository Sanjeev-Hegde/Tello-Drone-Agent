"""
Example usage of the Tello Drone AI Agent - Vision Only Mode.

This example demonstrates how to use the vision system with a webcam
for testing and development purposes.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.vision_agent import VisionAgent
from vision.camera_manager import CameraManager
from vision.object_detector import ObjectDetector
import cv2


async def vision_only_demo():
    """
    Demonstrate vision-only functionality using webcam.
    """
    print("Starting Vision-Only Demo...")
    
    try:
        # Initialize components
        vision_agent = VisionAgent()
        camera_manager = CameraManager()
        object_detector = ObjectDetector()
        
        # Initialize webcam
        if not await camera_manager.initialize("webcam"):
            print("Failed to initialize webcam")
            return
        
        print("Vision system initialized successfully")
        print("Available commands:")
        print("  - 'count chairs' - Count chairs in view")
        print("  - 'find people' - Find people in view")
        print("  - 'analyze scene' - Get scene description")
        print("  - 'quit' - Exit")
        
        # Start frame processing
        await camera_manager.start_processing()
        
        while True:
            try:
                # Get user input
                user_input = input("\nEnter vision command: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                # Get current frame
                frame = camera_manager.get_current_frame()
                if frame is None:
                    print("No camera frame available")
                    continue
                
                # Analyze frame
                print(f"Analyzing: {user_input}")
                analysis = vision_agent.analyze_image(frame, user_input)
                
                # Display results
                if analysis.get("error"):
                    print(f"Error: {analysis.get('description')}")
                else:
                    if "query_response" in analysis:
                        print(f"Result: {analysis['query_response']}")
                    else:
                        description = analysis.get("description", "")
                        objects = analysis.get("objects", [])
                        if objects:
                            object_names = [obj["name"] for obj in objects]
                            print(f"Scene: {description}")
                            print(f"Objects: {', '.join(object_names)}")
                        else:
                            print(f"Scene: {description}")
                            print("No objects detected")
                
                # Show annotated frame
                if objects:
                    annotated_frame = object_detector.draw_detections(frame, objects)
                    cv2.imshow("Vision Analysis", annotated_frame)
                    cv2.waitKey(1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error processing command: {e}")
        
        # Cleanup
        await camera_manager.stop_processing()
        cv2.destroyAllWindows()
        print("Demo completed")
        
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    # Note: This example requires Azure AI Vision to be configured
    print("Vision-Only Demo")
    print("Make sure to configure Azure AI Vision credentials in .env file")
    
    try:
        asyncio.run(vision_only_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted")
    except Exception as e:
        print(f"Demo error: {e}")
