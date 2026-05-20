"""
Prompt templates for AI extraction.
"""


def get_extraction_system_prompt() -> str:
    """Return the system prompt that forces the model to output only JSON."""
    return (
        "You are an AI assistant that extracts structured visit reports from text input. "
        "Your task is to output a single JSON object matching the following schema. "
        "Do not include any additional text, markdown formatting, or code fences. Respond ONLY with the JSON object.\n\n"
        "Schema:\n"
        "{\n"
        '  "customer_name": "string or null (if not mentioned)",\n'
        '  "company": "string or null",\n'
        '  "visit_date": "string in YYYY-MM-DD format (today if not specified)",\n'
        '  "topics": ["list of strings, key topics discussed"],\n'
        '  "action_items": ["list of strings, action items or follow-ups"],\n'
        '  "sentiment": "one of: positive, neutral, negative (infer from tone and content)",\n'
        "}\n\n"
        "Be thorough, concise, and ensure all fields are present."
    )


def get_extraction_user_prompt(input_text: str) -> str:
    """Wrap the input text into a user-prompt for the extraction model."""
    return f"Extract the visit report from the following input:\n\n{input_text}"
