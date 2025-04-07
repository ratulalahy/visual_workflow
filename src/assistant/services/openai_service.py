# src/assistant/services/openai_service.py

import openai
import logging
import json
from typing import List, Dict, Any, Optional, Type, Union, get_args, get_origin, Literal
from enum import Enum
import inspect # To get default values maybe
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined # To check for missing defaults

# Import necessary types and classes
from src.assistant.interfaces.llm_service import LLMService
from src.config import app_config
from src.assistant.exceptions import LLMError, ConfigError
# CRITICAL: Import the actual action definitions to generate the prompt
from src.assistant.models.actions import AnyAction, BaseAction

logger = logging.getLogger(__name__)

# Define the expected raw output type from this service
RawPlan = List[Dict[str, Any]]

# --- Prompt Generation Utility ---

def _format_field_for_prompt(field_name: str, field_info: FieldInfo, is_required: bool) -> str:
    """Formats a single Pydantic field for the LLM prompt."""
    field_type = field_info.annotation
    description = field_info.description or ""
    default_value = field_info.default if field_info.default is not PydanticUndefined else None

    type_str = str(field_type)
    # Simplify common type representations for the prompt
    origin = get_origin(field_type)
    if origin is Literal:
        options = get_args(field_type)
        # Ensure options are strings for join, represent them clearly
        type_str = f"<{'|'.join(map(repr, options))}>" # e.g. <'up'|'down'|'left'|'right'>
    elif origin is Union: # Handle Optional[T] which is Union[T, None]
        args = [arg for arg in get_args(field_type) if arg is not type(None)]
        if len(args) == 1:
             # Simplified representation for Optional[T] -> T
             inner_type = args[0]
             if inner_type is str: type_str = "<string>"
             elif inner_type is int: type_str = "<number>"
             elif inner_type is float: type_str = "<decimal>"
             elif inner_type is bool: type_str = "<true|false>"
             else: type_str = f"<{str(inner_type)}>" # Fallback
        else:
             type_str = f"<{'|'.join(str(a) for a in args)}>" # For other Unions
    elif field_type is str:
        type_str = "<string>"
    elif field_type is int:
        type_str = "<number>"
    elif field_type is float:
        type_str = "<decimal>"
    elif field_type is bool:
        type_str = "<true|false>"
    elif issubclass(field_type, Enum) if inspect.isclass(field_type) else False:
         type_str = f"<{'|'.join(item.value for item in field_type)}>" # For Enums
    # Add more specific formatting if needed

    parts = [f'"{field_name}": {type_str}']
    if not is_required:
        parts.append(f"// Optional")
        if default_value is not None:
             # Represent default nicely (handle strings vs numbers)
             default_repr = f'"{default_value}"' if isinstance(default_value, str) else str(default_value)
             parts.append(f", defaults to {default_repr} if omitted")
    else:
         parts.append(f"// Required")

    if description:
         parts.append(f"// {description}")

    return " ".join(parts)

def generate_action_definitions_prompt(action_union: Type) -> str:
    """Generates the action definition part of the system prompt from Pydantic models."""
    definitions = []
    action_models = get_args(action_union) # Get tuple of types in Union

    # Sort models for consistent prompt order (optional but good)
    action_models = sorted(action_models, key=lambda m: m.model_fields.get('action', FieldInfo(default=m.__name__)).default)

    for i, model_cls in enumerate(action_models, 1):
        if not inspect.isclass(model_cls) or not issubclass(model_cls, BaseModel): continue # Skip non-models

        # Use model_fields for Pydantic V2
        model_fields = model_cls.model_fields
        schema = model_cls.model_json_schema() # Still useful for required fields list
        required_fields = schema.get("required", [])

        # Get action literal value
        action_field_info = model_fields.get("action")
        if not action_field_info or get_origin(action_field_info.annotation) is not Literal: continue
        action_name = get_args(action_field_info.annotation)[0] # Get the literal value

        # Use class name in title for better readability if desired
        definition = f"{i}. Action '{action_name}' (Model: {model_cls.__name__}):\n"
        definition += "    {\n"

        field_lines = []
        example_fields = {}

        # Iterate through fields defined in the model for consistent order
        for field_name, field_info in model_fields.items():
            # Skip 'reason' as it's handled globally in the base prompt instructions
            if field_name == "reason": continue
            # Handle the action field itself separately
            if field_name == "action":
                 field_lines.append(f'        "action": "{action_name}" // Type Indicator')
                 example_fields[field_name] = action_name
                 continue

            is_required = field_name in required_fields
            field_lines.append(f"        {_format_field_for_prompt(field_name, field_info, is_required)}")

            # Create example values (simple heuristics, improve as needed)
            if is_required or field_name in ["text", "url", "application_name", "description", "prompt", "message", "key_name", "x", "y", "direction"]:
                field_type = field_info.annotation
                origin = get_origin(field_type)
                args = get_args(field_type)

                # Handle Optional[T] by looking at the inner type
                if origin is Union and type(None) in args:
                     inner_types = [arg for arg in args if arg is not type(None)]
                     if len(inner_types) == 1: field_type = inner_types[0]; origin = get_origin(field_type); args = get_args(field_type) # Update type info

                if origin is Literal: example_fields[field_name] = args[0] # Pick first option
                elif field_type is str: example_fields[field_name] = f"<{field_name}_example>"
                elif field_type is int: example_fields[field_name] = 123 if "x" in field_name else 456 if "y" in field_name else 1000 if "duration" in field_name else 10
                elif field_type is float: example_fields[field_name] = 0.1
                elif field_type is bool: example_fields[field_name] = True
                # Add more heuristics if needed

        definition += ",\n".join(field_lines)
        definition += "\n    }"

        # Add example
        example_fields["reason"] = "<why_this_action_is_needed>"
        example_json = json.dumps(example_fields, indent=4)
        indented_example = "\n".join("    " + line for line in example_json.splitlines())
        definition += f"\n    Example:\n{indented_example}\n"

        definitions.append(definition)

    return "\n".join(definitions)

