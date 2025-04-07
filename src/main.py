import asyncio
import logging
import argparse  # For potential command-line arguments

# Import configuration and logging setup
from src.config import app_config
from src.assistant.utils.logging_config import setup_logging


# Import core components
from src.assistant.orchestrator import Orchestrator
from src.assistant.services.openai_service import OpenAIService
from src.assistant.services.replicate_service import ReplicateVLMService
from src.assistant.services.desktop_control.pyautogui_controller import PyAutoGUIController
# Assuming PyAutoGUIController uses MSSScreenshotter by default, no need to import MSSScreenshotter explicitly here unless passed separately

# Import exceptions for handling startup issues
from src.assistant.exceptions import ConfigError, LLMError, VLMError, DesktopControlError

# Get a logger for the main module
logger = logging.getLogger(__name__)


async def main(command: str | None = None):
    """
    Main async function to initialize and run the assistant.

    Args:
        command: An optional command provided via arguments. If None, runs interactively.
    """
    # --- Setup Logging ---
    # Call this first to ensure all subsequent logs are captured
    setup_logging()

    logger.info("=========================================")
    logger.info("   Desktop AI Assistant - Starting Up    ")
    logger.info("=========================================")

    # --- Configuration Check ---
    if not app_config.openai_api_key:
        logger.error(
            "CRITICAL: OpenAI API Key (OPENAI_API_KEY) is not configured.")
        print("\nError: OpenAI API Key is missing. Please set it in .env or environment variables.")
        return  # Exit if critical config is missing
    if not app_config.replicate_api_token:
        logger.error(
            "CRITICAL: Replicate API Token (REPLICATE_API_TOKEN) is not configured.")
        print("\nError: Replicate API Token is missing. Please set it in .env or environment variables.")
        return  # Exit if critical config is missing

    logger.info(f"Configuration loaded: {app_config}")

    # --- Initialize Services ---
    try:
        logger.info("Initializing services...")
        # LLM Service (OpenAI)
        llm_service = OpenAIService(config=app_config)

        # VLM Service (Replicate OmniParser)
        vlm_service = ReplicateVLMService(config=app_config)

        # Desktop Controller (PyAutoGUI)
        # It implicitly creates its default screenshotter (MSS)
        desktop_controller = PyAutoGUIController()

        logger.info("Services initialized successfully.")

    except (ConfigError, LLMError, VLMError, DesktopControlError) as e:
        logger.exception(f"Fatal error during service initialization: {e}")
        print(
            f"\nError: Failed to initialize required services. Please check logs/configuration. Details: {e}")
        return
    except Exception as e:  # Catch any other unexpected init errors
        logger.exception(
            f"An unexpected fatal error occurred during initialization: {e}")
        print(
            f"\nError: An unexpected error occurred during setup. Details: {e}")
        return

    # --- Initialize Orchestrator ---
    orchestrator = Orchestrator(
        llm_service=llm_service,
        vlm_service=vlm_service,
        desktop_controller=desktop_controller
    )
    logger.info("Orchestrator initialized.")

    # --- Run Mode ---
    if command:
        # Run with command from argument
        logger.info(f"Running in single-command mode for: '{command}'")
        print(f"\nExecuting command: {command}")
        await orchestrator.run(command)
    else:
        # Run in interactive loop mode
        logger.info(
            "Running in interactive mode. Type 'quit' or 'exit' to stop.")
        print("\nDesktop AI Assistant")
        print("Enter your command (e.g., 'Open Spotify and play Taylor Swift', or 'quit' to exit):")
        while True:
            try:
                user_command = input("> ")
                if user_command.lower() in ["quit", "exit"]:
                    logger.info("User requested exit.")
                    break
                if not user_command:
                    continue

                logger.info(f"Received interactive command: '{user_command}'")
                await orchestrator.run(user_command)
                # Prompt for next command
                print("\nEnter your next command (or 'quit' to exit):")

            except KeyboardInterrupt:
                logger.info("User interrupted execution (Ctrl+C).")
                print("\nExiting...")
                break
            except Exception as e:  # Catch errors during the run loop itself
                logger.exception(
                    f"An error occurred during interactive command execution: {e}")
                print(f"\nAn error occurred: {e}")  # Show error to user
                print("\nEnter your next command (or 'quit' to exit):")  # Re-prompt

    logger.info("=========================================")
    logger.info("   Desktop AI Assistant - Shutting Down  ")
    logger.info("=========================================")


if __name__ == "__main__":
    # --- Argument Parsing (Optional) ---
    parser = argparse.ArgumentParser(description="Desktop AI Assistant")
    parser.add_argument(
        "-c", "--command",
        type=str,
        help="Execute a single command directly and exit."
    )
    args = parser.parse_args()

    # --- Run Main Application ---
    try:
        # Run the async main function
        asyncio.run(main(command=args.command))
    except Exception as e:
        # Catch any truly unexpected top-level errors during asyncio.run
        # Logging might not be set up if error is very early
        print(f"FATAL: An unexpected top-level error occurred: {e}")
        # Log manually if possible
        try:
            logging.getLogger(__name__).exception("FATAL Top-Level Exception")
        except:
            pass  # Ignore if logging setup failed
