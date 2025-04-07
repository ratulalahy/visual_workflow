import pytest
from assistant.models.common import Coordinates, BoundingBox, VLMAnalysisResult
# from ..models.common import Coordinates, BoundingBox, VLMAnalysisResult
from typing import List, Dict, Any


def test_coordinates_creation():
    coords = Coordinates(x=10, y=20)
    assert coords.x == 10
    assert coords.y == 20


def test_bounding_box_creation():
    bbox = BoundingBox(x_min=10, y_min=20, x_max=30, y_max=40)
    assert bbox.x_min == 10
    assert bbox.y_min == 20
    assert bbox.x_max == 30
    assert bbox.y_max == 40


def test_bounding_box_coords_must_be_positive():
    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=-1, y_min=20, x_max=30, y_max=40)
    assert "Bounding box coordinates must be non-negative" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=10, y_min=-20, x_max=30, y_max=40)
    assert "Bounding box coordinates must be non-negative" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=10, y_min=20, x_max=-30, y_max=40)
    assert "Bounding box coordinates must be non-negative" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=10, y_min=20, x_max=30, y_max=-40)
    assert "Bounding box coordinates must be non-negative" in str(exc_info.value)


def test_bounding_box_x_max_must_be_greater_than_x_min():
    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=30, y_min=20, x_max=30, y_max=40)
    assert "x_max must be strictly greater than x_min" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=40, y_min=20, x_max=30, y_max=40)
    assert "x_max must be strictly greater than x_min" in str(exc_info.value)


def test_bounding_box_y_max_must_be_greater_than_y_min():
    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=10, y_min=40, x_max=30, y_max=40)
    assert "y_max must be strictly greater than y_min" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        BoundingBox(x_min=10, y_min=50, x_max=30, y_max=40)
    assert "y_max must be strictly greater than y_min" in str(exc_info.value)


def test_bounding_box_calculate_center():
    bbox = BoundingBox(x_min=10, y_min=20, x_max=30, y_max=40)
    center = bbox.calculate_center()
    assert center.x == 20
    assert center.y == 30

    bbox = BoundingBox(x_min=0, y_min=0, x_max=100, y_max=200)
    center = bbox.calculate_center()
    assert center.x == 50
    assert center.y == 100


def test_bounding_box_from_list():
    bbox = BoundingBox.from_list([10, 20, 30, 40])
    assert bbox.x_min == 10
    assert bbox.y_min == 20
    assert bbox.x_max == 30
    assert bbox.y_max == 40


def test_bounding_box_from_list_invalid_length():
    with pytest.raises(ValueError) as exc_info:
        BoundingBox.from_list([10, 20, 30])
    assert "List must contain exactly four coordinate values." in str(exc_info.value)


def test_vlm_analysis_result_creation():
    raw_output: Dict[str, Any] = {"key": "value"}
    vlm_result = VLMAnalysisResult(raw_output=raw_output)
    assert vlm_result.raw_output == raw_output
    assert vlm_result.found_elements == []
    assert vlm_result.main_text_content is None
    assert vlm_result.identified_element_bbox is None
    assert vlm_result.verification_passed is None


def test_vlm_analysis_result_with_data():
    raw_output: Dict[str, Any] = {"key": "value"}
    found_elements: List[Dict[str, Any]] = [{"text": "element1", "bbox": [1, 2, 3, 4]}]
    bbox = BoundingBox(x_min=10, y_min=20, x_max=30, y_max=40)
    vlm_result = VLMAnalysisResult(
        raw_output=raw_output,
        found_elements=found_elements,
        main_text_content="Main Text",
        identified_element_bbox=bbox,
        verification_passed=True,
    )
    assert vlm_result.raw_output == raw_output
    assert vlm_result.found_elements == found_elements
    assert vlm_result.main_text_content == "Main Text"
    assert vlm_result.identified_element_bbox == bbox
    assert vlm_result.verification_passed is True
