import os
import re
import time

from google import genai
from app.config import get_settings


def _is_transient_error(exc: Exception) -> bool:
    """Retry server-side Gemini failures, but never client/auth failures."""
    for attr in ("status_code", "code"):
        status = getattr(exc, attr, None)
        if isinstance(status, int):
            return 500 <= status <= 599
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return 500 <= status <= 599

    message = str(exc)
    if re.search(r"\b[1-5]\d\d\b", message):
        codes = [int(code) for code in re.findall(r"\b[1-5]\d\d\b", message)]
        return any(500 <= code <= 599 for code in codes)
    return "unavailable" in message.lower()


class GeminiClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        settings = get_settings()
        api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set in config or environment."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = settings.gemini_model

    def generate_structured(self, prompt: str, schema: type) -> any:
        """
        Generate structured output matching the provided Pydantic schema.

        Retries temporary Gemini 5xx/unavailable errors with exponential
        backoff. Permanent errors are raised immediately.
        """

        max_attempts = 3
        delays = [0.5, 1.0]

        for attempt in range(max_attempts):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )

                return schema.model_validate_json(response.text)

            except Exception as exc:
                if not _is_transient_error(exc) or attempt == max_attempts - 1:
                    raise

                time.sleep(delays[attempt])


def get_llm_client() -> GeminiClient:
    return GeminiClient()
