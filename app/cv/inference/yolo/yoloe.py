import os
import sys
import cv2
import numpy as np
from typing import List, Union, Optional, Dict, Any

from ultralytics import YOLO
from ultralytics.models.yolo.yoloe import YOLOEVPSegPredictor

# Import config
try:
    from app.config import config
    # Get model paths from config
    YOLOE_SEG_PATH = config.get_yoloe_seg_path()
    YOLOE_SEG_PF_PATH = config.get_yoloe_seg_pf_path()
    
    # Check if paths are provided and valid
    if not YOLOE_SEG_PATH or not os.path.exists(YOLOE_SEG_PATH):
        print(f"Warning: YOLOE-SEG model path not found or invalid: {YOLOE_SEG_PATH}. Using default.")
        YOLOE_SEG_PATH = "yoloe-11s-seg.pt"
        
    if not YOLOE_SEG_PF_PATH or not os.path.exists(YOLOE_SEG_PF_PATH):
        print(f"Warning: YOLOE-SEG-PF model path not found or invalid: {YOLOE_SEG_PF_PATH}. Using default.")
        YOLOE_SEG_PF_PATH = "yoloe-11l-seg-pf.pt"
        
except ImportError:
    print("Warning: Could not import configuration. Using default model paths.")
    YOLOE_SEG_PATH = "yoloe-11s-seg.pt"
    YOLOE_SEG_PF_PATH = "yoloe-11l-seg-pf.pt"


