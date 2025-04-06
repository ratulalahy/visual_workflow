import replicate
import logging
import asyncio
from typing import Dict, Any, Optional

from src.assistant.interfaces.vlm_service import VLMService
from src.config import app_config  # Import the shared config instance
from src.assistant.exceptions import VLMError, ConfigError
from src.assistant.services.desktop_control.mss_screenshotter import MSSScreenshotter
from src.assistant.exceptions import ScreenshotError


logger = logging.getLogger(__name__)


class ReplicateVLMService(VLMService):
    """
    A concrete implementation of VLMService using the Replicate platform,
    specifically targeting a pre-defined OmniParser deployment.
    """

    def __init__(self, config: Optional[app_config.__class__] = None):
        """
        Initializes the Replicate VLM service.

        Args:
            config: An AppConfig instance. If None, uses the global app_config.
        """
        self._config = config or app_config
        if not self._config.replicate_api_token:
            logger.error("Replicate API token is not configured.")
            raise ConfigError(
                "REPLICATE_API_TOKEN is missing in configuration.")
        if not self._config.replicate_deployment_owner or not self._config.replicate_deployment_name:
            logger.error(
                "Replicate deployment owner or name is not configured.")
            raise ConfigError(
                "Replicate deployment owner/name is missing in configuration.")

        try:
            self.client = replicate.Client(
                api_token=self._config.replicate_api_token)
            self.deployment_id = f"{self._config.replicate_deployment_owner}/{self._config.replicate_deployment_name}"
            logger.info(
                f"ReplicateVLMService initialized for deployment: {self.deployment_id}")
        except Exception as e:
            logger.exception("Failed to initialize Replicate client.")
            raise VLMError(
                f"Failed to initialize Replicate client: {e}") from e

    async def analyze_image(self, image_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """
        Analyzes the provided image using the configured Replicate deployment.

        Args:
            image_bytes: The image content as bytes.
            prompt: The question or instruction for analyzing the image.

        Returns:
            A dictionary containing the analysis results from the Replicate model.

        Raises:
            VLMError: If the API call fails or returns an error.
        """
        if not self.client:
            raise VLMError("Replicate client is not initialized.")

        # Encode image to data URI format
        image_uri = self.create_data_uri(image_bytes, mime_type="image/png")
        logger.info(
            f"Analyzing image with Replicate OmniParser. Prompt (may be ignored by OmniParser): {prompt}")
        logger.debug(
            f"Image size: {len(image_bytes)} bytes. Data URI length: {len(image_uri)}")

        input_data = {
            "image": image_uri,
            # Include prompt if the model supports it
            # "prompt": prompt
        }

        try:
            logger.debug(
                f"Calling Replicate deployment prediction create for {self.deployment_id}")

            # Correct way to call the prediction
            prediction = await asyncio.to_thread(
                lambda: self.client.deployments.predictions.create(
                    deployment=self.deployment_id,  # Combine owner/name into one string
                    input=input_data
                )
            )

            logger.info(
                f"Replicate prediction started: ID {prediction.id}, Status: {prediction.status}")

            prediction_id = prediction.id
            final_prediction = None
            while True:
                retrieved_prediction = await asyncio.to_thread(self.client.predictions.get, prediction_id)
                if retrieved_prediction.status in ["succeeded", "failed", "canceled"]:
                    final_prediction = retrieved_prediction
                    break
                logger.debug(
                    f"Waiting for prediction {prediction_id}. Current status: {retrieved_prediction.status}")
                await asyncio.sleep(1)

            if final_prediction is None or final_prediction.status != "succeeded":
                error_detail = final_prediction.error if final_prediction else "Prediction object not available"
                logger.error(
                    f"Replicate prediction failed or was canceled. Status: {final_prediction.status if final_prediction else 'Unknown'}, Error: {error_detail}")
                raise VLMError(f"Replicate prediction failed: {error_detail}")

            logger.info(
                f"Replicate prediction {final_prediction.id} completed successfully.")

            output = final_prediction.output or {}
            if not isinstance(output, dict):
                logger.warning(
                    f"Replicate output is not a dictionary: {type(output)}. Returning as is.")
                return {"raw_output": output}

            logger.debug(f"Replicate analysis result: {output}")
            return output

        except replicate.exceptions.ReplicateError as e:
            logger.exception("Replicate API error occurred.")
            raise VLMError(f"Replicate API error: {e}") from e
        except Exception as e:
            logger.exception(
                "An unexpected error occurred during Replicate interaction.")
            raise VLMError(f"Unexpected error during VLM analysis: {e}") from e


# Example Usage (Requires running in an async context)
async def main():
    logging.basicConfig(level=logging.INFO)
    try:
        # 1. Get a screenshot
        screenshotter = MSSScreenshotter()
        img_bytes = screenshotter.take_screenshot()
        print(f"Screenshot captured ({len(img_bytes)} bytes)")

        # 2. Initialize Replicate Service
        vlm_service = ReplicateVLMService()

        # 3. Analyze
        # Example prompt (might be ignored by this specific OmniParser deployment)
        prompt = "Find the main elements on the screen."
        print("Analyzing screenshot with Replicate OmniParser...")
        result = await vlm_service.analyze_image(img_bytes, prompt)

        print("\nAnalysis Result:")
        # Print result nicely (OmniParser output can be complex)
        import json
        print(json.dumps(result, indent=2))

    except (ConfigError, ScreenshotError, VLMError) as e:
        print(f"Error: {e}")
    except ImportError:
        print("Error: Required libraries ('replicate', 'mss', 'Pillow', 'python-dotenv') not installed.")
        print("Please run: pip install replicate mss Pillow python-dotenv")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Check for API keys before running example
    if not app_config.replicate_api_token:
        print("Error: REPLICATE_API_TOKEN not found in environment or .env file.")
        print("Please set the API token to run this example.")
    else:
        # Use asyncio.run() to execute the async main function
        print("Running Replicate VLM Service example...")
        asyncio.run(main())
