"""
Azure AI Vision Agent.
Provides real-time object detection and analysis using Azure AI Vision API.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image
import io
import base64
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from config.settings import settings, config_manager


class VisionAgent:
    """
    Azure AI Vision-powered agent for real-time object detection and analysis.
    
    This agent processes images from the drone camera or webcam and provides
    detailed object detection, counting, and scene analysis using the modern
    Azure AI Vision API.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._setup_ai_vision()
    
    def _setup_ai_vision(self):
        """Setup Azure AI Vision client with secure authentication."""
        try:
            # Get API key securely from Key Vault or environment
            vision_key = config_manager.get_ai_vision_key()
            
            if not vision_key:
                raise ValueError("Azure AI Vision key not found in Key Vault or environment")
            
            # Create credentials and client
            credential = AzureKeyCredential(vision_key)
            self.client = ImageAnalysisClient(
                endpoint=settings.azure_ai_vision_endpoint,
                credential=credential
            )
            
            self.logger.info("Azure AI Vision client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure AI Vision client: {e}")
            raise
    
    async def analyze_image(self, image, query: str = "") -> Dict[str, Any]:
        """
        Analyze image using Azure AI Vision API.
        
        Args:
            image: Image as numpy array (RGB format) or PIL Image
            query: Optional specific query about the image
            
        Returns:
            Analysis results including objects, descriptions, and counts
        """
        try:
            import time
            start_time = time.time()
            
            # Convert image to bytes
            image_bytes = self._image_to_bytes(image)
            
            # Debug: Save the image being analyzed (optional)
            if self.logger.level <= 10:  # DEBUG level
                self._save_debug_image(image, image_bytes)
            
            # Log image info
            self.logger.info(f"Analyzing image: {len(image_bytes)} bytes, type: {type(image)}")
            
            # Create analysis request
            result = self.client.analyze(
                image_data=image_bytes,
                visual_features=[
                    VisualFeatures.OBJECTS,
                    VisualFeatures.PEOPLE, 
                    VisualFeatures.CAPTION,
                    VisualFeatures.TAGS,
                    VisualFeatures.DENSE_CAPTIONS
                ]
            )
            
            # Process all results
            objects = self._process_objects(result.objects)
            people = self._process_people(result.people)
            description = self._process_caption(result.caption)
            tags = self._process_tags(result.tags)
            dense_captions = self._process_dense_captions(result.dense_captions)
            navigation_suggestions = self._generate_navigation_suggestions(result)
            
            # Log summary of what was detected
            self.logger.info(f"Analysis complete: {len(objects)} objects, {len(people)} people, {len(tags)} tags, {len(dense_captions)} captions")
            
            return {
                "objects": objects,
                "people": people,
                "description": description,
                "tags": tags,
                "dense_captions": dense_captions,
                "navigation_suggestions": navigation_suggestions,
                "timestamp": time.time() - start_time
            }
            
            # Process specific query if provided
            if query:
                analysis_results["query_response"] = self._process_query(
                    analysis_results, query
                )
            
            self.logger.debug(f"Image analysis completed: {len(analysis_results['objects'])} objects detected")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Image analysis failed: {e}")
            return self._get_error_analysis(str(e))
    
    def _process_objects(self, objects_result) -> List[Dict[str, Any]]:
        """Process object detection results."""
        if not objects_result or not objects_result.list:
            self.logger.info("No objects detected by Azure AI Vision")
            return []
        
        all_objects = []
        filtered_objects = []
        
        for obj in objects_result.list:
            # In the new API, objects have tags instead of direct name/confidence
            # Each object should have at least one tag
            if obj.tags and len(obj.tags) > 0:
                # Use the first (highest confidence) tag for the object name and confidence
                primary_tag = obj.tags[0]
                obj_info = {
                    "name": primary_tag.name,
                    "confidence": primary_tag.confidence,
                    "bounding_box": {
                        "x": obj.bounding_box.x,
                        "y": obj.bounding_box.y,
                        "width": obj.bounding_box.width,
                        "height": obj.bounding_box.height
                    }
                }
                all_objects.append(obj_info)
                
                if primary_tag.confidence >= settings.vision_confidence_threshold:
                    filtered_objects.append(obj_info)
        
        self.logger.info(f"Objects detected: {len(all_objects)} total, {len(filtered_objects)} above threshold ({settings.vision_confidence_threshold})")
        for obj in all_objects:
            status = "✓" if obj["confidence"] >= settings.vision_confidence_threshold else "✗"
            self.logger.info(f"  {status} {obj['name']}: {obj['confidence']:.3f}")
        
        return filtered_objects
    
    def _process_people(self, people_result) -> List[Dict[str, Any]]:
        """Process people detection results."""
        if not people_result or not people_result.list:
            return []
        
        people = []
        for person in people_result.list:
            if person.confidence >= settings.vision_confidence_threshold:
                people.append({
                    "name": "person",
                    "confidence": person.confidence,
                    "bounding_box": {
                        "x": person.bounding_box.x,
                        "y": person.bounding_box.y,
                        "width": person.bounding_box.width,
                        "height": person.bounding_box.height
                    }
                })
        
        return people
    
    def _process_caption(self, caption_result) -> str:
        """Process image caption."""
        if caption_result and caption_result.text:
            return caption_result.text
        return "No description available"
    
    def _process_tags(self, tags_result) -> List[str]:
        """Process image tags."""
        if not tags_result or not tags_result.list:
            return []
        
        return [
            tag.name for tag in tags_result.list 
            if tag.confidence >= settings.vision_confidence_threshold
        ]
    
    def _process_dense_captions(self, dense_captions_result) -> List[Dict[str, Any]]:
        """Process dense captions (detailed region descriptions)."""
        if not dense_captions_result or not dense_captions_result.list:
            return []
        
        captions = []
        for caption in dense_captions_result.list:
            if caption.confidence >= settings.vision_confidence_threshold:
                captions.append({
                    "text": caption.text,
                    "confidence": caption.confidence,
                    "bounding_box": {
                        "x": caption.bounding_box.x,
                        "y": caption.bounding_box.y,
                        "width": caption.bounding_box.width,
                        "height": caption.bounding_box.height
                    } if caption.bounding_box else None
                })
        
        return captions
    
    def _generate_navigation_suggestions(self, result) -> List[str]:
        """Generate navigation suggestions based on analysis results."""
        suggestions = []
        
        # Check for people (safety priority)
        if hasattr(result, 'people') and result.people and result.people.list:
            people_count = len(result.people.list)
            suggestions.append(f"Caution: {people_count} people detected - maintain safe distance")
        
        # Check for obstacles
        if hasattr(result, 'objects') and result.objects and result.objects.list:
            obstacle_objects = []
            for obj in result.objects.list:
                # In the new API, objects have tags instead of direct name
                if obj.tags and len(obj.tags) > 0:
                    primary_tag = obj.tags[0]
                    if primary_tag.name.lower() in ["wall", "tree", "building", "car", "table", "chair", "pole"]:
                        obstacle_objects.append(obj)
            
            if obstacle_objects:
                suggestions.append(f"Navigate carefully around {len(obstacle_objects)} detected obstacles")
        
        # General navigation advice
        if not suggestions:
            suggestions.append("Area appears clear for normal flight operations")
        
        return suggestions
    
    
    def _process_query(self, analysis_results: Dict[str, Any], query: str) -> str:
        """
        Process specific query about the image analysis.
        
        Args:
            analysis_results: Results from image analysis
            query: User's specific question
            
        Returns:
            Response to the query
        """
        query_lower = query.lower()
        objects = analysis_results.get("objects", [])
        people = analysis_results.get("people", [])
        all_detected = objects + people
        
        # Count objects
        if "how many" in query_lower or "count" in query_lower:
            return self._count_objects(all_detected, query_lower)
        
        # Find specific objects
        elif "find" in query_lower or "locate" in query_lower:
            return self._find_objects(all_detected, query_lower)
        
        # People-specific queries
        elif "people" in query_lower or "person" in query_lower:
            people_count = len(people)
            if people_count == 0:
                return "I don't see any people in the image."
            elif people_count == 1:
                return "I can see 1 person in the image."
            else:
                return f"I can see {people_count} people in the image."
        
        # General description
        else:
            description = analysis_results.get("description", "")
            object_names = [obj["name"] for obj in all_detected]
            if object_names:
                return f"{description} I can see: {', '.join(set(object_names))}"
            else:
                return description
    
    def _count_objects(self, detected_items: List[Dict[str, Any]], query: str) -> str:
        """Count specific objects based on query."""
        # Extract target object from query
        target_objects = []
        for item in detected_items:
            item_name = item["name"].lower()
            if any(word in query for word in item_name.split()):
                target_objects.append(item)
        
        if not target_objects:
            # Try common object names
            common_objects = ["chair", "table", "person", "people", "bottle", "book", "laptop", "car", "phone"]
            for common_obj in common_objects:
                if common_obj in query:
                    matching_objects = [
                        item for item in detected_items 
                        if common_obj in item["name"].lower() or (common_obj == "people" and item["name"] == "person")
                    ]
                    if matching_objects:
                        count = len(matching_objects)
                        object_name = "people" if common_obj in ["people", "person"] else common_obj
                        return f"I found {count} {object_name}{'s' if count > 1 and not object_name.endswith('s') else ''} in the image."
            
            return "I couldn't find the specific objects you're looking for in the image."
        
        object_type = target_objects[0]["name"]
        count = len(target_objects)
        return f"I found {count} {object_type}{'s' if count > 1 and not object_type.endswith('s') else ''} in the image."
    
    def _find_objects(self, detected_items: List[Dict[str, Any]], query: str) -> str:
        """Find and locate specific objects."""
        found_objects = []
        
        for item in detected_items:
            item_name = item["name"].lower()
            if any(word in query for word in item_name.split()):
                bbox = item["bounding_box"]
                location = self._describe_location(bbox)
                found_objects.append(f"{item['name']} {location}")
        
        if found_objects:
            return f"I found: {', '.join(found_objects)}"
        else:
            return "I couldn't find the specified objects in the current view."
    
    def _describe_location(self, bbox: Dict[str, int]) -> str:
        """Describe the location of an object based on its bounding box."""
        x, y = bbox["x"], bbox["y"]
        
        # Assume standard image dimensions (this could be made more precise)
        horizontal = "left" if x < 200 else "center" if x < 400 else "right"
        vertical = "top" if y < 150 else "middle" if y < 300 else "bottom"
        
        return f"in the {vertical}-{horizontal} of the image"
    
    def _image_to_bytes(self, image) -> bytes:
        """Convert image (numpy array or PIL Image) to bytes for API call."""
        # Handle PIL Image
        if isinstance(image, Image.Image):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            return img_byte_arr.getvalue()
        
        # Handle numpy array
        if isinstance(image, np.ndarray):
            # Convert numpy array to PIL Image (assumes RGB format)
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image)
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='JPEG', quality=85)
            return img_byte_arr.getvalue()
        
        # If neither, raise an error
        raise ValueError(f"Unsupported image type: {type(image)}. Expected numpy.ndarray or PIL.Image.Image")
    
    def _save_debug_image(self, image, image_bytes: bytes):
        """Save debug image to see what's being analyzed."""
        try:
            import os
            import time
            
            # Create debug directory
            debug_dir = "debug_images"
            os.makedirs(debug_dir, exist_ok=True)
            
            # Save with timestamp
            timestamp = int(time.time() * 1000)
            filename = f"{debug_dir}/debug_image_{timestamp}.jpg"
            
            # Save the actual bytes being sent to API
            with open(filename, 'wb') as f:
                f.write(image_bytes)
            
            self.logger.debug(f"Debug image saved: {filename}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save debug image: {e}")
    
    def _get_error_analysis(self, error_message: str) -> Dict[str, Any]:
        """Generate error analysis result."""
        return {
            "objects": [],
            "people": [],
            "description": f"Analysis failed: {error_message}",
            "tags": [],
            "dense_captions": [],
            "error": True,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    def count_objects_in_image(self, image: np.ndarray, object_type: str) -> int:
        """
        Count specific objects in the image.
        
        Args:
            image: Image as numpy array (RGB format)
            object_type: Type of object to count
            
        Returns:
            Number of objects found
        """
        analysis = asyncio.run(self.analyze_image(image, f"count {object_type}"))
        objects = analysis.get("objects", [])
        people = analysis.get("people", [])
        all_items = objects + people
        
        # Count objects matching the type
        count = sum(
            1 for item in all_items 
            if object_type.lower() in item["name"].lower()
        )
        
        return count
    
    def get_scene_summary(self, image: np.ndarray) -> str:
        """
        Get a comprehensive summary of the scene.
        
        Args:
            image: Image as numpy array (RGB format)
            
        Returns:
            Scene summary text
        """
        analysis = asyncio.run(self.analyze_image(image))
        
        description = analysis.get("description", "")
        objects = analysis.get("objects", [])
        people = analysis.get("people", [])
        tags = analysis.get("tags", [])
        
        # Combine objects and people for counting
        all_items = objects + people
        
        item_counts = {}
        for item in all_items:
            name = item["name"]
            item_counts[name] = item_counts.get(name, 0) + 1
        
        summary_parts = [description]
        
        if item_counts:
            counts_str = ", ".join([
                f"{count} {name}{'s' if count > 1 and not name.endswith('s') else ''}" 
                for name, count in item_counts.items()
            ])
            summary_parts.append(f"Detected: {counts_str}")
        
        if tags:
            summary_parts.append(f"Scene elements: {', '.join(tags[:5])}")
        
        return ". ".join(summary_parts)
    
    def analyze_for_drone_navigation(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze image specifically for drone navigation and safety.
        
        Args:
            image: Image as numpy array (RGB format)
            
        Returns:
            Navigation analysis with safety recommendations
        """
        analysis = asyncio.run(self.analyze_image(image))
        
        # Extract navigation-relevant information
        objects = analysis.get("objects", [])
        people = analysis.get("people", [])
        
        # Safety assessment
        safety_concerns = []
        if people:
            safety_concerns.append(f"{len(people)} people detected - maintain safe distance")
        
        # Identify obstacles
        obstacles = [obj for obj in objects if obj["name"].lower() in 
                    ["wall", "tree", "building", "car", "table", "chair", "pole"]]
        
        if obstacles:
            safety_concerns.append(f"{len(obstacles)} potential obstacles detected")
        
        # Navigation recommendations
        navigation_info = {
            "safe_to_fly": len(safety_concerns) == 0,
            "safety_concerns": safety_concerns,
            "people_count": len(people),
            "obstacle_count": len(obstacles),
            "clear_space": len(objects) < 5,  # Simple heuristic
            "description": analysis.get("description", ""),
            "recommendations": self._generate_navigation_recommendations(people, obstacles)
        }
        
        return navigation_info
    
    def _generate_navigation_recommendations(self, people: List[Dict], obstacles: List[Dict]) -> List[str]:
        """Generate navigation recommendations based on detected objects."""
        recommendations = []
        
        if people:
            recommendations.append("Maintain minimum 3-meter distance from people")
            recommendations.append("Reduce flight speed in populated areas")
        
        if obstacles:
            recommendations.append("Navigate carefully around detected obstacles")
            recommendations.append("Consider altitude adjustment to avoid obstacles")
        
        if not people and not obstacles:
            recommendations.append("Area appears clear for normal flight operations")
        
        return recommendations
