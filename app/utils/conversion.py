# Utility functions for annotation format conversion

import logging

def convert_to_yolo_format(annotations: list, image_width: int, image_height: int, class_name_to_id: dict) -> str:
    """
    Converts a list of annotations to YOLO format string.

    Args:
        annotations: A list of annotation dictionaries. Each dict should have
                     'bbox' (list/tuple: [x_min, y_min, width, height]) and
                     'category_name' (str).
        image_width: The width of the image.
        image_height: The height of the image.
        class_name_to_id: A dictionary mapping category names (str) to YOLO class IDs (int, 0-based).

    Returns:
        A string containing annotations in YOLO format, one line per annotation.
        Returns an empty string if annotations list is empty or image dimensions are invalid.
    """
    if not annotations or image_width <= 0 or image_height <= 0:
        return ""

    yolo_lines = []
    for ann in annotations:
        try:
            # Use category_name, which reflects user edits if any
            class_name = ann.get('category_name')
            if class_name is None or class_name not in class_name_to_id:
                logging.warning(f"Skipping annotation due to missing or unknown category_name: {ann}")
                continue

            class_id = class_name_to_id[class_name]

            # Assuming bbox is [x_min, y_min, width, height]
            # Frontend sends x, y, width, height directly
            x_min = float(ann.get('x', ann.get('bbox', [0,0,0,0])[0]))
            y_min = float(ann.get('y', ann.get('bbox', [0,0,0,0])[1]))
            width = float(ann.get('width', ann.get('bbox', [0,0,0,0])[2]))
            height = float(ann.get('height', ann.get('bbox', [0,0,0,0])[3]))

            # Calculate center coordinates and dimensions
            x_center = x_min + width / 2
            y_center = y_min + height / 2

            # Normalize coordinates and dimensions
            x_center_norm = x_center / image_width
            y_center_norm = y_center / image_height
            width_norm = width / image_width
            height_norm = height / image_height

            # Clamp values to be within [0.0, 1.0] to avoid issues with minor rounding errors
            x_center_norm = max(0.0, min(1.0, x_center_norm))
            y_center_norm = max(0.0, min(1.0, y_center_norm))
            width_norm = max(0.0, min(1.0, width_norm))
            height_norm = max(0.0, min(1.0, height_norm))

            # Format the YOLO line
            yolo_line = f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {width_norm:.6f} {height_norm:.6f}"
            yolo_lines.append(yolo_line)

        except (KeyError, TypeError, ValueError, IndexError) as e:
            logging.warning(f"Skipping annotation due to error: {e}. Annotation data: {ann}")
            continue

    return "\n".join(yolo_lines)

# Example Usage (for testing):
if __name__ == '__main__':
    example_annotations = [
        {'id': 1, 'category_id': 0, 'category_name': 'person', 'bbox': [100, 100, 50, 150], 'confidence': 0.9, 'x': 100, 'y': 100, 'width': 50, 'height': 150},
        {'id': 2, 'category_id': 1, 'category_name': 'car', 'bbox': [300, 200, 100, 80], 'confidence': 0.8, 'x': 300, 'y': 200, 'width': 100, 'height': 80},
        {'id': 3, 'category_id': 0, 'category_name': 'person', 'bbox': [500, 50, 40, 120], 'confidence': 0.95, 'x': 500, 'y': 50, 'width': 40, 'height': 120},
        {'id': 4, 'category_name': 'unknown', 'bbox': [10, 10, 10, 10], 'x': 10, 'y': 10, 'width': 10, 'height': 10}, # Should be skipped
        {'id': 5, 'category_name': 'car', 'bbox': [0, 0, 640, 480], 'x': 0, 'y': 0, 'width': 640, 'height': 480}, # Full image
    ]
    img_w, img_h = 640, 480
    class_map = {'person': 0, 'car': 1, 'dog': 2} # 'unknown' is not here

    yolo_output = convert_to_yolo_format(example_annotations, img_w, img_h, class_map)
    print(f"--- YOLO Output (Image: {img_w}x{img_h}) ---")
    print(yolo_output)
    print("--- End YOLO Output ---")

    # Test edge cases
    print("\n--- Testing Edge Cases ---")
    print("Empty annotations:", convert_to_yolo_format([], img_w, img_h, class_map))
    print("Invalid dimensions:", convert_to_yolo_format(example_annotations, 0, 0, class_map))
    print("--- End Edge Cases ---")