class YOLOE:
    """
    A high-level OOP wrapper around the Ultralytics YOLOE models.

    This class supports:
      1) **Prompt-free** detection (using a built-in vocabulary of ~4,585 classes).
      2) **Text-prompted** detection (use your own class labels).
      3) **Image-prompted** detection (provide bounding boxes with example visual prompts).
      4) Batch processing (predicting on multiple images at once).

    It returns predictions as a dictionary in the following structure:

    .. code-block:: python

        {
            "class": ["cat", "dog", ...],
            "confidence": [0.98, 0.65, ...],
            "bbox": [
                [x1, y1, x2, y2],
                [x1, y1, x2, y2],
                ...
            ],
            "masks": [
                [ [x1,y1], [x2,y2], ... ],
                ...
            ]
        }

    Usage Example
    =============

    .. code-block:: python

        from yoloe_wrapper import YOLOE

        # 1) Prompt-free example
        model = YOLOE()
        result_json = model.predict("path/to/image.jpg")
        print(result_json)
        
        # 2) Text-prompted example
        model = YOLOE()
        result_json = model.text_predict(
            "path/to/image.jpg",
            class_names=["person", "hat", "backpack"]
        )
        print(result_json)

        # 3) Image-prompted example
        prompts = dict(
            bboxes=np.array([[100, 200, 150, 300]]),
            cls=np.array([0])
        )
        model = YOLOE()
        result_json = model.image_predict(
            "path/to/image.jpg",
            visual_prompts=prompts
        )
        print(result_json)
    """

    def __init__(self, model_path: str = "default"):
        """
        Initializes a YOLOE model.
        
        Args:
            model_path (str):
                Path to the YOLOE model weights (e.g. "yoloe-11s-seg.pt") or
                "default" to use our mode-switching logic with default
                models for prompt-free vs. text/image-prompted modes.
        """
        self.current_mode = "prompt-free"
        self.class_names: Optional[List[str]] = None
        self.embeddings: Optional[np.ndarray] = None

        if model_path == "default":
            # Keep self.model_path as 'default' but load the correct
            # "prompt-free" model for initial usage.
            initial_path = self._get_default_model_path()
            self.model = YOLO(initial_path)
            self.model_path = "default"
        else:
            # Load a custom or user-specified model path
            self.model = YOLO(model_path)
            self.model_path = model_path

    def _get_default_model_path(self) -> str:
        """
        Returns the default model path based on the current mode.

        * 'prompt-free' mode uses a larger RAM++ vocabulary model.
        * 'text-prompted' or 'image-prompted' uses the standard YOLOE model.

        Modify these paths to your absolute paths if needed.
        """
        if self.current_mode == "prompt-free":
            return YOLOE_SEG_PF_PATH
        else:
            return YOLOE_SEG_PATH

    def _switch_to_mode(self, mode: str) -> None:
        """
        Switches internal mode and updates the underlying model if necessary
        (only if model_path was 'default').
        
        Args:
            mode (str): One of ["prompt-free", "text-prompted", "image-prompted"].
        """
        previous_mode = self.current_mode
        self.current_mode = mode

        if self.model_path == "default":
            # If we are switching between prompt-free and a prompted mode,
            # reload the corresponding default model.
            if previous_mode == "prompt-free" and mode in ["text-prompted", "image-prompted"]:
                self.model = YOLO(self._get_default_model_path())
            elif previous_mode in ["text-prompted", "image-prompted"] and mode == "prompt-free":
                self.model = YOLO(self._get_default_model_path())

    def _preprocess_source(self, source: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Preprocesses the `source` (image path or list of image paths) for YOLO inference.
        
        Args:
            source (Union[str, List[str]]): file path or list of file paths.
            
        Returns:
            (Union[str, List[str]]): The same input or a processed variant (if needed).
        """
        if isinstance(source, list):
            return source
        return source  # Single path as-is
        
    def _convert_results_to_summary_dict(self, results: List[Any]) -> Dict[str, List[Any]]:
        """
        Converts Ultralytics 'Results' objects into a single dictionary:
            {
                "class": [...],
                "confidence": [...],
                "bbox": [...],
                "masks": [...]
            }
        
        Args:
            results (List[Any]): A list of Ultralytics Results objects.
            
        Returns:
            Dict[str, List[Any]]: A single dict merging all detections from
                                   all images into four lists (class, conf, bbox, masks).
        """
        summary = {
            "class": [],
            "confidence": [],
            "bbox": [],
            "masks": [],
        }

        # Each 'Results' object in `results` corresponds to a single image
        for res in results:
            # If there are bounding boxes:
            if res.boxes is not None and len(res.boxes) > 0:
                class_ids = res.boxes.cls.cpu().numpy().astype(int)
                confidences = res.boxes.conf.cpu().numpy()
                bboxes = res.boxes.xyxy.cpu().numpy()
                
                # If there are masks (segmentation):
                mask_xy = None
                if res.masks is not None:
                    mask_xy = res.masks.xy  # list of arrays

                for i, class_id in enumerate(class_ids):
                    # Class name
                    if hasattr(res, "names") and res.names is not None and class_id in res.names:
                        class_name = res.names[class_id]
                    else:
                        class_name = f"class_{class_id}"
                    
                    summary["class"].append(class_name)
                    summary["confidence"].append(float(confidences[i]))
                    summary["bbox"].append(bboxes[i].tolist())
                    
                    # If segmentation mask is present, store it
                    if mask_xy is not None and i < len(mask_xy):
                        # mask_xy[i] is an Nx2 array of polygon points
                        summary["masks"].append(mask_xy[i].tolist())
                    else:
                        summary["masks"].append(None)

        return summary

    def reset_to_prompt_free(self) -> None:
        """
        Resets the model to 'prompt-free' mode and reloads the default
        prompt-free model if model_path=='default'.
        """
        self._switch_to_mode("prompt-free")
        # Clear text/embedding references
        self.class_names = None
        self.embeddings = None

    def set_classes(self, class_names: List[str]) -> None:
        """
        Sets the model to 'text-prompted' mode, with the given text class prompts.

        Args:
            class_names (List[str]): A list of class strings to detect.
        """
        self._switch_to_mode("text-prompted")
        # Get embeddings for the new text prompts
        self.class_names = class_names
        self.embeddings = self.model.get_text_pe(class_names)
        self.model.set_classes(class_names, self.embeddings)

    def predict(
        self,
        source: Union[str, List[str]],
        conf: float = 0.25,
        iou: float = 0.7,
        save: bool = False,
        save_dir: Optional[str] = None,
        mode: Optional[str] = None,
        prompt: Optional[Union[List[str], Dict[str, np.ndarray]]] = None,
        refer_image: Optional[Union[str, np.ndarray]] = None,
        return_dict: bool = True,
        **kwargs
    ) -> Union[Dict[str, List[Any]], List[Any]]:
        """
        Runs inference on the given image(s), with optional prompts and mode-switching.
        
        Args:
            source: File path or list of file paths to images.
            conf: Confidence threshold (0.0-1.0).
            iou: IoU threshold for non-max suppression (0.0-1.0).
            save: Whether to save annotated outputs to disk.
            save_dir: Directory in which to save outputs if save=True.
            mode: Override detection mode: "prompt-free", "text-prompted", or "image-prompted".
            prompt: If mode="text-prompted", a list of class strings; if mode="image-prompted",
                    a dict with "bboxes" and "cls".
            refer_image: If mode="image-prompted" with external reference, pass
                         that reference image path/array here.
            return_dict: If True, returns a JSON-compatible dictionary summarizing
                         **all** detections. Otherwise returns the raw Results list.
            **kwargs: Other valid arguments for Ultralytics model.predict().
            
        Returns:
            If return_dict=True -> A single dictionary with "class", "confidence",
                                   "bbox", "masks" arrays.
            Otherwise -> A list of Ultralytics 'Results' objects (one per image).
        """
        # Optionally switch detection mode
        if mode is not None:
            self._switch_to_mode(mode)
            # Handle prompt specifics
            if mode == "prompt-free":
                self.class_names = None
                self.embeddings = None
            elif mode == "text-prompted":
                if prompt is None or not isinstance(prompt, list):
                    raise ValueError("For text-prompted mode, prompt must be a list of class strings.")
                # Set classes for text mode
                self.class_names = prompt
                self.embeddings = self.model.get_text_pe(prompt)
                self.model.set_classes(prompt, self.embeddings)
            elif mode == "image-prompted":
                if not (isinstance(prompt, dict) and "bboxes" in prompt and "cls" in prompt):
                    raise ValueError("For image-prompted mode, prompt must be a dict with 'bboxes' & 'cls'.")
                kwargs["visual_prompts"] = prompt
                kwargs["predictor"] = YOLOEVPSegPredictor
                if refer_image is not None:
                    kwargs["refer_image"] = refer_image

        # Preprocess input source
        processed_source = self._preprocess_source(source)
            
        # Configure save folder if needed
        if save_dir is not None:
            kwargs["project"] = os.path.dirname(save_dir)
            kwargs["name"] = os.path.basename(save_dir)
        
        # Run inference
        results = self.model.predict(
            source=processed_source,
            conf=conf,
            iou=iou,
            save=save,
            **kwargs
        )
        
        # Return results in desired format
        if return_dict:
            return self._convert_results_to_summary_dict(results)
        else:
            return results
    
    def prompt_free_predict(
        self,
        source: Union[str, List[str]],
        conf: float = 0.25,
        iou: float = 0.7,
        save: bool = False,
        save_dir: Optional[str] = None,
        return_dict: bool = True,
        **kwargs
    ) -> Union[Dict[str, List[Any]], List[Any]]:
        """
        Runs inference in 'prompt-free' mode (uses built-in 4k+ label vocabulary).

        Args:
            source: File path or list of file paths to images.
            conf: Confidence threshold.
            iou: IoU threshold for non-max suppression.
            save: Whether to save annotated outputs to disk.
            save_dir: Directory in which to save outputs (if save=True).
            return_dict: If True, returns a JSON-compatible summary dict of results.
            **kwargs: Additional predict() arguments.

        Returns:
            Dict or list of Ultralytics Results objects, depending on `return_dict`.
        """
        self.reset_to_prompt_free()
        return self.predict(
            source=source,
            conf=conf,
            iou=iou,
            save=save,
            save_dir=save_dir,
            return_dict=return_dict,
            mode="prompt-free",
            **kwargs
        )

    def text_predict(
        self,
        source: Union[str, List[str]],
        class_names: List[str],
        conf: float = 0.25,
        iou: float = 0.7, 
        save: bool = False,
        save_dir: Optional[str] = None,
        return_dict: bool = True,
        **kwargs
    ) -> Union[Dict[str, List[Any]], List[Any]]:
        """
        Runs inference in 'text-prompted' mode with user-specified class names.
        
        Args:
            source: File path or list of file paths to images.
            class_names: List of class names for detection.
            conf: Confidence threshold.
            iou: IoU threshold for non-max suppression.
            save: Whether to save annotated outputs to disk.
            save_dir: Directory in which to save outputs (if save=True).
            return_dict: If True, returns a JSON-compatible summary dict of results.
            **kwargs: Additional predict() arguments.
            
        Returns:
            Dict or list of Ultralytics Results objects, depending on `return_dict`.
        """
        # Switch to text-prompted and set classes
        self._switch_to_mode("text-prompted")
        self.class_names = class_names
        self.embeddings = self.model.get_text_pe(class_names)
        self.model.set_classes(class_names, self.embeddings)

        return self.predict(
            source=source,
            conf=conf,
            iou=iou,
            save=save,
            save_dir=save_dir,
            return_dict=return_dict,
            mode="text-prompted",
            prompt=class_names,
            **kwargs
        )
    
    def image_predict(
        self,
        source: Union[str, List[str]],
        visual_prompts: Dict[str, Union[np.ndarray, List[np.ndarray]]],
        refer_image: Optional[Union[str, np.ndarray]] = None,
        conf: float = 0.25,
        iou: float = 0.7,
        save: bool = False,
        save_dir: Optional[str] = None,
        return_dict: bool = True,
        **kwargs
    ) -> Union[Dict[str, List[Any]], List[Any]]:
        """
        Runs inference in 'image-prompted' mode with bounding boxes from a reference.
        
        Args:
            source: File path or list of file paths to images (the target(s) for detection).
            visual_prompts: Dict with:
                - "bboxes": np.ndarray (N x 4) bounding box coords
                - "cls": np.ndarray (N,) class IDs for each box
            refer_image: Optional reference image for bounding boxes (if they are from a separate image).
            conf: Confidence threshold.
            iou: IoU threshold for non-max suppression.
            save: Whether to save annotated outputs to disk.
            save_dir: Directory in which to save outputs (if save=True).
            return_dict: If True, returns a JSON-compatible summary dict of results.
            **kwargs: Additional predict() arguments.
            
        Returns:
            Dict or list of Ultralytics Results objects, depending on `return_dict`.
        """
        self._switch_to_mode("image-prompted")

        if not isinstance(visual_prompts, dict) or "bboxes" not in visual_prompts or "cls" not in visual_prompts:
            raise ValueError("`visual_prompts` must be a dict containing 'bboxes' and 'cls' keys.")
        
        # Forward to our main predict method
        return self.predict(
            source=source,
            conf=conf,
            iou=iou,
            save=save,
            save_dir=save_dir,
            return_dict=return_dict,
            mode="image-prompted",
            prompt=visual_prompts,
            refer_image=refer_image,
            **kwargs
        )
    
    def batch_predict(
        self,
        sources: List[str],
        mode: str = "prompt-free",
        prompts: Optional[Union[List[str], Dict[str, Union[np.ndarray, List[np.ndarray]]]]] = None,
        refer_image: Optional[Union[str, np.ndarray]] = None,
        conf: float = 0.25,
        iou: float = 0.7,
        save: bool = False,
        save_dir: Optional[str] = None,
        return_dict: bool = True,
        **kwargs
    ) -> Union[Dict[str, List[Any]], List[Any]]:
        """
        Runs batch prediction on a list of images with the specified mode and prompts.
        
        Args:
            sources: List of image paths.
            mode: "prompt-free", "text-prompted", or "image-prompted".
            prompts: If 'text-prompted', a list of class strings; if 'image-prompted',
                     a dict with 'bboxes' & 'cls'.
            refer_image: Optional reference for image-prompted mode.
            conf: Confidence threshold.
            iou: IoU threshold for non-max suppression.
            save: Whether to save annotated outputs to disk.
            save_dir: Directory in which to save outputs (if save=True).
            return_dict: If True, returns a JSON-compatible summary dict of results.
            **kwargs: Additional predict() arguments.
            
        Returns:
            Dict or list of Ultralytics Results objects, depending on `return_dict`.
        """
        if mode == "prompt-free":
            return self.prompt_free_predict(
                sources,
                conf=conf,
                iou=iou,
                save=save,
                save_dir=save_dir,
                return_dict=return_dict,
                **kwargs
            )
        elif mode == "text-prompted":
            if not (isinstance(prompts, list) and all(isinstance(x, str) for x in prompts)):
                raise ValueError("For text-prompted mode, `prompts` must be a list of strings.")
            return self.text_predict(
                sources,
                class_names=prompts,
                conf=conf,
                iou=iou,
                save=save,
                save_dir=save_dir,
                return_dict=return_dict,
                **kwargs
            )
        elif mode == "image-prompted":
            if not (isinstance(prompts, dict) and "bboxes" in prompts and "cls" in prompts):
                raise ValueError("For image-prompted mode, `prompts` must be a dict with 'bboxes' and 'cls'.")
            return self.image_predict(
                sources,
                visual_prompts=prompts,
                refer_image=refer_image,
                conf=conf,
                iou=iou,
                save=save,
                save_dir=save_dir,
                return_dict=return_dict,
                **kwargs
            )
        else:
            raise ValueError(
                f"Unknown mode '{mode}'. Must be one of: 'prompt-free', 'text-prompted', 'image-prompted'."
            )

    def visualize(
        self,
        results: List[Any], 
        index: int = 0,
        save: bool = False, 
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Visualizes the detection result for a given index in the results list.
        
        Args:
            results (List[Any]): List of Ultralytics Results objects.
            index (int): Which result index to plot (for batch predictions).
            save (bool): Whether to save the annotated image.
            save_path (str): Optional path to save the annotated image.
            
        Returns:
            np.ndarray: The annotated image in BGR format (OpenCV style).
        """
        if not 0 <= index < len(results):
            raise IndexError(f"Index {index} out of range for results (length {len(results)}).")

        plot_image = results[index].plot()

        if save:
            if save_path is None:
                os.makedirs("./runs/detect", exist_ok=True)
                save_path = os.path.join("./runs/detect", f"result_{index}.jpg")
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            cv2.imwrite(save_path, plot_image)
        
        return plot_image
    

# ---------------------------------------------------------------------------- #
# Example usage and quick tests
# ---------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Replace these with your local image paths or absolute paths.
    TEST_IMAGE_PATH = "/home/a/PycharmProjects/EurekAnno/dataset/examples/boys.jpeg"
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Test image not found at {TEST_IMAGE_PATH}")
        sys.exit(1)
    
    # Create output directories
    os.makedirs("./test_results", exist_ok=True)
    
    print("=== Testing YOLOE Model with Config-Based Model Paths ===")
    print(f"Using YOLOE-SEG path: {YOLOE_SEG_PATH}")
    print(f"Using YOLOE-SEG-PF path: {YOLOE_SEG_PF_PATH}")
    
    model = YOLOE()  # Will use YOLOE_SEG_PF_PATH by default for prompt-free

    # 1) Prompt-free prediction
    print("\n1) Prompt-free prediction with a single image:")
    result_json = model.predict(TEST_IMAGE_PATH, save=True, save_dir="./test_results")
    print("Result JSON keys:", result_json.keys())
    print("Classes:", result_json["class"])
    print("Confidences:", result_json["confidence"])
    
    # 2) Text-prompted prediction
    print("\n2) Text-prompted prediction with class names:")
    text_prompts = ["person", "backpack", "hat"]

    # We re-init a fresh YOLOE to replicate a separate usage scenario
    model = YOLOE()
    result_json = model.text_predict(
        TEST_IMAGE_PATH,
        class_names=text_prompts,
        save=True, 
        save_dir="./test_results/text_prompted",
    )
    print("Text-prompted result JSON keys:", result_json.keys())
    print("Classes:", result_json["class"])
    print("Confidences:", result_json["confidence"])

    # 3) Switch back to prompt-free mode
    print("\n3) Switching back to prompt-free mode:")
    model.reset_to_prompt_free()
    result_json = model.predict(TEST_IMAGE_PATH, save=True, save_dir="./test_results/after_reset")
    print("Prompt-free result JSON keys:", result_json.keys())
    print("Classes:", result_json["class"])

    print("\nAll tests completed successfully!")
