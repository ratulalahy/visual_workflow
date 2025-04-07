from pydantic import BaseModel, Field, field_validator, model_validator # Import new decorators
from typing import List, Optional, Dict, Any

# Coordinates class remains the same as it has no validators
class Coordinates(BaseModel):
    """Represents a point on the screen."""
    x: int = Field(..., description="X-coordinate")
    y: int = Field(..., description="Y-coordinate")

class BoundingBox(BaseModel):
    """
    Represents a rectangular area on the screen, typically identified by a VLM.
    Coordinates represent [x_min, y_min, x_max, y_max].
    """
    x_min: int = Field(..., description="Minimum X-coordinate (top-left)")
    y_min: int = Field(..., description="Minimum Y-coordinate (top-left)")
    x_max: int = Field(..., description="Maximum X-coordinate (bottom-right)")
    y_max: int = Field(..., description="Maximum Y-coordinate (bottom-right)")

    # Replaces @validator('*')
    @field_validator('x_min', 'y_min', 'x_max', 'y_max')
    @classmethod # Keep as classmethod if you need cls, otherwise instance method is fine
    def coords_must_be_positive(cls, v: int):
        """Validate that coordinates are non-negative."""
        if v < 0:
            # Use PydanticCustomError or just raise ValueError
            raise ValueError('Bounding box coordinates must be non-negative')
        return v

    # Replaces interdependent @validator('x_max') and @validator('y_max')
    # Use model_validator for checks involving multiple fields
    @model_validator(mode='after') # 'after' runs after individual field validation
    def check_min_max_order(self) -> 'BoundingBox':
        """Validate that max coordinates are strictly greater than min coordinates."""
        if self.x_max <= self.x_min:
            raise ValueError('x_max must be strictly greater than x_min')
        if self.y_max <= self.y_min:
            raise ValueError('y_max must be strictly greater than y_min')
        # Must return the model instance (self) for mode='after'
        return self

    def calculate_center(self) -> Coordinates:
        """Calculates the center point of the bounding box."""
        center_x = self.x_min + (self.x_max - self.x_min) // 2
        center_y = self.y_min + (self.y_max - self.y_min) // 2
        return Coordinates(x=center_x, y=center_y)

    @classmethod
    def from_list(cls, coords: List[int]) -> 'BoundingBox':
        """Creates a BoundingBox from a list [x_min, y_min, x_max, y_max]."""
        if len(coords) != 4:
            raise ValueError("List must contain exactly four coordinate values.")
        # Validation will run automatically when cls() is called
        return cls(x_min=coords[0], y_min=coords[1], x_max=coords[2], y_max=coords[3])


# VLMAnalysisResult remains the same as it has no validators defined here
class VLMAnalysisResult(BaseModel):
    """
    Represents the structured result from a VLM analysis.
    This is a flexible model; specific fields depend on the VLM output and the prompt.
    """
    found_elements: List[Dict[str, Any]] = Field(default_factory=list, description="List of identified elements with details (text, bbox, type)")
    main_text_content: Optional[str] = Field(None, description="Extracted main text (e.g., OCR)")
    identified_element_bbox: Optional[BoundingBox] = Field(None, description="Bounding box of a specifically requested element")
    verification_passed: Optional[bool] = Field(None, description="Result of a verification prompt (e.g., 'Is X visible?')")
    raw_output: Dict[str, Any] = Field(..., description="The raw dictionary output from the VLM service")
    
    # Example of how add specific parsing might be later:
    # def get_bounding_box_for_text(self, text: str) -> Optional[BoundingBox]:
    #     for element in self.found_elements:
    #         if element.get("text") == text and "bounding_box" in element:
    #             try:
    #                 # Assuming bbox is stored as list [xmin, ymin, xmax, ymax]
    #                 return BoundingBox.from_list(element["bounding_box"])
    #             except (ValueError, TypeError):
    #                 # Log error or handle malformed data
    #                 pass
    #     return None