from abc import ABC, abstractmethod
from typing import Tuple, Optional

class IScreenshotter(ABC):
    """Interface specifically for taking screenshots."""
    @abstractmethod
    def take_screenshot(self) -> bytes:
        """
        Captures the current screen.

        Returns:
            The screenshot image as bytes (e.g., PNG format).
        """
        pass

class IDesktopController(ABC):
    """
    Abstract Base Class for Desktop Interaction.
    Defines the interface for controlling mouse, keyboard, and taking screenshots.
    """

    @abstractmethod
    def click(self, x: int, y: int):
        """Performs a single left click at the specified coordinates."""
        pass

    @abstractmethod
    def double_click(self, x: int, y: int):
        """Performs a double left click at the specified coordinates."""
        pass

    @abstractmethod
    def type_text(self, text: str):
        """Types the given text using the keyboard."""
        pass

    @abstractmethod
    def press_key(self, key_name: str):
        """Presses a special key (e.g., 'enter', 'tab', 'esc')."""
        pass

    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """Returns the screen resolution (width, height)."""
        pass

    @abstractmethod
    def take_screenshot(self) -> bytes:
        """
        Captures the current screen.

        Returns:
            The screenshot image as bytes (e.g., PNG format).
        """
        pass # Can delegate to an IScreenshotter implementation