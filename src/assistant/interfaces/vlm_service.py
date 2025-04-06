import base64
from abc import ABC, abstractmethod
from typing import Dict, Any, Union 
class VLMService(ABC):
    """
    Abstract Base Class for Visual Language Model Services.
    Defines the interface for analyzing images (screenshots).
    """

    @abstractmethod
    async def analyze_image(self, image_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """
        Analyzes the provided image based on the given prompt.

        Args:
            image_bytes: The image content as bytes.
            prompt: The question or instruction for analyzing the image.

        Returns:
            A dictionary containing the analysis results from the VLM.
            The structure will depend on the specific VLM's output.
            Example: {"text_found": "Spotify", "bounding_box": [110, 630, 130, 650]}
        """
        pass

    def encode_image_to_base64(self, image_bytes: bytes) -> str:
        """Helper method to encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')

    def create_data_uri(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Helper method to create a data URI (useful for some APIs)."""
        base64_image = self.encode_image_to_base64(image_bytes)
        return f"data:{mime_type};base64,{base64_image}"