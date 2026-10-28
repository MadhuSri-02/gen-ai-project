
import json
import os
from datetime import date
from typing import Any

import requests
from pydantic import ValidationError

from .schemas import TaskExtraction


# Gemini API endpoint
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/{model}:generateContent"
)


class AIServiceError(Exception):
    """Custom error for AI extraction problems."""
    pass


def _extract_json(text: str) -> dict[str, Any]:
    """Parse and validate that the AI response is a JSON object."""

    cleaned = text.strip()

    # Handle Markdown code fences if the model returns them
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIServiceError(
            "Gemini returned invalid JSON. Please try again."
        ) from exc

    if not isinstance(data, dict):
        raise AIServiceError(
            "Gemini did not return a JSON object."
        )

    return data


def extract_task(user_text: str) -> TaskExtraction:
    """Extract structured task details using the Gemini API."""

    # Read Gemini settings from environment variables
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "replace_with_your_key":
        raise AIServiceError(
            "GEMINI_API_KEY is not configured. "
            "Add it to backend/.env and restart the backend."
        )

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    ).strip()

    if not model:
        raise AIServiceError(
            "GEMINI_MODEL is missing from the configuration."
        )

    today = date.today().isoformat()

    prompt = f"""
You are a task extraction assistant.

Today's date is {today}.

Extract task information from the user's text.

Return exactly one JSON object with these fields:

{{
    "title": "A concise task title",
    "due_date": "YYYY-MM-DD or null",
    "priority": "Low, Medium, or High",
    "notes": "Additional task details or an empty string"
}}

Rules:
1. The title must contain between 3 and 200 characters.
2. The due_date must be an ISO date in YYYY-MM-DD format or null.
3. Never invent a deadline. If the date is missing or ambiguous, use null.
4. Resolve relative dates only when they are unambiguous.
5. Priority must be exactly Low, Medium, or High.
6. Use Medium priority unless the user indicates otherwise.
7. Notes must be a string.
8. Do not include additional fields.
9. Return JSON only, without Markdown.

User's task:
{user_text}
"""

    url = GEMINI_URL.format(model=model)

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=35
        )

        if response.status_code in (401, 403):
            raise AIServiceError(
                "Gemini rejected the API key or access is unavailable. "
                "Check your API key and Google AI Studio project."
            )

        if response.status_code == 429:
            raise AIServiceError(
                "Gemini quota or rate limit reached. "
                "Check your API usage and try again later."
            )

        if response.status_code == 404:
            raise AIServiceError(
                f"Gemini model '{model}' was not found or is unavailable. "
                "Check the model name and availability."
            )

        response.raise_for_status()

        result = response.json()

        candidates = result.get("candidates", [])
        if not candidates:
            raise AIServiceError(
                "Gemini returned no response candidates."
            )

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts or not isinstance(parts[0].get("text"), str):
            raise AIServiceError(
                "Gemini returned no usable text response."
            )

        response_text = parts[0]["text"]

    except AIServiceError:
        raise

    except requests.Timeout as exc:
        raise AIServiceError(
            "Gemini request timed out. Please try again."
        ) from exc

    except requests.HTTPError as exc:
        raise AIServiceError(
            f"Gemini returned HTTP {response.status_code}. "
            "Check the API configuration and try again."
        ) from exc

    except requests.RequestException as exc:
        raise AIServiceError(
            "Could not connect to Gemini. "
            "Check your internet connection."
        ) from exc

    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise AIServiceError(
            "Could not read the Gemini response."
        ) from exc

    # Parse JSON returned by Gemini
    data = _extract_json(response_text)

    # Validate the result against the Pydantic schema
    try:
        return TaskExtraction.model_validate(data)

    except ValidationError as exc:
        raise AIServiceError(
            "Gemini returned data that does not match the task schema. "
            "Please try describing the task differently."
        ) from exc
