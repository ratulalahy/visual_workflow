import os
import logging
from dotenv import load_dotenv
from typing import Optional

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info(".env file loaded.")
else:
    logger.warning(".env file not found. Relying on environment variables.")

class AppConfig:
    """
    Holds application configuration.
    """
    def __init__(self):
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.replicate_api_token: Optional[str] = os.getenv("REPLICATE_API_TOKEN")
        self.replicate_deployment_owner: str = "rapidstart" # As specified
        self.replicate_deployment_name: str = "omni-dev"  # As specified

        self._validate() # Basic validation on initialization

    def _validate(self):
        """
        Basic validation for essential configurations.
        """
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY is not set.")
            # Depending on strictness, you might raise an exception here
            # raise ValueError("Missing required configuration: OPENAI_API_KEY")
        if not self.replicate_api_token:
            logger.warning("REPLICATE_API_TOKEN is not set.")
            # raise ValueError("Missing required configuration: REPLICATE_API_TOKEN")

    def __repr__(self) -> str:
        """
        String representation of the configuration.
        Returns:
            str: The string representation of the configuration.
        """
        # Avoid logging keys directly, just confirm if they are set
        openai_set = 'Set' if self.openai_api_key else 'Not Set'
        replicate_set = 'Set' if self.replicate_api_token else 'Not Set'
        return (f"AppConfig(OpenAI Key: {openai_set}, Replicate Token: {replicate_set}, "
                f"Replicate Deployment: {self.replicate_deployment_owner}/{self.replicate_deployment_name})")

# Create a single instance for the application to use
app_config = AppConfig()

if __name__ == '__main__':
    # Example of how to use it
    print(app_config)
    if not app_config.openai_api_key or not app_config.replicate_api_token:
        print("\nWarning: One or more API keys are missing. Please set them in a .env file or environment variables.")
        print("Example .env file content:")
        print("OPENAI_API_KEY=sk-...")
        print("REPLICATE_API_TOKEN=r8_...")