from pydantic import BaseModel, Field
from typing import Union, Literal, Optional, List


class BaseAction(BaseModel):
    reason: Optional[str] = None


class ClickAction(BaseAction):
    action: Literal["CLICK"] = "CLICK"
    x: Optional[int] = None
    y: Optional[int] = None
    description: Optional[str] = None  # For VLM lookup later
    # Add button, clicks etc. if needed


class TypeTextAction(BaseAction):
    action: Literal["TYPE_TEXT"] = "TYPE_TEXT"
    text: str
    interval: float = 0.01  # Default interval


class OpenApplicationAction(BaseAction):
    action: Literal["OPEN_APPLICATION"] = "OPEN_APPLICATION"
    application_name: str


class NavigateWebsiteAction(BaseAction):
    action: Literal["NAVIGATE_TO_WEBSITE"] = "NAVIGATE_TO_WEBSITE"
    url: str


class TakeScreenshotAction(BaseAction):
    action: Literal["TAKE_SCREENSHOT"] = "TAKE_SCREENSHOT"


class AnalyzeScreenshotAction(BaseAction):
    action: Literal["ANALYZE_SCREENSHOT"] = "ANALYZE_SCREENSHOT"
    prompt: str

class WaitAction(BaseAction):
    action: Literal["WAIT"] = "WAIT"
    duration_ms: int = Field(default=1000, ge=0, description="Duration to wait in milliseconds")

class PressKeyAction(BaseAction):
    action: Literal["PRESS_KEY"] = "PRESS_KEY"
    # Consider adding validation for common keys if desired,
    # but the controller handles basic validation against pyautogui keys
    key_name: str = Field(..., description="Name of the key to press (e.g., 'enter', 'f5', 'ctrl')")

class FindAppAction(BaseAction):
    action: Literal["FIND_APP"] = "FIND_APP"
    # This is mostly conceptual for the LLM plan
    app_name: str = Field(..., description="Name of the application the LLM is trying to locate")

class DoubleClickAction(BaseAction):
    action: Literal["DOUBLE_CLICK"] = "DOUBLE_CLICK"
    x: Optional[int] = None
    y: Optional[int] = None
    description: Optional[str] = None # Optional description for VLM lookup

class MoveMouseAction(BaseAction):
    action: Literal["MOVE_MOUSE"] = "MOVE_MOUSE"
    x: int
    y: int
    duration: float = Field(default=0.2, ge=0, description="Time in seconds for the mouse move animation")


class TaskCompleteAction(BaseAction):
    action: Literal["TASK_COMPLETE"] = "TASK_COMPLETE"
    message: Optional[str] = None
    success: Literal[True] = True


class TaskFailedAction(BaseAction):
    action: Literal["TASK_FAILED"] = "TASK_FAILED"
    message: Optional[str] = None
    success: Literal[False] = False


class ScrollAction(BaseAction):
    action: Literal["SCROLL"] = "SCROLL"
    direction: Literal["up", "down", "left", "right"]
    # Optional: amount/magnitude (e.g., number of lines/pixels, depends on controller)
    amount: int = Field(
        default=10, description="Magnitude of scroll (lines/pixels)")  # Example default


# Discriminated Union - Pydantic uses the 'action' field to determine the type
AnyAction = Union[
    ClickAction,
    DoubleClickAction, 
    TypeTextAction,
    OpenApplicationAction,
    NavigateWebsiteAction,
    TakeScreenshotAction,
    AnalyzeScreenshotAction,
    PressKeyAction,    
    WaitAction, 
    FindAppAction,
    ScrollAction,
    MoveMouseAction, 
    TaskCompleteAction,
    TaskFailedAction,
]

# The Plan from LLM 
class Plan(BaseModel):
    steps: List[AnyAction]
