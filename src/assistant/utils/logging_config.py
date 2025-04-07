import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Define log directory and file
LOG_DIR = "logs"
LOG_FILENAME = os.path.join(LOG_DIR, "assistant.log")

DEFAULT_LOG_LEVEL = logging.INFO # Default level for the application
CONSOLE_LOG_LEVEL = logging.INFO # Level for console output
FILE_LOG_LEVEL = logging.DEBUG   # Level for file output (more verbose)

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_file: str = LOG_FILENAME,
    max_bytes: int = 5 * 1024 * 1024, # 5 MB max file size
    backup_count: int = 3             # Keep 3 backup log files
):
    """
    Configures root logger for console and file output.

    Args:
        log_level: The minimum logging level for the root logger.
        log_file: Path to the log file.
        max_bytes: Maximum size of the log file before rotation.
        backup_count: Number of backup log files to keep.
    """
    # Define log format
    log_format = logging.Formatter(
        fmt='%(asctime)s - %(levelname)-8s - %(name)-15s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level) # Set the minimum level for the logger itself

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(CONSOLE_LOG_LEVEL) # Set level specific to this handler
    console_handler.setFormatter(log_format)

    # --- File Handler ---
    # Use RotatingFileHandler for managing log file size
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(FILE_LOG_LEVEL) # Log more details to the file
    file_handler.setFormatter(log_format)

    # --- Add Handlers ---
    # Clear existing handlers (optional, good practice if run multiple times)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Add a confirmation message that logging is set up
    root_logger.info(f"Logging configured: Level={logging.getLevelName(log_level)}, ConsoleLevel={logging.getLevelName(CONSOLE_LOG_LEVEL)}, FileLevel={logging.getLevelName(FILE_LOG_LEVEL)}, File='{log_file}'")

# Example basic setup call if needed elsewhere, but main.py should call it.
# if __name__ == '__main__':
#     setup_logging()
#     logging.debug("This is a debug message (file only).")
#     logging.info("This is an info message (console and file).")
#     logging.warning("This is a warning message.")
#     logging.error("This is an error message.")