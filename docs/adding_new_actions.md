# How to Add a New Action

Adding a new capability (e.g., copying text to the clipboard) involves these steps:

---

## Step 1: Define the Action Model (`src/assistant/models/actions.py`)

- Create a new Pydantic class inheriting from `BaseAction`.
- Define the action: `Literal["ACTION_NAME"] = "ACTION_NAME"` field with the unique uppercase name for this action.
- Add any necessary fields required for the action (e.g., maybe `text_to_copy: Optional[str]` if copying specific text, or no extra fields if just copying current selection).
- Add the new action class to the `AnyAction = Union[...]` list.

```python
# src/assistant/models/actions.py

# ... other imports and BaseAction ...

class CopyToClipboardAction(BaseAction):
    action: Literal["COPY_TO_CLIPBOARD"] = "COPY_TO_CLIPBOARD"
    # Optional: add text field if you want to copy specific text,
    # otherwise assume it copies current selection (requires controller logic)
    # text_to_copy: Optional[str] = Field(None, description="Specific text to copy, if not copying selection")
    reason: Optional[str] = None  # Inherited from BaseAction

# ... other action classes ...

# --- Add the new action to the Union ---
AnyAction = Union[
    ClickAction,
    DoubleClickAction,
    TypeTextAction,
    # ... other existing actions ...
    ScrollAction,
    MoveMouseAction,
    CopyToClipboardAction,  # <--- ADD HERE
    TaskCompleteAction,
    TaskFailedAction,
]

# Plan class remains the same
```

---

## Step 2: Define the Interface Method (`src/assistant/interfaces/desktop_controller.py`)

Add a corresponding abstract method to the `IDesktopController` interface. Make it async if the implementation might involve I/O.

```python
# src/assistant/interfaces/desktop_controller.py
from abc import ABC, abstractmethod
# ... other imports ...

class IDesktopController(ABC):
    # ... existing abstract methods ...

    @abstractmethod
    async def copy_to_clipboard(self):  # Add parameters if needed (e.g., text: str)
        """Copies the current selection (or specified text) to the clipboard."""
        pass
```

---

## Step 3: Implement the Controller Method (`src/assistant/services/desktop_control/pyautogui_controller.py`)

- Add the concrete implementation of the method defined in the interface.
- Use appropriate libraries (e.g., `pyperclip` for clipboard operations, `PyAutoGUI` for simulating Ctrl+C/Cmd+C).
- Wrap blocking calls in `asyncio.to_thread`.
- Include logging and raise `DesktopControlError` on failure.

```python
# src/assistant/services/desktop_control/pyautogui_controller.py
import pyautogui
import asyncio
import pyperclip  # Import pyperclip (add to requirements.txt)
import platform
# ... other imports ...
from src.assistant.interfaces.desktop_controller import IDesktopController
from src.assistant.exceptions import DesktopControlError

logger = logging.getLogger(__name__)

class PyAutoGUIController(IDesktopController):
    # ... existing methods ...

    async def copy_to_clipboard(self):  # Match interface signature
        """Copies the current selection using keyboard shortcuts."""
        logger.info("Attempting to copy current selection to clipboard.")
        try:
            # Use platform-specific copy shortcuts
            if platform.system() == "Darwin":  # macOS
                hotkey_args = ['command', 'c']
            else:  # Windows/Linux
                hotkey_args = ['ctrl', 'c']

            # Use asyncio.to_thread for the blocking pyautogui call
            await asyncio.to_thread(pyautogui.hotkey, *hotkey_args)
            await asyncio.sleep(0.2)  # Brief pause to ensure clipboard updates
            # Optional: Verify by reading clipboard
            # copied_text = await asyncio.to_thread(pyperclip.paste)
            # logger.info(f"System copy command executed. Clipboard content (start): '{copied_text[:50]}...'")
            logger.info(f"Executed copy shortcut ({'/'.join(hotkey_args)}).")

        except Exception as e:  # Catch potential errors from pyautogui or pyperclip
            logger.exception(f"Failed to copy to clipboard: {e}")
            raise DesktopControlError(f"Copy to clipboard failed: {e}") from e

    # ... rest of the class ...
```

**Remember:** Install the new dependency:

```bash
pip install pyperclip
```

And add it to `requirements.txt`.

---

## Step 4: Add Orchestrator Logic (`src/assistant/orchestrator.py`)

- Import the new action model (`from .models.actions import CopyToClipboardAction`).
- Add an `elif isinstance(action, CopyToClipboardAction)` block within the `_execute_action` method.
- Call the corresponding controller method.

```python
# src/assistant/orchestrator.py
# ... other imports ...
from .models.actions import (
    AnyAction, ClickAction, TypeTextAction,  # ... other actions ...
    CopyToClipboardAction  # <--- IMPORT HERE
)

class Orchestrator:
    # ... existing methods ...

    async def _execute_action(self, action: AnyAction) -> Optional[Dict[str, Any]]:
        # ... (start of method) ...
        try:
            # ... existing elif blocks ...

            elif isinstance(action, CopyToClipboardAction):
                try:
                    await self.desktop_controller.copy_to_clipboard()
                    # Optionally read clipboard to confirm/log?
                    # result_data = {"clipboard_content_preview": clipboard_text[:50]}
                    result_data = {"status": "Copy command executed"}
                except DesktopControlError as e:
                    logger.error(f"Copy to clipboard failed: {e}")
                    raise  # Propagate error

            # ... elif blocks for TaskComplete/Failed, else: ...

        # ... (rest of method: history update, error handling) ...
```

---

## Step 5: Restart and Test

- Restart the assistant application.
- Give it a command that should trigger the new action (e.g., `"Select the first paragraph and copy it to the clipboard"`).

---

That's it! You do **not** need to manually update the prompt file. The `OpenAIService` will automatically detect the `CopyToClipboardAction` in `AnyAction` during its initialization and include it in the system prompt sent to the LLM.
