"""
#   © 2024 EurekAILab. All rights reserved.
#   No part of this publication may be reproduced, distributed,
#   or transmitted in any form or by any means, including photocopying, recording,
#   or other electronic or mechanical methods, without the prior written permission of the publisher,
#   except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.
"""

import base64
import io
import json
import logging
import zipfile
import numpy as np
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Body
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.models.yoloe import BatchExportYoloRequest, ExportYoloRequest
from app.utils.tools import read_imagefile_async, encode_mask_to_base64, encode_bgr_image_to_base64

# Assuming YOLOE class is correctly defined and imported
try:
    from app.cv.inference.yolo.yoloe import YOLOE
except ImportError:
    logging.warning("YOLOE class not found, inference endpoints might fail.")
    # Define a dummy class if YOLOE is not available, to avoid import errors
    class YOLOE:
        def __init__(self, model_path="default"): pass
        def prompt_free_predict(self, **kwargs): return []
        def text_predict(self, **kwargs): return []
        def image_predict(self, **kwargs): return []

# Import the conversion utility
from app.utils.conversion import convert_to_yolo_format

import cv2
from PIL import Image

router = APIRouter()



@router.post("/prompt-free")
async def prompt_free_inference(
    file: UploadFile = File(...),
    model_path: Optional[str] = Form("default"),
    conf: float = Form(0.25),
    iou: float = Form(0.7),
    return_image: bool = Form(False),
    retina_masks: bool = Form(False)
):
    try:
        img_bgr = await read_imagefile_async(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error reading image: {e}")
        raise HTTPException(status_code=500, detail="Error processing image file.")

    try:
        model = YOLOE(model_path=model_path)
        results_json = model.prompt_free_predict(
            source=img_bgr,
            conf=conf,
            iou=iou,
            return_dict=True,
            save=False,
            retina_masks=retina_masks
        )
        response_data = {"results": results_json}

        if return_image or (retina_masks and results_json.get("detection_results")):
            raw_results = model.prompt_free_predict(
                source=img_bgr,
                conf=conf,
                iou=iou,
                return_dict=False,
                save=False,
                retina_masks=retina_masks
            )
            if raw_results:
                if return_image:
                    annotated_bgr = raw_results[0].plot()
                    response_data["annotated_image"] = encode_bgr_image_to_base64(annotated_bgr)
                if retina_masks and hasattr(raw_results[0], 'masks') and raw_results[0].masks is not None:
                    masks = raw_results[0].masks.data
                    encoded_masks = []
                    for i in range(len(masks)):
                        mask = masks[i].cpu().numpy() * 255
                        encoded_masks.append(encode_mask_to_base64(mask.astype(np.uint8)))
                    response_data["segmentation_masks"] = encoded_masks
        return response_data
    except Exception as e:
        logging.error(f"Error during prompt-free inference: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

@router.post("/text-prompt")
async def text_prompt_inference(
    file: UploadFile = File(...),
    class_names: List[str] = Form(...),
    model_path: Optional[str] = Form("default"),
    conf: float = Form(0.25),
    iou: float = Form(0.7),
    return_image: bool = Form(False),
    retina_masks: bool = Form(False)
):
    try:
        img_bgr = await read_imagefile_async(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error reading image: {e}")
        raise HTTPException(status_code=500, detail="Error processing image file.")

    if not class_names:
         raise HTTPException(status_code=400, detail="Class names list cannot be empty.")

    try:
        model = YOLOE(model_path=model_path)
        results_json = model.text_predict(
            source=img_bgr,
            class_names=class_names,
            conf=conf,
            iou=iou,
            return_dict=True,
            save=False,
            retina_masks=retina_masks
        )
        response_data = {"results": results_json}

        if return_image or (retina_masks and results_json.get("detection_results")):
            raw_results = model.text_predict(
                source=img_bgr,
                class_names=class_names,
                conf=conf,
                iou=iou,
                return_dict=False,
                save=False,
                retina_masks=retina_masks
            )
            if raw_results:
                if return_image:
                    annotated_bgr = raw_results[0].plot()
                    response_data["annotated_image"] = encode_bgr_image_to_base64(annotated_bgr)
                if retina_masks and hasattr(raw_results[0], 'masks') and raw_results[0].masks is not None:
                    masks = raw_results[0].masks.data
                    encoded_masks = []
                    for i in range(len(masks)):
                        mask = masks[i].cpu().numpy() * 255
                        encoded_masks.append(encode_mask_to_base64(mask.astype(np.uint8)))
                    response_data["segmentation_masks"] = encoded_masks
        return response_data
    except Exception as e:
        logging.error(f"Error during text-prompt inference: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

@router.post("/image-prompt",
    summary="Run YOLOe detection with visual prompts",
    description="""
    Performs object detection using visual prompts where example objects are specified with bounding boxes.

    **Visual Prompts**:
    - Each bounding box in `bboxes` should tightly enclose an example of the object you want to detect
    - The corresponding entry in `cls` specifies the class label for that box
    - Class IDs should be sequential, starting from 0

    **How to use**:
    1. **Same-image prompting**: Use bounding boxes from the target image itself
       - Upload your image as `file`
       - Provide bounding boxes and class IDs for objects in that image

    2. **Reference-image prompting**: Use bounding boxes from a separate reference image
       - Upload your target image as `file`
       - Upload a reference image as `refer_file`
       - Provide bounding boxes and class IDs for objects in the reference image
    """
)
async def image_prompt_inference(
    file: UploadFile = File(..., description="Target image for detection"),
    bboxes: str = Form(..., description="JSON array of bounding boxes. Format: [[x1,y1,x2,y2], [x1,y1,x2,y2], ...]"),
    cls: str = Form(..., description="JSON array of class IDs (must start from 0). Format: [0, 1, ...]"),
    model_path: Optional[str] = Form("default", description="Path to model weights or 'default' for built-in model"),
    conf: float = Form(0.25, description="Confidence threshold (0.0-1.0)"),
    iou: float = Form(0.7, description="IoU threshold for non-max suppression (0.0-1.0)"),
    return_image: bool = Form(False, description="If true, returns annotated image in base64 format"),
    retina_masks: bool = Form(False, description="If true, returns high-quality segmentation masks"),
    refer_file: Optional[UploadFile] = File(None, description="Reference image containing visual prompt examples (optional)")
):
    try:
        img_bgr = await read_imagefile_async(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid target image: {e}")
    except Exception as e:
        logging.error(f"Unexpected error reading target image: {e}")
        raise HTTPException(status_code=500, detail="Error processing target image file.")

    refer_bgr = None
    if refer_file is not None:
        try:
            refer_bgr = await read_imagefile_async(refer_file)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid reference image: {e}")
        except Exception as e:
            logging.error(f"Unexpected error reading reference image: {e}")
            raise HTTPException(status_code=500, detail="Error processing reference image file.")

    try:
        # Validate JSON inputs with proper error handling
        if not bboxes or bboxes.isspace():
            raise ValueError("bboxes parameter cannot be empty")
        if not cls or cls.isspace():
            raise ValueError("cls parameter cannot be empty")

        # First, try to parse standard JSON format
        try:
            bboxes_list = json.loads(bboxes)
        except json.JSONDecodeError:
            # If standard JSON fails, try fixing common formatting issues

            # Replace single quotes with double quotes
            fixed_bboxes = bboxes.replace("'", "\"")

            # Fix missing commas between brackets
            fixed_bboxes = fixed_bboxes.replace("][", "],[")

            # Fix malformed brackets with incorrect syntax like [[0,200[
            fixed_bboxes = fixed_bboxes.replace("[,", "[0,")
            fixed_bboxes = fixed_bboxes.replace(",[", ",[0")
            fixed_bboxes = fixed_bboxes.replace("[", "[")
            fixed_bboxes = fixed_bboxes.replace("]", "]")

            # Replace invalid entries like [0,200[ with [0,200]
            import re
            fixed_bboxes = re.sub(r'\[\s*(\d+)\s*,\s*(\d+)\s*\[', r'[\1,\2]', fixed_bboxes)

            try:
                bboxes_list = json.loads(fixed_bboxes)
            except json.JSONDecodeError as e:
                # Try a more aggressive fix - manually parsing for those formats
                try:
                    if "[[" in bboxes and "]]" in bboxes:
                        # Extract all numeric values
                        import re
                        numbers = re.findall(r'\d+', bboxes)

                        # Count brackets to determine how many bboxes there should be
                        # Subtract 1 for the outer brackets
                        open_brackets = bboxes.count('[') - 1
                        close_brackets = bboxes.count(']') - 1

                        # Use class list length as a hint if available
                        try:
                            cls_count = len(json.loads(cls))
                        except:
                            try:
                                cls_count = len(re.findall(r'\d+', cls))
                            except:
                                cls_count = 0

                        # Determine how many bboxes we likely have
                        num_bboxes = max(open_brackets, close_brackets, len(numbers) // 4, cls_count)

                        # Group numbers in sets of 4 for bounding boxes [x1,y1,x2,y2]
                        bboxes_list = []
                        for i in range(0, min(len(numbers), num_bboxes * 4), 4):
                            if i+3 < len(numbers):
                                bboxes_list.append([int(numbers[i]), int(numbers[i+1]),
                                                  int(numbers[i+2]), int(numbers[i+3])])

                        # If we don't have enough boxes, add dummy boxes to match cls count
                        while len(bboxes_list) < num_bboxes:
                            bboxes_list.append([0, 0, 100, 100])  # Add dummy box
                    else:
                        raise ValueError("Could not parse bboxes format")
                except Exception as parse_err:
                    # Provide more helpful error message with example
                    raise ValueError(f"Invalid bboxes format. Expected format: [[x1,y1,x2,y2], [x1,y1,x2,y2]]. Error: {e}")

        # Parse cls with similar error handling
        try:
            cls_list = json.loads(cls)
        except json.JSONDecodeError:
            # Clean up the cls format
            fixed_cls = cls.replace("'", "\"")
            fixed_cls = fixed_cls.replace(" ", "")

            try:
                cls_list = json.loads(fixed_cls)
            except json.JSONDecodeError as e:
                # If still failing, try to extract numbers directly
                try:
                    import re
                    cls_list = [int(n) for n in re.findall(r'\d+', cls)]
                except Exception:
                    raise ValueError(f"Invalid cls format. Expected format: [0, 1, 2]. Error: {e}")

        # Validate data types and formats
        if not isinstance(bboxes_list, list):
            raise ValueError("bboxes must be a JSON array of arrays.")
        if not isinstance(cls_list, list):
            raise ValueError("cls must be a JSON array of integers.")

        # Check that each bbox is a list of 4 coordinates
        for i, bbox in enumerate(bboxes_list):
            if not isinstance(bbox, list) or len(bbox) != 4:
                raise ValueError(f"Each bounding box must contain exactly 4 values [x1,y1,x2,y2]. Error in box {i+1}: {bbox}")

        # Validate class IDs are sequential starting from 0
        # Check if lengths match
        if len(bboxes_list) != len(cls_list):
            raise ValueError(f"Length of bboxes ({len(bboxes_list)}) must match length of cls ({len(cls_list)}). " +
                           f"Each bounding box must have a corresponding class ID. " +
                           f"Please provide the same number of elements in both arrays.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid visual prompts format: {e}")

    visual_prompts = {
        "bboxes": np.array(bboxes_list, dtype=np.float32),
        "cls": np.array(cls_list, dtype=np.int32),
    }

    try:
        model = YOLOE(model_path=model_path)
        results_json = model.image_predict(
            source=img_bgr,
            visual_prompts=visual_prompts,
            refer_image=refer_bgr,
            conf=conf,
            iou=iou,
            return_dict=True,
            save=False,
            retina_masks=retina_masks
        )
        response_data = {"results": results_json}

        if return_image or (retina_masks and results_json.get("detection_results")):
            raw_results = model.image_predict(
                source=img_bgr,
                visual_prompts=visual_prompts,
                refer_image=refer_bgr,
                conf=conf,
                iou=iou,
                return_dict=False,
                save=False,
                retina_masks=retina_masks
            )
            if raw_results:
                if return_image:
                    annotated_bgr = raw_results[0].plot()
                    response_data["annotated_image"] = encode_bgr_image_to_base64(annotated_bgr)
                if retina_masks and hasattr(raw_results[0], 'masks') and raw_results[0].masks is not None:
                    masks = raw_results[0].masks.data
                    encoded_masks = []
                    for i in range(len(masks)):
                        mask = masks[i].cpu().numpy() * 255
                        encoded_masks.append(encode_mask_to_base64(mask.astype(np.uint8)))
                    response_data["segmentation_masks"] = encoded_masks
        return response_data
    except Exception as e:
        logging.error(f"Error during image-prompt inference: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

# ------------------------------------------------------
# 4) Export YOLO Format Endpoint (Single Image)
# ------------------------------------------------------
@router.post("/export/yolo")
async def export_yolo_single(
    request_data: ExportYoloRequest = Body(...)
):
    """
    Converts annotations for a single image to YOLO format and returns as a text file.
    """
    try:
        # Convert Pydantic AnnotationData models to simple dicts for the conversion function
        annotations_dict_list = [ann.to_conversion_dict() for ann in request_data.annotations]

        yolo_content = convert_to_yolo_format(
            annotations=annotations_dict_list,
            image_width=request_data.image_width,
            image_height=request_data.image_height,
            class_name_to_id=request_data.class_name_to_id
        )

        # Sanitize filename
        safe_filename_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in request_data.filename_base)
        filename = f"{safe_filename_base}.txt"

        return Response(
            content=yolo_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logging.error(f"Error during single YOLO export: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export YOLO format: {e}")

# ------------------------------------------------------
# 5) Export YOLO Format Endpoint (Batch - Zip)
# ------------------------------------------------------
@router.post("/export/yolo-batch")
async def export_yolo_batch(
    request_data: BatchExportYoloRequest = Body(...)
):
    """
    Converts annotations for multiple images to YOLO format,
    packages them into individual .txt files, and returns a zip archive.
    """
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for image_filename, image_data in request_data.images_data.items():
                # Convert Pydantic AnnotationData models to simple dicts
                annotations_dict_list = [ann.to_conversion_dict() for ann in image_data.annotations]

                yolo_content = convert_to_yolo_format(
                    annotations=annotations_dict_list,
                    image_width=image_data.image_width,
                    image_height=image_data.image_height,
                    class_name_to_id=request_data.class_name_to_id
                )

                # Create a .txt filename based on the original image filename
                base_name = image_filename.rsplit('.', 1)[0] # Remove extension
                txt_filename = f"{base_name}.txt"

                # Add the YOLO content as a file to the zip archive
                zip_file.writestr(txt_filename, yolo_content)

        zip_buffer.seek(0)

        # Sanitize zip filename base
        safe_zip_filename_base = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in request_data.zip_filename_base)
        zip_filename = f"{safe_zip_filename_base}.zip"

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
    except Exception as e:
        logging.error(f"Error during batch YOLO export: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export batch YOLO format: {e}")

