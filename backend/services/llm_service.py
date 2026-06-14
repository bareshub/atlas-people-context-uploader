import json

import anthropic

from config import Settings
from schemas import InferredMetadata

# JSON Schema enforced by the Messages API via structured outputs. Keeping it
# explicit (rather than deriving from the Pydantic model) makes the exact
# contract sent to the model obvious to a reviewer. Must stay in sync with
# ``InferredMetadata``.
_METADATA_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "document_type": {"type": "string"},
        "time_period": {"type": "string"},
        "refers_to": {"type": "array", "items": {"type": "string"}},
        "key_topics": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "title",
        "summary",
        "document_type",
        "time_period",
        "refers_to",
        "key_topics",
    ],
    "additionalProperties": False,
}

_SYSTEM_PROMPT = (
    "You extract structured metadata from organisational context documents for "
    "Atlas People (company strategies, team objectives, job profiles, psychometric "
    "summaries, and similar). Infer concise, accurate metadata from the document. "
    "Use 'Not specified' for any string field you cannot determine, and an empty "
    "list when no people, teams, or topics apply. Do not invent details."
)


class LLMServiceError(RuntimeError):
    """Raised when metadata inference fails (API error or unparseable output)."""


class LLMService:
    """Infers document metadata with a single Anthropic Haiku call.

    Structured outputs guarantee the response is schema-valid JSON, so the
    backend can parse it directly without stripping markdown fences.
    """

    def __init__(self, settings: Settings) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        self._char_limit = settings.llm_input_char_limit

    def infer_metadata(self, filename: str, content: str) -> InferredMetadata:
        excerpt = content[: self._char_limit]
        truncated_note = "\n\n[document truncated for metadata inference]" if len(content) > self._char_limit else ""

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Filename: {filename}\n\n"
                            f"Document:\n{excerpt}{truncated_note}"
                        ),
                    }
                ],
                # Passed via extra_body so it reaches the wire regardless of the
                # installed SDK's typed-parameter surface.
                extra_body={
                    "output_config": {
                        "format": {"type": "json_schema", "schema": _METADATA_SCHEMA}
                    }
                },
            )
        except anthropic.APIError as exc:
            raise LLMServiceError(f"Anthropic API error: {exc}") from exc

        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMServiceError(f"Model returned non-JSON output: {text!r}") from exc

        return InferredMetadata.model_validate(data)
