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
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Body
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.models.yoloe import BatchExportYoloRequest, ExportYoloRequest
from app.utils.tools import read_imagefile, encode_mask_to_base64, encode_bgr_image_to_base64

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
        img_bgr = read_imagefile(file)
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
        img_bgr = read_imagefile(file)
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

@router.post("/image-prompt")
async def image_prompt_inference(
    file: UploadFile = File(...),
    bboxes: str = Form(...), # Receive as JSON string
    cls: str = Form(...),    # Receive as JSON string
    model_path: Optional[str] = Form("default"),
    conf: float = Form(0.25),
    iou: float = Form(0.7),
    return_image: bool = Form(False),
    retina_masks: bool = Form(False),
    refer_file: Optional[UploadFile] = File(default=None)
):
    try:
        img_bgr = read_imagefile(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid target image: {e}")
    except Exception as e:
        logging.error(f"Unexpected error reading target image: {e}")
        raise HTTPException(status_code=500, detail="Error processing target image file.")

    refer_bgr = None
    if refer_file is not None:
        try:
            refer_bgr = read_imagefile(refer_file)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid reference image: {e}")
        except Exception as e:
            logging.error(f"Unexpected error reading reference image: {e}")
            raise HTTPException(status_code=500, detail="Error processing reference image file.")

    try:
        # Validate JSON inputs with proper error handling for empty strings
        if not bboxes or bboxes.isspace():
            raise ValueError("bboxes parameter cannot be empty")
        if not cls or cls.isspace():
            raise ValueError("cls parameter cannot be empty")
            
        bboxes_list = json.loads(bboxes)
        cls_list = json.loads(cls)
        
        if not isinstance(bboxes_list, list) or not isinstance(cls_list, list):
            raise ValueError("bboxes and cls must be JSON arrays.")
        if len(bboxes_list) != len(cls_list):
            raise ValueError("Length of bboxes must match length of cls.")
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

