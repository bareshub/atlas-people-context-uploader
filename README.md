# Atlas People Context Uploader

A small full-stack feature for uploading organisational context documents. A user
drops in a plain-text or Markdown file; the backend stores it in Cloudflare R2,
asks Claude Haiku to infer metadata (title, time period, what it refers to, a
summary, key topics), and the UI shows every document with its metadata for the
user to review and correct.

## What it does

- **Upload** `.txt` / `.md` via drag-and-drop or file picker.
- **Store** the raw text and a metadata JSON object in R2 (no separate database).
- **Infer** metadata on upload with `claude-haiku-4-5`, using the Messages API's
  **structured outputs** so the response is guaranteed schema-valid JSON.
- **Review & correct** every field inline, then save. Also: **re-infer** on demand
  and **delete**.

## Run it

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env        # then fill in your Anthropic + R2 credentials
docker compose up --build
```

Open **http://localhost:3000**. The frontend (nginx) proxies `/api` to the backend.

### Option B — run the two services directly

**Backend** (Python 3.13):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# export the same vars as .env.example, then:
uvicorn main:app --reload --port 8000
```

**Frontend** (Node 24):

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000, proxies /api → localhost:8000
```

## Configuration

All backend config comes from environment variables (see `.env.example`):

| Variable | Description |
| --- | --- |
| `ANTHROPIC_API_KEY` | Anthropic API key. |
| `ANTHROPIC_MODEL` | Inference model (default `claude-haiku-4-5`). |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | R2 (S3-compatible) credentials. |
| `R2_BUCKET_NAME` | Target bucket. |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins. |

## Provisioning the bucket (optional)

`infra/` holds Terraform for the R2 bucket:

```bash
cd infra
export TF_VAR_cloudflare_account_id=...
export TF_VAR_cloudflare_api_token=...      # token with R2 read/write
terraform init && terraform apply
```

## Tests

```bash
cd backend && pytest -q
```

The tests mock R2 and Anthropic via FastAPI dependency overrides, so they need no
real credentials or network access. CI (`.github/workflows/ci.yml`) runs them and
validates both Docker images build.

## Layout

```txt
backend/    FastAPI app — routes (main.py), config, schemas, services/{r2_client,llm_service}, tests
frontend/   React + Vite + Tailwind — App, components/{Dropzone,MetadataForm}, api/client
infra/      Terraform for the R2 bucket
```

## Notes & trade-offs

- **Storage:** each document is two R2 objects — `content/<id>` (text) and
  `metadata/<id>.json` (metadata). Listing reads the metadata objects. This keeps
  the stack to a single storage provider with no database; at larger scale the
  metadata would move to an indexed store (e.g. D1/Postgres) so listing isn't N+1
  reads.
- **Model:** `claude-haiku-4-5` with structured outputs — the brief suggested an
  older Haiku snapshot that is now retired, and structured outputs remove the need
  to defensively parse free-form JSON.
- **Auth:** out of scope for this exercise — there is no user/tenant model.
