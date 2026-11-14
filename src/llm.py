
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gemini-3.8-flash")

_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=3)
    ),
)


def ask_llm(prompt: str, system: str | None = None, json_mode: bool = False) -> str:
    """Call the primary model; on failure, try the fallback model."""
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json" if json_mode else None,
        temperature=0,
    )
    last_error = None
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            response = _client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response.text
        except Exception as e:  # noqa: BLE001
            last_error = e
    raise RuntimeError(f"All models failed: {last_error}")