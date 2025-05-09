"""
# Test script for YOLOe API endpoints
#
# Usage:
# python test_yoloe_api.py
"""

import os
import sys
import json
import requests
from pathlib import Path
import argparse
import base64
from PIL import Image
import io

# Constants
DEFAULT_API_URL = "http://0.0.0.0:8000/api/v1/yoloe"
DEFAULT_IMAGE_PATH = "../dataset/examples/boys.jpeg"  # Update with a correct path
DEFAULT_REFER_PATH = "../dataset/examples/boys.jpeg"  # Using same image for reference test

def test_image_prompt_endpoint(api_url, image_path, refer_path=None, save_output=True):
    """Test the image-prompt endpoint."""
    print("\n=== Testing YOLOe image-prompt endpoint ===")
    
    # Prepare endpoint URL
    endpoint_url = f"{api_url}/image-prompt"
    print(f"Endpoint URL: {endpoint_url}")
    
    # Prepare files and data
    files = {'file': open(image_path, 'rb')}
    
    # Create example bounding boxes (adjust these for your actual image)
    # Format: [x1, y1, x2, y2] for each box
    bboxes = [[100, 100, 200, 200], [300, 300, 400, 400]]
    cls = [0, 1]  # Classes 0 and 1 for the two boxes
    
    data = {
        'bboxes': json.dumps(bboxes),
        'cls': json.dumps(cls),
        'return_image': 'true',
        'conf': '0.25',
        'iou': '0.7',
        'retina_masks': 'true'
    }
    
    # Add reference image if provided
    if refer_path:
        print(f"Using reference image: {refer_path}")
        files['refer_file'] = open(refer_path, 'rb')
    
    # Make the request
    print("Sending request...")
    response = requests.post(endpoint_url, files=files, data=data)
    
    # Close file handles
    for f in files.values():
        f.close()
    
    # Process response
    if response.status_code == 200:
        print("Request successful!")
        result = response.json()
        
        # Print detection results summary
        if "results" in result and "class" in result["results"]:
            classes = result["results"]["class"]
            confidences = result["results"]["confidence"]
            
            print("\nDetections:")
            for i, (cls, conf) in enumerate(zip(classes, confidences)):
                print(f"  - {cls}: {conf:.2f}")
        else:
            print("No detections found.")
        
        # Save the annotated image if available
        if "annotated_image" in result and save_output:
            image_data = base64.b64decode(result["annotated_image"])
            image = Image.open(io.BytesIO(image_data))
            
            output_dir = "test_outputs"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "image_prompt_result.jpg")
            
            image.save(output_path)
            print(f"\nSaved annotated image to: {output_path}")
            
        # Save segmentation masks if available
        if "segmentation_masks" in result and save_output and result["segmentation_masks"]:
            output_dir = "test_outputs/masks"
            os.makedirs(output_dir, exist_ok=True)
            
            for i, mask_b64 in enumerate(result["segmentation_masks"]):
                if mask_b64:
                    mask_data = base64.b64decode(mask_b64)
                    mask = Image.open(io.BytesIO(mask_data))
                    
                    output_path = os.path.join(output_dir, f"mask_{i}.png")
                    mask.save(output_path)
            
            print(f"Saved {len(result['segmentation_masks'])} segmentation masks to: {output_dir}")
        
        return True
    else:
        print(f"Request failed with status code {response.status_code}")
        print(f"Error: {response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test YOLOe API endpoints")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument("--image", default=DEFAULT_IMAGE_PATH, help="Path to test image")
    parser.add_argument("--refer", default=None, help="Path to reference image (optional)")
    parser.add_argument("--no-save", action="store_true", help="Don't save output images")
    
    args = parser.parse_args()
    
    # Test image-prompt endpoint
    success = test_image_prompt_endpoint(
        args.api_url, 
        args.image, 
        args.refer, 
        not args.no_save
    )
    
    if success:
        print("\nAll tests completed successfully!")
    else:
        print("\nSome tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()