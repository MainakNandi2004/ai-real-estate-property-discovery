from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from app.ai.llm_client import GeminiClient


class StructuredPayload(BaseModel):
    value: str


class GeminiError(Exception):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


@pytest.fixture
def client():
    instance = object.__new__(GeminiClient)
    instance.client = MagicMock()
    instance.model = "test-model"
    return instance


def test_retries_transient_server_errors_at_most_three_times(client):
    client.client.models.generate_content.side_effect = [
        GeminiError("temporarily unavailable", 503),
        GeminiError("internal error", 500),
        GeminiError("still unavailable", 503),
    ]
    with patch("app.ai.llm_client.time.sleep") as sleep:
        with pytest.raises(GeminiError):
            client.generate_structured("prompt", StructuredPayload)

    assert client.client.models.generate_content.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [0.5, 1.0]


def test_does_not_retry_permanent_client_error(client):
    client.client.models.generate_content.side_effect = GeminiError("invalid API key", 401)

    with patch("app.ai.llm_client.time.sleep") as sleep:
        with pytest.raises(GeminiError):
            client.generate_structured("prompt", StructuredPayload)

    client.client.models.generate_content.assert_called_once()
    sleep.assert_not_called()


def test_preserves_structured_output_validation(client):
    client.client.models.generate_content.return_value.text = '{"value": "parsed"}'

    assert client.generate_structured("prompt", StructuredPayload) == StructuredPayload(value="parsed")
