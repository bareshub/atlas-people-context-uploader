import pytest
from fastapi.testclient import TestClient

from dependencies import get_llm_service, get_r2_client
from main import app
from schemas import InferredMetadata
from services.llm_service import LLMServiceError

SAMPLE_METADATA = InferredMetadata(
    title="2024 Growth Strategy",
    summary="Outlines the company's expansion plan for 2024.",
    document_type="Company Strategy",
    time_period="2024",
    refers_to=["Leadership Team"],
    key_topics=["expansion", "hiring"],
)


class FakeR2:
    """In-memory stand-in for R2Client used in tests."""

    def __init__(self) -> None:
        self.texts: dict[str, str] = {}
        self.metadata: dict[str, dict] = {}

    def put_text(self, key: str, text: str) -> None:
        self.texts[key] = text

    def put_metadata(self, doc_id: str, document: dict) -> None:
        self.metadata[doc_id] = document

    def get_text(self, key: str) -> str | None:
        return self.texts.get(key)

    def get_metadata(self, doc_id: str) -> dict | None:
        return self.metadata.get(doc_id)

    def list_metadata(self) -> list[dict]:
        return list(self.metadata.values())

    def delete_document(self, doc_id: str, content_key: str) -> None:
        self.texts.pop(content_key, None)
        self.metadata.pop(doc_id, None)


class StubLLM:
    """Returns fixed metadata, or raises when configured to fail."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def infer_metadata(self, filename: str, content: str) -> InferredMetadata:
        self.calls += 1
        if self.fail:
            raise LLMServiceError("boom")
        return SAMPLE_METADATA.model_copy()


@pytest.fixture
def fake_r2() -> FakeR2:
    return FakeR2()


@pytest.fixture
def stub_llm() -> StubLLM:
    return StubLLM()


@pytest.fixture
def client(fake_r2: FakeR2, stub_llm: StubLLM) -> TestClient:
    app.dependency_overrides[get_r2_client] = lambda: fake_r2
    app.dependency_overrides[get_llm_service] = lambda: stub_llm
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _upload(client: TestClient, name: str = "strategy.md", body: bytes = b"# Strategy\nGrow in 2024."):
    return client.post(
        "/api/documents", files={"file": (name, body, "text/markdown")}
    )


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_upload_infers_and_stores(client: TestClient, fake_r2: FakeR2, stub_llm: StubLLM) -> None:
    response = _upload(client)
    assert response.status_code == 201

    body = response.json()
    assert body["filename"] == "strategy.md"
    assert body["metadata"]["title"] == "2024 Growth Strategy"
    assert stub_llm.calls == 1
    # Both the text and metadata objects were persisted.
    assert body["id"] in fake_r2.metadata
    assert fake_r2.texts[body["content_key"]].startswith("# Strategy")


def test_upload_rejects_unsupported_extension(client: TestClient) -> None:
    response = _upload(client, name="resume.pdf")
    assert response.status_code == 400


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = _upload(client, body=b"   \n")
    assert response.status_code == 400


def test_upload_surfaces_llm_failure(fake_r2: FakeR2) -> None:
    failing_llm = StubLLM(fail=True)
    app.dependency_overrides[get_r2_client] = lambda: fake_r2
    app.dependency_overrides[get_llm_service] = lambda: failing_llm
    with TestClient(app) as client:
        response = _upload(client)
    app.dependency_overrides.clear()

    assert response.status_code == 502
    # Nothing should be stored when inference fails.
    assert fake_r2.metadata == {}


def test_list_documents(client: TestClient) -> None:
    _upload(client)
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_content(client: TestClient) -> None:
    doc_id = _upload(client).json()["id"]
    response = client.get(f"/api/documents/{doc_id}/content")
    assert response.status_code == 200
    assert response.json()["content"].startswith("# Strategy")


def test_patch_updates_metadata(client: TestClient) -> None:
    doc_id = _upload(client).json()["id"]
    corrected = SAMPLE_METADATA.model_copy(update={"title": "Corrected Title"})

    response = client.patch(f"/api/documents/{doc_id}", json=corrected.model_dump())
    assert response.status_code == 200
    assert response.json()["metadata"]["title"] == "Corrected Title"


def test_reinfer_metadata(client: TestClient, stub_llm: StubLLM) -> None:
    doc_id = _upload(client).json()["id"]
    response = client.post(f"/api/documents/{doc_id}/reinfer")
    assert response.status_code == 200
    assert stub_llm.calls == 2  # once on upload, once on re-infer


def test_delete_document(client: TestClient, fake_r2: FakeR2) -> None:
    doc_id = _upload(client).json()["id"]
    assert client.delete(f"/api/documents/{doc_id}").status_code == 204
    assert fake_r2.metadata == {}


def test_missing_document_returns_404(client: TestClient) -> None:
    assert client.get("/api/documents/nope/content").status_code == 404
    assert client.patch(
        "/api/documents/nope", json=SAMPLE_METADATA.model_dump()
    ).status_code == 404
