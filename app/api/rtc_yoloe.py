"""
Streaming inference endpoints for YOLOe using FastRTC.
"""
import json
import logging
from typing import List, Optional, AsyncGenerator

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, Query

from app.utils.tools import encode_bgr_image_to_base64

# Attempt to import the actual YOLOE implementation
try:
    from app.cv.inference.yolo.yoloe import YOLOE
except ImportError:  # pragma: no cover - fallback for missing dependency
    logging.warning("YOLOE class not found, streaming endpoints will be no-op.")

    class YOLOE:
        def __init__(self, *_, **__):
            pass

        def prompt_free_predict(self, source, **_):
            return {}

        def text_predict(self, source, class_names, **_):
            return {}

        def image_predict(self, source, visual_prompts, refer_image=None, **_):
            return {}

# Try to import FastRTC from gradio
try:
    from fastrtc.fastapi import FastRTCEndpoint
except Exception:  # pragma: no cover - fallback stub
    class FastRTCEndpoint:
        async def stream(self, websocket: WebSocket, generator: AsyncGenerator):
            await websocket.accept()
            async for data in generator:
                await websocket.send_json(data)
            await websocket.close()

rtc = FastRTCEndpoint()
router = APIRouter()


async def _frame_generator(
    source: str,
    mode: str,
    class_names: Optional[List[str]] = None,
    bboxes: Optional[List[List[float]]] = None,
    cls: Optional[List[int]] = None,
    refer_image: Optional[np.ndarray] = None,
) -> AsyncGenerator[dict, None]:
    cap_source = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(cap_source)
    model = YOLOE()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if mode == "prompt-free":
                result_json = model.prompt_free_predict(frame, return_dict=True, save=False)
                raw_results = model.prompt_free_predict(frame, return_dict=False, save=False)
            elif mode == "text-prompt":
                result_json = model.text_predict(frame, class_names=class_names or [], return_dict=True, save=False)
                raw_results = model.text_predict(frame, class_names=class_names or [], return_dict=False, save=False)
            elif mode == "image-prompt":
                prompts = {"bboxes": np.array(bboxes or []), "cls": np.array(cls or [])}
                result_json = model.image_predict(frame, visual_prompts=prompts, refer_image=refer_image, return_dict=True, save=False)
                raw_results = model.image_predict(frame, visual_prompts=prompts, refer_image=refer_image, return_dict=False, save=False)
            else:
                result_json = {}
                raw_results = []

            annotated = frame
            if raw_results:
                annotated = raw_results[0].plot()
            encoded = encode_bgr_image_to_base64(annotated)
            yield {"results": result_json, "annotated_image": encoded}
    finally:
        cap.release()


@router.websocket("/prompt-free")
async def ws_prompt_free(
    websocket: WebSocket,
    source: str = Query("0", description="Camera index or RTSP URL"),
):
    """Stream prompt-free detection results via FastRTC/WebSocket."""
    gen = _frame_generator(source=source, mode="prompt-free")
    await rtc.stream(websocket, gen)


@router.websocket("/text-prompt")
async def ws_text_prompt(
    websocket: WebSocket,
    class_names: str = Query("[]", description="JSON list of class names"),
    source: str = Query("0", description="Camera index or RTSP URL"),
):
    try:
        names = json.loads(class_names)
    except json.JSONDecodeError:
        names = []
    gen = _frame_generator(source=source, mode="text-prompt", class_names=names)
    await rtc.stream(websocket, gen)


@router.websocket("/image-prompt")
async def ws_image_prompt(
    websocket: WebSocket,
    bboxes: str = Query("[]", description="JSON list of bounding boxes"),
    cls: str = Query("[]", description="JSON list of class IDs"),
    source: str = Query("0", description="Camera index or RTSP URL"),
):
    try:
        boxes = json.loads(bboxes)
    except json.JSONDecodeError:
        boxes = []
    try:
        cls_list = json.loads(cls)
    except json.JSONDecodeError:
        cls_list = []
    gen = _frame_generator(
        source=source,
        mode="image-prompt",
        bboxes=boxes,
        cls=cls_list,
    )
    await rtc.stream(websocket, gen)

