from abc import ABC, abstractmethod
from typing import List, Dict, Any 

# from ..models.actions import Action

class LLMService(ABC):
    """
    Abstract Base Class for Language Model Services.
    Defines the interface for generating execution plans from natural language commands.
    """

    @abstractmethod
    async def generate_plan(self, command: str, current_context: str = "") -> List[Dict[str, Any]]:
        """
        Generates a step-by-step plan based on the user command and optional context.

        Args:
            command: The natural language command from the user.
            current_context: Optional context, potentially including recent screen analysis.

        Returns:
            A list of dictionaries, where each dictionary represents an action step.
            (Structure to be refined with specific Action models).
            Example step: {"action": "CLICK", "parameters": {"x": 100, "y": 200}}
        """
        pass