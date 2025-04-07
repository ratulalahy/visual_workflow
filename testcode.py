import json
import openai

# Your OpenAI API Key
OPENAI_API_KEY = "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"

# System prompt to guide the LLM
SYSTEM_PROMPT = """
You are an AI assistant that controls a computer desktop. Your goal is to translate a user's natural language command into a sequence of precise actions to be executed on the GUI.

[Rest of your system prompt remains exactly the same...]

IMPORTANT: Respond with a JSON object containing the plan. The output must be valid JSON.
"""

def generate_plan(command: str):
    """
    Generates a step-by-step plan using OpenAI's GPT-4o model.
    Returns a list of dictionaries representing the action plan.
    """
    try:
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        print(f"Generating plan for command: '{command}'")
        
        # Make the API call with explicit JSON instruction
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"User Command: \"{command}\"\n\nPlease respond with a JSON formatted plan."},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        raw_response = response.choices[0].message.content
        print("Raw response from OpenAI:")
        print(raw_response)

        # Parse the JSON response
        parsed_json = json.loads(raw_response)
        
        # Handle different response formats
        if isinstance(parsed_json, list):
            plan = parsed_json
        elif isinstance(parsed_json, dict) and "plan" in parsed_json:
            plan = parsed_json["plan"]
        else:
            raise ValueError("Unexpected response format from OpenAI")

        # Validate each step in the plan
        for step in plan:
            if not isinstance(step, dict) or "action" not in step or "parameters" not in step:
                raise ValueError(f"Invalid step format: {step}")

        print(f"Successfully generated plan with {len(plan)} steps.")
        return plan

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print(f"Raw response was: {raw_response}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
if __name__ == '__main__':
    command = "Open Gmail and send an email to ratul.kuet@gmail.com asking to schedule the next meeting"
    print(f"\nGenerating plan for: '{command}'")
    
    plan = generate_plan(command)
    
    if plan:
        print("\nGenerated Plan:")
        print(json.dumps(plan, indent=2))
    else:
        print("Failed to generate plan")