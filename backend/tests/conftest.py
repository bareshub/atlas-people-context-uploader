import os

# Settings are validated at import time (the CORS middleware reads them), so
# dummy credentials must exist before `main` is imported. The real R2 and
# Anthropic clients are never constructed because the tests override the
# dependencies with mocks.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("R2_ACCOUNT_ID", "test-account")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-access")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-secret")
os.environ.setdefault("R2_BUCKET_NAME", "test-bucket")
