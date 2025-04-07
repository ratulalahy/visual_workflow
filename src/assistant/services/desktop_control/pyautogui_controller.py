import pyautogui
import logging
import time
import platform
import subprocess
import asyncio
from typing import Tuple, Optional

from src.assistant.interfaces.desktop_controller import IDesktopController, IScreenshotter
from src.assistant.exceptions import DesktopControlError, ScreenshotError
from src.assistant.services.desktop_control.mss_screenshotter import MSSScreenshotter

logger = logging.getLogger(__name__)

# Configure PyAutoGUI pauses (optional but recommended)
pyautogui.PAUSE = 0.1  # Small pause after each PyAutoGUI call
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort


class PyAutoGUIController(IDesktopController):
    """
    A concrete implementation of IDesktopController using the PyAutoGUI library.
    Handles mouse clicks, keyboard input, and delegates screenshotting.
    """

    def __init__(self, screenshotter: Optional[IScreenshotter] = None):
        """
        Initializes the PyAutoGUI controller.

        Args:
            screenshotter: An instance conforming to the IScreenshotter interface.
                           If None, a default MSSScreenshotter will be created.
        """
        self._screenshotter = screenshotter or MSSScreenshotter()
        try:
            # Check if pyautogui is usable (basic check)
            self._screen_width, self._screen_height = pyautogui.size()
            logger.info(
                f"PyAutoGUIController initialized. Screen size: "
                f"{self._screen_width}x{self._screen_height}. "
                f"Using screenshotter: {type(self._screenshotter).__name__}"
            )
            # You might want to add checks for specific OS requirements here if needed
        except Exception as e:
            logger.exception(
                "Failed to initialize PyAutoGUI or get screen size.")
            # Specific error types for pyautogui might vary (e.g., ImportError, platform issues)
            raise DesktopControlError(
                f"Failed to initialize PyAutoGUI: {e}") from e

    def _validate_coordinates(self, x: int, y: int):
        """Checks if coordinates are within screen bounds."""
        if not (0 <= x < self._screen_width and 0 <= y < self._screen_height):
            logger.error(f"Coordinates ({x}, {y}) are outside screen bounds "
                         f"({self._screen_width}x{self._screen_height}).")
            raise DesktopControlError(
                f"Coordinates ({x}, {y}) are out of bounds.")

    def click(self, x: int, y: int):
        """
        Performs a single left click at the specified coordinates.

        Args:
            x: The x-coordinate.
            y: The y-coordinate.

        Raises:
            DesktopControlError: If coordinates are invalid or click fails.
        """
        try:
            self._validate_coordinates(x, y)
            logger.info(f"Performing single click at ({x}, {y})")
            pyautogui.click(x=x, y=y, button='left')
            # Add a small delay sometimes helps ensure click registers
            time.sleep(0.1)
        except pyautogui.PyAutoGUIException as e:
            logger.exception(f"PyAutoGUI failed during click at ({x}, {y}).")
            raise DesktopControlError(f"Click failed: {e}") from e
        except Exception as e:
            # Catch potential errors from _validate_coordinates or other issues
            logger.exception(f"Unexpected error during click at ({x}, {y}).")
            raise DesktopControlError(f"Unexpected click error: {e}") from e

    def double_click(self, x: int, y: int):
        """
        Performs a double left click at the specified coordinates.

        Args:
            x: The x-coordinate.
            y: The y-coordinate.

        Raises:
            DesktopControlError: If coordinates are invalid or double click fails.
        """
        try:
            self._validate_coordinates(x, y)
            logger.info(f"Performing double click at ({x}, {y})")
            pyautogui.doubleClick(x=x, y=y, button='left')
            time.sleep(0.1)  # Small delay
        except pyautogui.PyAutoGUIException as e:
            logger.exception(
                f"PyAutoGUI failed during double click at ({x}, {y}).")
            raise DesktopControlError(f"Double click failed: {e}") from e
        except Exception as e:
            logger.exception(
                f"Unexpected error during double click at ({x}, {y}).")
            raise DesktopControlError(
                f"Unexpected double click error: {e}") from e

    def type_text(self, text: str, interval: float):
        """
        Types the given text using the keyboard.

        Args:
            text: The string to type.

        Raises:
            DesktopControlError: If typing fails.
        """
        try:
            # Log snippet
            logger.info(
                f"Typing text: '{text[:50]}{'...' if len(text)>50 else ''}'")
            # Use interval for potentially more reliable typing
            pyautogui.write(text, interval=interval)
        except pyautogui.PyAutoGUIException as e:
            logger.exception(f"PyAutoGUI failed during {text}.")
            raise DesktopControlError(f"Typing failed: {e}") from e
        except Exception as e:
            logger.exception(f"Unexpected error during {text}.")
            raise DesktopControlError(f"Unexpected typing error: {e}") from e

    def press_key(self, key_name: str):
        """
        Presses a special key (e.g., 'enter', 'tab', 'esc', 'f5').
        See PyAutoGUI documentation for valid key names.

        Args:
            key_name: The name of the key to press.

        Raises:
            DesktopControlError: If the key name is invalid or pressing fails.
        """
        # Basic validation for common keys - can be expanded
        valid_keys = pyautogui.KEYBOARD_KEYS
        normalized_key = key_name.lower()

        if normalized_key not in valid_keys:
            logger.error(
                f"Invalid key name: '{key_name}'. See PyAutoGUI docs for valid keys.")
            raise DesktopControlError(f"Invalid key name: '{key_name}'")

        try:
            logger.info(f"Pressing key: '{normalized_key}'")
            pyautogui.press(normalized_key)
        except pyautogui.PyAutoGUIException as e:
            logger.exception(
                f"PyAutoGUI failed during press_key '{normalized_key}'.")
            raise DesktopControlError(f"Key press failed: {e}") from e
        except Exception as e:
            logger.exception(
                f"Unexpected error during press_key '{normalized_key}'.")
            raise DesktopControlError(
                f"Unexpected key press error: {e}") from e

    def get_screen_size(self) -> Tuple[int, int]:
        """
        Returns the screen resolution (width, height).

        Returns:
            A tuple (width, height).
        """
        # Return the size fetched during initialization
        return self._screen_width, self._screen_height

    def take_screenshot(self) -> bytes:
        """
        Captures the current screen using the injected screenshotter instance.

        Returns:
            The screenshot image as bytes (e.g., PNG format).

        Raises:
            ScreenshotError: If the underlying screenshotter fails.
        """
        logger.info("Delegating screenshot capture.")
        # No try/except here, let the screenshotter handle its own errors
        # and propagate ScreenshotError if needed.
        return self._screenshotter.take_screenshot()

    async def open_application(self, application_name: str):
        """Opens the specified application (OS-dependent)."""
        logger.info(f"Attempting to open application: {application_name}")
        try:
            os_name = platform.system()
            if os_name == "Darwin":  # macOS
                # Using 'open -a' command
                await asyncio.to_thread(subprocess.run, ['open', '-a', application_name], check=True)
                # Alternative: Use Spotlight search via PyAutoGUI
                # pyautogui.hotkey('command', 'space')
                # await asyncio.sleep(0.5) # Wait for spotlight
                # pyautogui.typewrite(application_name, interval=0.05)
                # await asyncio.sleep(0.5)
                # pyautogui.press('enter')
            elif os_name == "Windows":
                # Using 'start' command (might need exact path sometimes)
                # Or just typing name into Run dialog
                pyautogui.hotkey('win', 'r')
                await asyncio.sleep(0.5)
                pyautogui.typewrite(application_name, interval=0.05)
                await asyncio.sleep(0.1)
                pyautogui.press('enter')
            elif os_name == "Linux":
                # Using 'xdg-open' or directly calling the app name usually works if in PATH
                # This is less reliable, may need specific commands
                try:
                    await asyncio.to_thread(subprocess.run, [application_name], check=True, start_new_session=True)
                except FileNotFoundError:
                    # Fallback using xdg-open (might open a file/URL if name matches)
                    await asyncio.to_thread(subprocess.run, ['xdg-open', application_name], check=True)

            else:
                raise DesktopControlError(
                    f"Unsupported operating system for open_application: {os_name}")

            # Add a small delay to allow the app to launch
            await asyncio.sleep(2.0)
            logger.info(f"Command to open '{application_name}' executed.")

        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            logger.error(
                f"Failed to open application '{application_name}': {e}")
            raise DesktopControlError(
                f"Failed to open application '{application_name}': {e}") from e

    async def navigate_url(self, url: str):
        """Opens the given URL in the default web browser."""
        logger.info(f"Attempting to navigate to URL: {url}")
        try:
            os_name = platform.system()
            # Use webbrowser module for cross-platform default browser opening
            import webbrowser
            opened = await asyncio.to_thread(webbrowser.open, url)
            if not opened:
                raise DesktopControlError(
                    f"webbrowser.open failed for URL: {url}")

            # Optional: Alternative using PyAutoGUI if webbrowser fails or focus is needed
            # Requires knowing how to get to address bar (e.g., Ctrl+L/Cmd+L)
            # Assume browser might need opening first:
            # await self.open_application("Google Chrome") # Or "firefox", etc. - potentially problematic
            # await asyncio.sleep(1.0) # Wait for browser
            # if os_name == "Darwin":
            #     pyautogui.hotkey('command', 'l')
            # else: # Windows/Linux often Ctrl+L
            #     pyautogui.hotkey('ctrl', 'l')
            # await asyncio.sleep(0.3)
            # pyautogui.typewrite(url, interval=0.02)
            # await asyncio.sleep(0.1)
            # pyautogui.press('enter')

            await asyncio.sleep(1.0)  # Allow page load time
            logger.info(f"Command to navigate to '{url}' executed.")
        except Exception as e:
            logger.error(f"Failed to navigate to URL '{url}': {e}")
            raise DesktopControlError(
                f"Failed to navigate to URL '{url}': {e}") from e


    async def scroll(self, direction: str, amount: int):
        try:
            unit = amount # PyAutoGUI scroll uses 'clicks' which map roughly to lines/notches
            if direction == "up":
                await asyncio.to_thread(pyautogui.scroll, unit)
            elif direction == "down":
                await asyncio.to_thread(pyautogui.scroll, -unit)
            elif direction == "left":
                await asyncio.to_thread(pyautogui.hscroll, -unit) # Horizontal scroll
            elif direction == "right":
                await asyncio.to_thread(pyautogui.hscroll, unit) # Horizontal scroll
            logger.info(f"Scrolled {direction} by {amount} units.")
        except Exception as e: # PyAutoGUI doesn't have specific scroll errors
            logger.error(f"Scrolling {direction} failed: {e}")
            raise DesktopControlError(f"Scroll {direction} failed: {e}") from e



    async def move_mouse(self, x: int, y: int, duration: float = 0.2):
        """Moves the mouse cursor to the specified coordinates over a duration."""
        try:
            self._validate_coordinates(x, y) # Reuse validation
            logger.info(f"Moving mouse to ({x}, {y}) over {duration}s.")
            await asyncio.to_thread(pyautogui.moveTo, x, y, duration=duration)
        except pyautogui.PyAutoGUIException as e:
            logger.exception(f"PyAutoGUI failed during move_mouse to ({x}, {y}).")
            raise DesktopControlError(f"Move mouse failed: {e}") from e
        except Exception as e:
            logger.exception(f"Unexpected error during move_mouse to ({x}, {y}).")
            raise DesktopControlError(f"Unexpected move mouse error: {e}") from e

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Running PyAutoGUI Controller example...")
    print("WARNING: This will interact with your desktop!")
    print("Ensure no sensitive windows are open.")
    print("Starting in 5 seconds...")
    time.sleep(5)

    try:
        # You can explicitly pass a screenshotter if needed:
        # screenshotter = MSSScreenshotter()
        # controller = PyAutoGUIController(screenshotter=screenshotter)
        controller = PyAutoGUIController()  # Uses default MSSScreenshotter

        width, height = controller.get_screen_size()
        print(f"Screen Size: {width}x{height}")

        # Example: Click near center (use coordinates cautiously!)
        center_x, center_y = width // 2, height // 2
        print(f"Clicking near center at ({center_x}, {center_y})")
        controller.click(center_x, center_y)
        time.sleep(1)

        # Example: Typing (will type wherever focus is!)
        print("Typing 'Hello from PyAutoGUI!'")
        controller.type_text("Hello from PyAutoGUI!")
        time.sleep(1)

        # Example: Pressing Enter
        print("Pressing Enter key")
        controller.press_key('enter')
        time.sleep(1)

        # Example: Taking a screenshot
        print("Taking screenshot...")
        img_bytes = controller.take_screenshot()
        output_path = "pyautogui_test_screenshot.png"
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        print(f"Screenshot saved to {output_path}")

        print("Example finished successfully.")

    except (DesktopControlError, ScreenshotError) as e:
        print(f"Error during controller execution: {e}")
    except ImportError:
        print("Error: Required libraries ('pyautogui', 'mss', 'Pillow') not installed.")
        print("Please run: pip install pyautogui mss Pillow")
        # Note: PyAutoGUI might have OS-specific dependencies (e.g., scrot on Linux)
    except Exception as e:
        # Catch pyautogui.FailSafeException if user triggers failsafe
        if "FailSafeException" in str(type(e)):
            print(
                "\nFailsafe triggered (mouse moved to top-left corner). Execution stopped.")
        else:
            print(f"An unexpected error occurred: {e}")
