# Dynamic Prompt Generation

To avoid manually keeping the LLM system prompt synchronized with the defined Pydantic action models (`models/actions.py`), the `OpenAIService` dynamically generates the **"Available Actions"** section of the prompt upon initialization.

### Base Prompt (`base_system_prompt.md`):

- Contains general instructions and includes the placeholder: `AVAILABLE_ACTIONS_PLACEHOLDER`.

### Generation Function (`generate_action_definitions_prompt` in `openai_service.py`):

- Uses Python's typing module (`get_args`) to inspect the `AnyAction` union and retrieves the list of all defined action model classes.
- Iterates through each action model.
- Leverages Pydantic's introspection capabilities (`model_fields`, `model_json_schema`) to extract:
  - The action's literal name (e.g., `"COPY_TO_CLIPBOARD"`).
  - Required fields.
  - Optional fields.
  - Field types, default values, and descriptions.
- Formats this information into the structured text block seen in the prompt, including JSON format examples.

### Initialization (`OpenAIService.__init__`):

- Loads the content from `base_system_prompt.md`.
- Calls `generate_action_definitions_prompt(AnyAction)` to obtain the action definitions string.
- Replaces the `AVAILABLE_ACTIONS_PLACEHOLDER` in the base prompt content with the generated definitions.
- Stores the finalized, complete prompt string for use in API calls.

---
