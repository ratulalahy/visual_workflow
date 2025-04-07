# Desktop AI Assistant - Documentation

This project aims to create an AI assistant capable of understanding natural language commands and translating them into actions that control a computer's graphical user interface (GUI). It leverages Large Language Models (LLMs) for planning, Vision Language Models (VLMs) for screen analysis (optional/future), and desktop automation libraries for execution.

### Core Flow

1.  User provides a command (e.g., "Open Chrome and go to google.com").
2.  The **LLM Service** receives the command.
3.  The LLM Service interacts with an LLM (e.g., GPT-4o) using a carefully crafted **dynamic prompt** to generate a step-by-step plan.
4.  The plan is returned as a list of structured action objects (conforming to Pydantic models).
5.  The **Orchestrator** receives the raw plan, validates each step against the defined Pydantic action models (`AnyAction` union), and then executes the steps sequentially.
6.  For each step, the Orchestrator calls the appropriate method on the **Desktop Controller** interface.
7.  The specific **Desktop Controller implementation** (e.g., `PyAutoGUIController`) interacts with the GUI using libraries like PyAutoGUI.
8.  (Future) For visual actions (like clicking based on description), the Orchestrator would use the **Screenshotter** and **VLM Service** to analyze the screen and find coordinates.

# Running the Assistant

Ensure you've created `.env` and installed dependencies:

```bash
pip install -r requirements.txt
```

**Interactive Mode:**

```bash
python -m src.main
```

Then, type commands at the `>` prompt. Type `quit` or `exit` to stop.

**Single Command Mode:**

```bash
python -m src.main --command "Your command here"
```

**Example:**

```bash
python -m src.main --command "Open Calculator and type 5*5 then press enter"
```

Check console output and `logs/assistant.log` for detailed execution logs and debugging information.
