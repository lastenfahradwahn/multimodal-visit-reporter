"""
AI service module for multimodal extraction.
Uses LiteLLM to interface with Groq (Whisper) and OpenRouter (Pixtral, Mistral Small).
"""

import base64
import json
import logging
import os
import re
import sys
from typing import Any, Dict

import litellm
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env

from app.prompts import get_extraction_system_prompt, get_extraction_user_prompt

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JSON parsing helper
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from the given text, handling extra commentary,
    markdown code fences, or surrounding text.
    """
    clean = text.strip()

    # 1st attempt: parse the whole string directly
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Fallback: locate the first balanced JSON object
    start = clean.find("{")
    if start == -1:
        raise ValueError("No JSON object found in the AI response.")

    brace_count = 0
    for i in range(start, len(clean)):
        if clean[i] == "{":
            brace_count += 1
        elif clean[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                json_str = clean[start : i + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Extracted JSON fragment is invalid: {e}"
                    ) from e
    raise ValueError("Incomplete JSON object in AI response: unmatched braces.")


# ---------------------------------------------------------------------------
# AI capabilities
# ---------------------------------------------------------------------------
def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an audio file using Groq Whisper.

    Args:
        file_path: Path to the audio file (wav, mp3, m4a, etc.).

    Returns:
        Transcribed text.

    Raises:
        Exception if transcription fails.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcription = litellm.transcription(
                model="groq/whisper-large-v3",
                file=audio_file,
            )
        if isinstance(transcription, dict):
            return transcription.get("text", "")
        return str(transcription)
    except Exception:
        logger.exception("Audio transcription failed")
        raise


def describe_image(image_path: str) -> str:
    """
    Generate a natural language description of an image using Pixtral.

    Args:
        image_path: Path to an image file (jpg, png, etc.).

    Returns:
        Text description of the image.

    Raises:
        Exception if the API call fails or returns empty content.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Describe this image in detail, capturing all visible text, "
                        "diagrams, and key elements."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    },
                },
            ],
        }
    ]

    try:
        response = litellm.completion(
            model="openrouter/mistralai/pixtral-large-2411",
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from image description model.")
        return content.strip()
    except Exception:
        logger.exception("Image description failed")
        raise


def extract_from_text(text: str) -> Dict[str, Any]:
    """
    Extract a structured visit report from a piece of text.

    Args:
        text: Raw text (transcription, image description, or manual note).

    Returns:
        Dictionary matching the Visit schema (id and created_at are added later).

    Raises:
        ValueError if the AI response cannot be parsed into valid JSON.
        Exception for API failures.
    """
    system_prompt = get_extraction_system_prompt()
    user_prompt = get_extraction_user_prompt(text)

    try:
        response = litellm.completion(
            model="openrouter/google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=1024,
        )
        ai_text = response.choices[0].message.content
        if not ai_text:
            raise ValueError("Empty response from extraction model.")

        report = _extract_json(ai_text)

        report.setdefault("customer_name", None)
        report.setdefault("company", None)
        report.setdefault("visit_date", None)
        report.setdefault("topics", [])
        report.setdefault("action_items", [])
        report.setdefault("sentiment", None)

        return report
    except Exception:
        logger.exception("Extraction from text failed")
        raise


def extract_from_image(image_path: str) -> Dict[str, Any]:
    """
    Full pipeline for image -> structured report:
    1. Describe the image with Pixtral.
    2. Extract structured data from that description.
    """
    description = describe_image(image_path)
    return extract_from_text(description)


# ---------------------------------------------------------------------------
# Basic local test (no API call)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    test_string = (
        'Here is the JSON: {"customer_name": "John Doe", '
        '"company": "Acme", "visit_date": "2025-04-01", '
        '"topics": ["demo", "pricing"], '
        '"action_items": ["send email"], "sentiment": "positive"}'
    )
    try:
        result = _extract_json(test_string)
        print("✓ JSON extraction test passed:", result)
    except Exception as e:
        print("✗ JSON extraction test failed:", e)

    print("AI service module loaded successfully.")
