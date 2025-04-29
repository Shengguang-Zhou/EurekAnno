from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class VisualPromptData(BaseModel):
    """
    Pydantic model describing bounding boxes and their corresponding class IDs
    for image-prompted detection.
    """
    bboxes: List[List[float]] = Field(
        ...,
        description="List of bounding boxes, each as [x1, y1, x2, y2]."
    )
    cls: List[int] = Field(
        ...,
        description="List of class IDs, must match length of bboxes."
    )

class AnnotationData(BaseModel):
    """
    Represents a single annotation object as expected from the frontend.
    """
    id: Any
    x: float
    y: float
    width: float
    height: float
    category_name: Optional[str] = Field(None, alias='className') # Allow alias for frontend compatibility
    originalClass: Optional[str] = None
    userLabel: Optional[str] = None
    confidence: Optional[float] = None

    # Handle potential alias and prioritize user label
    def get_effective_category_name(self) -> Optional[str]:
        return self.userLabel or self.category_name or self.originalClass

    # Convert to dict suitable for conversion function
    def to_conversion_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "category_name": self.get_effective_category_name()
        }

class ExportYoloRequest(BaseModel):
    """
    Request body for single image YOLO export.
    """
    annotations: List[AnnotationData]
    image_width: int
    image_height: int
    class_name_to_id: Dict[str, int]
    filename_base: str = "annotations"

class BatchExportYoloRequestItem(BaseModel):
    """
    Data for a single image within a batch export request.
    """
    annotations: List[AnnotationData]
    image_width: int
    image_height: int

class BatchExportYoloRequest(BaseModel):
    """
    Request body for batch YOLO export.
    Key is the original image filename (used for the .txt filename).
    """
    images_data: Dict[str, BatchExportYoloRequestItem]
    class_name_to_id: Dict[str, int]
    zip_filename_base: str = "annotations_batch"