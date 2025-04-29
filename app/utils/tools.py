import base64
import io
import logging

import cv2
import numpy as np
from PIL.Image import Image
from fastapi import UploadFile


def read_imagefile(file: UploadFile) -> np.ndarray:
    """
    Converts an uploaded file into a NumPy BGR image array.
    """
    try:
        image_bytes = file.file.read()
        if not image_bytes:
            raise ValueError("Uploaded file is empty or invalid.")
        image_stream = io.BytesIO(image_bytes)
        pil_image = Image.open(image_stream).convert("RGB")
        # Convert PIL -> OpenCV (BGR)
        cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return cv2_image
    except Exception as e:
        logging.error(f"Error reading image file {file.filename}: {e}")
        raise ValueError(f"Failed to read image file: {e}")
    finally:
        # Reset file pointer in case it's needed again (though usually not for single read)
        if hasattr(file, 'file') and hasattr(file.file, 'seek'):
            file.file.seek(0)

def encode_bgr_image_to_base64(image_bgr: np.ndarray) -> str:
    """
    Encodes an OpenCV BGR image as base64 JPEG string.
    """
    success, encoded_image = cv2.imencode(".jpg", image_bgr)
    if not success:
        raise ValueError("Failed to encode image to JPEG.")
    base64_str = base64.b64encode(encoded_image.tobytes()).decode("utf-8")
    return base64_str

def encode_mask_to_base64(mask: np.ndarray) -> str:
    """
    Encodes a segmentation mask as base64 PNG string.
    """
    success, encoded_mask = cv2.imencode(".png", mask)
    if not success:
        raise ValueError("Failed to encode mask to PNG.")
    base64_str = base64.b64encode(encoded_mask.tobytes()).decode("utf-8")
    return base64_str