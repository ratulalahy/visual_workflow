import mss
import mss.tools
import logging
from typing import Optional

from src.assistant.interfaces.desktop_controller import IScreenshotter
from src.assistant.exceptions import ScreenshotError

logger = logging.getLogger(__name__)


class MSSScreenshotter(IScreenshotter):
    """
    A concrete implementation of IScreenshotter using the MSS library.
    Captures the primary monitor by default.
    """

    def __init__(self, monitor_number: int = 1):
        """
        Initializes the MSS screenshotter.

        Args:
            monitor_number: The monitor number to capture (1-based index).
                            Defaults to the primary monitor (monitor 1).
        """
        self.monitor_number = monitor_number
        self._sct: Optional[mss.mss] = None
        self._monitor: Optional[dict] = None
        logger.info(
            f"MSSScreenshotter initialized for monitor {self.monitor_number}")

    def _ensure_initialized(self):
        """Initializes the mss instance and selects the monitor if not already done."""
        if self._sct is None:
            try:
                self._sct = mss.mss()
                if not self._sct.monitors:
                    raise ScreenshotError("No monitors found by MSS.")

                # Adjust monitor index (mss is 0-based for 'all', 1-based for specific)
                if self.monitor_number < 1 or self.monitor_number >= len(self._sct.monitors):
                    logger.warning(
                        f"Monitor number {self.monitor_number} is invalid. "
                        f"Found {len(self._sct.monitors)-1} monitors. Defaulting to monitor 1."
                    )
                    self.monitor_number = 1  # Default to primary if invalid index

                self._monitor = self._sct.monitors[self.monitor_number]
                logger.debug(f"Selected monitor details: {self._monitor}")

            except mss.ScreenShotError as e:
                logger.exception("Failed to initialize MSS or select monitor.")
                self._sct = None
                self._monitor = None
                raise ScreenshotError(
                    f"Failed to initialize screen capture: {e}") from e
            except Exception as e:
                logger.exception(
                    "An unexpected error occurred during MSS initialization.")
                self._sct = None
                self._monitor = None
                raise ScreenshotError(
                    f"Unexpected error during screen capture init: {e}") from e

    def take_screenshot(self) -> bytes:
        """
        Captures the specified monitor's screen.

        Returns:
            The screenshot image as PNG bytes.

        Raises:
            ScreenshotError: If capturing the screenshot fails.
        """
        self._ensure_initialized()
        if self._sct is None or self._monitor is None:
            raise ScreenshotError(
                "MSSScreenshotter is not properly initialized.")

        try:
            # Grab the selected monitor
            sct_img = self._sct.grab(self._monitor)
            # Convert to PNG bytes
            png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            logger.info(
                f"Screenshot taken successfully for monitor {self.monitor_number}.")
            return png_bytes
        except mss.ScreenShotError as e:
            logger.exception(
                f"Failed to capture screenshot for monitor {self.monitor_number}.")
            raise ScreenshotError(f"Failed to capture screenshot: {e}") from e
        except Exception as e:
            logger.exception(
                "An unexpected error occurred during screenshot capture.")
            raise ScreenshotError(
                f"Unexpected error during screenshot capture: {e}") from e

    def __enter__(self):
        """Support context management for initialization."""
        self._ensure_initialized()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleans up the MSS context manager if it was created."""
        if self._sct and hasattr(self._sct, 'close') and callable(self._sct.close):
            # Check if sct object is a context manager itself before calling close
            # mss.mss() returns the instance directly, not necessarily a context manager
            # No explicit close needed unless used `with mss.mss() as sct:` internally
            pass
        logger.debug("MSSScreenshotter context exited.")


# Example usage (optional, for testing this module directly)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        screenshotter = MSSScreenshotter()
        # Method 1: Direct call
        # img_bytes = screenshotter.take_screenshot()

        # Method 2: Using context manager
        with MSSScreenshotter() as sct:
            img_bytes = sct.take_screenshot()

        if img_bytes:
            output_path = "test_screenshot.png"
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            print(f"Screenshot saved to {output_path}")
        else:
            print("Failed to capture screenshot.")

    except ScreenshotError as e:
        print(f"Error: {e}")
    except ImportError:
        print("Error: Required libraries ('mss', 'Pillow') not installed.")
        print("Please run: pip install mss Pillow")
