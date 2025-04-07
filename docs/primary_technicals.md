# Core Components

- **`src/main.py`**: Main application entry point. Handles setup, optional argument parsing, service initialization, and starting the Orchestrator loop.
- **`src/config.py`**: Loads configuration from environment variables or a `.env` file (API keys, etc.).
- **`src/assistant/orchestrator.py`**: The central coordinator. Manages overall execution flow, interacts with services, validates plans, and executes actions step-by-step.
- **`src/assistant/models/`**: Contains Pydantic models.
  - **`actions.py`**: Defines the structure for **every possible action** the assistant can perform (e.g., `ClickAction`, `TypeTextAction`, `OpenApplicationAction`). Includes the crucial `AnyAction = Union[...]` type that lists all valid actions.
  - **`common.py`**: Defines common data structures like `Coordinates`, `BoundingBox`.
- **`src/assistant/interfaces/`**: Defines Abstract Base Classes (interfaces) for services, ensuring modularity.
  - **`llm_service.py`**: Interface for services generating action plans from commands (`generate_plan`).
  - **`vlm_service.py`**: Interface for services analyzing images (`analyze_image`).
  - **`desktop_controller.py`**: Interface for desktop interaction (`click`, `type_text`, `open_application`, `take_screenshot`, etc.) and includes the `IScreenshotter` interface.
- **`src/assistant/services/`**: Concrete implementations of interfaces.
  - **`openai_service.py`**: Implements `LLMService` using OpenAI's API, including dynamic prompt generation.
  - **`replicate_service.py`**: Implements `VLMService` using Replicate (or other VLM providers).
  - **`desktop_control/`**: Implementations for desktop interaction.
    - **`pyautogui_controller.py`**: Implements `IDesktopController` using PyAutoGUI.
    - **`mss_screenshotter.py`**: Implements `IScreenshotter` using MSS library.
  - **`prompts/`**: External prompt files.
    - **`base_system_prompt.md`**: Base Markdown template for the LLM system prompt, contains `AVAILABLE_ACTIONS_PLACEHOLDER`.
- **`src/assistant/exceptions.py`**: Custom exception classes for error handling.
- **`src/assistant/utils/`**: Utility modules.
  - **`logging_config.py`**: Configures application logging.
- **`logs/`**: Directory for log files.
- **`.env`**: File storing sensitive API keys (ignored by Git).

---

## Configuration (`.env` file)

Create a `.env` file in the project root with your API keys:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
REPLICATE_API_TOKEN=your_replicate_api_token_here
# Optional VLM deployment override:
# REPLICATE_VLM_DEPLOYMENT=owner/model-name:version
```

---

## How Actions Work

Actions are fundamental execution units, rigorously defined using Pydantic for structured validation.

- **Definition (`models/actions.py`)**:  
  Each possible action (e.g., click, type, open app) has its own Pydantic class inheriting from `BaseAction`. These classes define required fields (e.g., `text` for `TypeTextAction`, `application_name` for `OpenApplicationAction`) and use `Literal` types for the action field (e.g., `action: Literal["TYPE_TEXT"] = "TYPE_TEXT"`).

- **Union (`models/actions.py`)**:  
  `AnyAction = Union[...]` combines individual action models for type hinting and validation.

- **Planning (`openai_service.py`)**:  
  The LLM receives dynamically generated prompts instructing it to produce a JSON plan conforming to defined action models.

- **Validation (`orchestrator.py`)**:  
  The Orchestrator validates the received plan (`List[dict]`) using `pydantic.TypeAdapter(AnyAction)`. Pydantic checks actions, fields, types, and required properties, catching errors before execution.

- **Execution (`orchestrator.py`)**:  
  Validated actions (`List[AnyAction]`) are executed step-by-step using `isinstance(action, SpecificActionModel)` checks, invoking corresponding `IDesktopController` methods with validated parameters.

---


# Potential Future Enhancements

- **VLM Integration**: Fully implement screenshot analysis for interacting based on visual descriptions (using `ANALYZE_SCREENSHOT` results in `_get_coordinates_from_action_or_vlm`).
- **Error Recovery/Re-planning**: On step failure, ask the LLM for a new plan based on errors and context.
- **More Complex Actions**: Add support for drag-and-drop, closing/switching applications, reading from screen (OCR without VLM).
- **State Management**: Maintain richer desktop state context between commands.
- **User Interface**: Develop a simple GUI instead of using the console.
- **Configuration File**: Use YAML/TOML files for more complex configurations beyond `.env`.