# --- Updated OpenAIService ---

PROMPT_DIR = Path(__file__).parent / "prompts"
# Point to the Markdown file
BASE_SYSTEM_PROMPT_FILE = PROMPT_DIR / "base_system_prompt.md"

class OpenAIService(LLMService):
    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, config: Optional[app_config.__class__] = None):
        """Initializes the OpenAI service client and generates the system prompt."""
        self._config = config or app_config
        if not self._config.openai_api_key:
            logger.error("OpenAI API key missing in configuration")
            raise ConfigError("OPENAI_API_KEY is required")

        try:
            self.client = openai.AsyncOpenAI(api_key=self._config.openai_api_key)
            self.model = self.DEFAULT_MODEL
            # Load base prompt and generate full prompt during initialization
            self._system_prompt = self._generate_full_system_prompt()
            logger.info(f"OpenAIService initialized with model: {self.model}")
            # Optionally log the first/last parts of the generated prompt for verification
            # logger.debug(f"Generated System Prompt (Start): {self._system_prompt[:500]}...")
            # logger.debug(f"Generated System Prompt (End): ...{self._system_prompt[-500:]}")
        except Exception as e:
            logger.exception("OpenAI client or prompt loading/generation failed")
            raise LLMError(f"Initialization failed: {e}") from e

    def _generate_full_system_prompt(self) -> str:
        """Loads base prompt and combines with dynamically generated action definitions."""
        try:
            # 1. Load Base Prompt from MD file
            if not BASE_SYSTEM_PROMPT_FILE.is_file():
                 raise FileNotFoundError(f"Base system prompt file missing: {BASE_SYSTEM_PROMPT_FILE}")
            with open(BASE_SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
            logger.info(f"Base system prompt loaded from {BASE_SYSTEM_PROMPT_FILE}")

            # 2. Generate Action Definitions dynamically
            action_definitions = generate_action_definitions_prompt(AnyAction)
            logger.info("Action definitions generated dynamically from Pydantic models.")
            # logger.debug(f"Generated Action Definitions:\n{action_definitions}") # Can be verbose

            # 3. Combine (Replace the placeholder in the base prompt)
            placeholder = "AVAILABLE_ACTIONS_PLACEHOLDER"
            if placeholder not in base_prompt:
                logger.error(f"Placeholder '{placeholder}' not found in base prompt file '{BASE_SYSTEM_PROMPT_FILE}'. Cannot insert action definitions.")
                raise ConfigError(f"Missing placeholder '{placeholder}' in base system prompt.")
            else:
                full_prompt = base_prompt.replace(placeholder, action_definitions)
                logger.info("Action definitions inserted into base prompt.")

            return full_prompt

        except FileNotFoundError as e:
            raise ConfigError(f"Failed to load base system prompt: {e}") from e # Treat missing file as config error
        except Exception as e:
            logger.exception(f"Error generating full system prompt")
            raise LLMError(f"Failed to generate system prompt: {e}") from e

    async def generate_plan(self, command: str, current_context: str = "") -> RawPlan:
        """
        Generate a raw action plan from a natural language command using the generated prompt.

        Args:
            command: User's natural language instruction.
            current_context: Optional context (currently unused).

        Returns:
            List of raw action dictionaries, intended for Pydantic validation later.

        Raises:
            LLMError: For API errors or if the response doesn't contain a valid plan structure.
        """
        if not self.client:
            raise LLMError("OpenAI client not initialized")
        if not self._system_prompt: # Ensure prompt was loaded
             raise LLMError("System prompt not available.")

        logger.info(f"Generating plan for command: '{command}'")
        user_prompt = (
            f"User Command: \"{command}\"\n\n"
            "Please generate the JSON action plan strictly following the structure and action definitions provided in the system prompt."
        )

        try:
            # Use the dynamically generated system prompt stored in self._system_prompt
            logger.debug(f"Using dynamically generated System Prompt (truncated): {self._system_prompt[:300]}...")
            logger.debug(f"User Prompt: {user_prompt}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt}, # Use the generated prompt
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            raw_response_content = response.choices[0].message.content
            logger.debug(f"Raw API response content: {raw_response_content}")

            if not raw_response_content:
                raise LLMError("Received empty content from OpenAI API")

            # Parse the JSON string
            try:
                response_data = json.loads(raw_response_content)
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON response: {json_err}. Response was: {raw_response_content}")
                raise LLMError(f"Invalid JSON received from API: {json_err}") from json_err

            # Extract the plan list - expecting {"plan": [...]}
            if isinstance(response_data, dict) and "plan" in response_data and isinstance(response_data["plan"], list):
                raw_plan = response_data["plan"]
                logger.info(f"Extracted raw plan with {len(raw_plan)} steps.")
                # Basic check: ensure list items are dictionaries (further validation is in Orchestrator)
                if not all(isinstance(step, dict) for step in raw_plan):
                     logger.warning("Plan list contains non-dictionary items. Validation may fail later.")
                return raw_plan # Return the raw list of dictionaries
            else:
                logger.error(f"Response JSON does not contain a 'plan' list. Received structure: {type(response_data)}")
                raise LLMError("Invalid plan structure in API response: Missing 'plan' list.")

        except openai.APIError as api_err:
            logger.exception(f"OpenAI API request failed: {api_err}")
            raise LLMError(f"OpenAI API error: {api_err}") from api_err
        except LLMError: # Re-raise LLMErrors from parsing/structure checks
            raise
        except Exception as e:
            logger.exception("Unexpected error during plan generation")
            raise LLMError(f"Unexpected error in plan generation: {e}") from e

# Keep the main guard for testing this service independently if needed
async def main():
    """Example usage of the OpenAIService."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logging.getLogger("httpx").setLevel(logging.WARNING) # Quieten HTTP logs for example

    # Ensure prompts directory and file exist for the example run
    if not BASE_SYSTEM_PROMPT_FILE.exists():
        print(f"ERROR: Base prompt file not found at {BASE_SYSTEM_PROMPT_FILE}")
        print("Please create the directory structure src/assistant/services/prompts/ and the file base_system_prompt.md")
        # Optionally create a dummy file for testing
        # try:
        #     BASE_SYSTEM_PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
        #     with open(BASE_SYSTEM_PROMPT_FILE, 'w') as f:
        #         f.write("Base Prompt.\nAVAILABLE_ACTIONS_PLACEHOLDER\nEnd Base.")
        #     print("Created dummy base prompt file.")
        # except Exception as e:
        #     print(f"Could not create dummy file: {e}")
        #     return # Exit if file is essential and cannot be created
        return # Exit if file is missing

    if not app_config.openai_api_key:
        print("Error: OPENAI_API_KEY not configured in .env or environment.")
        return

    try:
        # Initialization now includes prompt generation
        print("\n--- Initializing OpenAIService (loads/generates prompt) ---")
        service = OpenAIService()
        print("--- Initialization Complete ---")

        command = "Open notepad, type 'Dynamic prompt test!', and scroll down twice."

        print(f"\n--- Generating plan for: '{command}' ---")
        raw_plan_output = await service.generate_plan(command)

        print("\n--- Generated Raw Plan (List of Dictionaries) ---")
        print(json.dumps(raw_plan_output, indent=2))

        # Simulate Orchestrator validation
        print("\n--- Simulating Orchestrator Pydantic Validation ---")
        try:
           # These imports would normally be in the orchestrator
           from src.assistant.models.actions import AnyAction
           from pydantic import TypeAdapter, ValidationError
           action_adapter = TypeAdapter(AnyAction)
           validated_plan: List[AnyAction] = [action_adapter.validate_python(step) for step in raw_plan_output]
           print(f"--- Pydantic Validation Successful ({len(validated_plan)} steps) ---")
        except ValidationError as validation_error:
           print(f"--- Pydantic Validation FAILED ---")
           # Print simplified errors for readability in example
           print(f"Error count: {len(validation_error.errors())}")
           for error in validation_error.errors()[:5]: # Show first 5 errors
                print(f"  Input: {error.get('input', {}).get('action', 'N/A')} - Loc: {error['loc']} - Msg: {error['msg']} - Type: {error['type']}")
           if len(validation_error.errors()) > 5: print("  ...")
        except ImportError:
            print("Could not import models/TypeAdapter for simulation.")
        except Exception as e:
            print(f"An error occurred during simulated validation: {e}")

    except (ConfigError, LLMError) as e:
        print(f"\n--- Service Error ---")
        print(f"Error: {e}")
    except Exception as e:
        print(f"\n--- Unexpected Error ---")
        print(f"Error: {e}")

if __name__ == '__main__':
    print("--- OpenAI Service with Dynamic Prompt Example ---")
    import asyncio
    asyncio.run(main())