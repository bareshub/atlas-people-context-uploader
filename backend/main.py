import uuid
from datetime import datetime, timezone

from botocore.exceptions import ClientError
from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from dependencies import get_llm_service, get_r2_client
from schemas import Document, DocumentContent, InferredMetadata
from services.llm_service import LLMService, LLMServiceError
from services.r2_client import R2Client

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown"}

app = FastAPI(title="Atlas Context Uploader", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/documents", response_model=Document, status_code=201)
async def upload_document(
    file: UploadFile,
    r2: R2Client = Depends(get_r2_client),
    llm: LLMService = Depends(get_llm_service),
) -> Document:
    """Store a text/markdown document and infer its metadata via the LLM."""
    filename = file.filename or "untitled.txt"
    _validate_extension(filename)

    raw = await file.read()
    settings = get_settings()
    if len(raw) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_file_size_bytes} byte limit.",
        )

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc

    if not content.strip():
        raise HTTPException(status_code=400, detail="File is empty.")

    try:
        metadata = llm.infer_metadata(filename, content)
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    doc_id = uuid.uuid4().hex
    document = Document(
        id=doc_id,
        filename=filename,
        content_key=R2Client.content_key(doc_id),
        size_bytes=len(raw),
        metadata=metadata,
    )

    try:
        r2.put_text(document.content_key, content)
        r2.put_metadata(doc_id, document.model_dump())
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Storage error: {exc}") from exc

    return document


@app.get("/api/documents", response_model=list[Document])
def list_documents(r2: R2Client = Depends(get_r2_client)) -> list[Document]:
    """List all stored documents, newest first."""
    try:
        records = r2.list_metadata()
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Storage error: {exc}") from exc

    documents = [Document.model_validate(record) for record in records]
    documents.sort(key=lambda d: d.uploaded_at, reverse=True)
    return documents


@app.get("/api/documents/{doc_id}/content", response_model=DocumentContent)
def get_document_content(
    doc_id: str, r2: R2Client = Depends(get_r2_client)
) -> DocumentContent:
    """Return the stored text of a document."""
    document = _load_document(r2, doc_id)
    content = r2.get_text(document.content_key)
    if content is None:
        raise HTTPException(status_code=404, detail="Document content not found.")
    return DocumentContent(id=doc_id, content=content)


@app.patch("/api/documents/{doc_id}", response_model=Document)
def update_metadata(
    doc_id: str,
    metadata: InferredMetadata,
    r2: R2Client = Depends(get_r2_client),
) -> Document:
    """Replace a document's metadata with user-corrected values."""
    document = _load_document(r2, doc_id)
    document.metadata = metadata
    document.updated_at = datetime.now(timezone.utc).isoformat()

    try:
        r2.put_metadata(doc_id, document.model_dump())
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Storage error: {exc}") from exc

    return document


@app.post("/api/documents/{doc_id}/reinfer", response_model=Document)
def reinfer_metadata(
    doc_id: str,
    r2: R2Client = Depends(get_r2_client),
    llm: LLMService = Depends(get_llm_service),
) -> Document:
    """Stretch goal: re-run metadata inference on a stored document."""
    document = _load_document(r2, doc_id)
    content = r2.get_text(document.content_key)
    if content is None:
        raise HTTPException(status_code=404, detail="Document content not found.")

    try:
        document.metadata = llm.infer_metadata(document.filename, content)
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    document.updated_at = datetime.now(timezone.utc).isoformat()
    try:
        r2.put_metadata(doc_id, document.model_dump())
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Storage error: {exc}") from exc

    return document


@app.delete("/api/documents/{doc_id}", status_code=204)
def delete_document(doc_id: str, r2: R2Client = Depends(get_r2_client)) -> None:
    """Delete a document and its metadata."""
    document = _load_document(r2, doc_id)
    try:
        r2.delete_document(doc_id, document.content_key)
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Storage error: {exc}") from exc


def _validate_extension(filename: str) -> None:
    lowered = filename.lower()
    if not any(lowered.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Only plain text or markdown files (.txt, .md) are supported.",
        )


def _load_document(r2: R2Client, doc_id: str) -> Document:
    record = r2.get_metadata(doc_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return Document.model_validate(record)
