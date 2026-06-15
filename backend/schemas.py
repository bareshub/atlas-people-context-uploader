from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InferredMetadata(BaseModel):
    """Metadata inferred from a document by the LLM and editable by the user.

    The JSON schema sent to the model lives in ``services/llm_service.py`` and
    must stay in sync with these fields.
    """

    title: str = Field(description="Concise, human-readable document title.")
    summary: str = Field(description="Two or three sentence summary of the document.")
    document_type: str = Field(
        description="Category, e.g. 'Company Strategy', 'Team Objectives', 'Job Profile'."
    )
    time_period: str = Field(
        description="Time period the document covers, e.g. 'Q1 2026' or 'Not specified'."
    )
    refers_to: list[str] = Field(
        default_factory=list,
        description="People, teams, or organisations the document is about.",
    )
    key_topics: list[str] = Field(
        default_factory=list, description="Salient topics or themes."
    )


class Document(BaseModel):
    """A stored document plus its inferred metadata."""

    id: str
    filename: str
    content_key: str
    size_bytes: int
    uploaded_at: str = Field(default_factory=_utcnow_iso)
    updated_at: str = Field(default_factory=_utcnow_iso)
    metadata: InferredMetadata


class DocumentContent(BaseModel):
    """A document's stored text, returned on demand."""

    id: str
    content: str
