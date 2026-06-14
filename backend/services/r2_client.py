import json

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from config import Settings

# Key prefixes keep document text and metadata separate within the bucket.
CONTENT_PREFIX = "content/"
METADATA_PREFIX = "metadata/"


class R2Client:
    """Thin wrapper over the S3-compatible Cloudflare R2 API.

    Documents are stored as two objects: the raw text under ``content/<id>``
    and a metadata JSON document under ``metadata/<id>.json``. Listing reads
    the metadata objects; the text is fetched only when explicitly requested.
    """

    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.r2_bucket_name
        self._s3 = boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    @staticmethod
    def content_key(doc_id: str) -> str:
        return f"{CONTENT_PREFIX}{doc_id}"

    @staticmethod
    def metadata_key(doc_id: str) -> str:
        return f"{METADATA_PREFIX}{doc_id}.json"

    def put_text(self, key: str, text: str) -> None:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=text.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )

    def put_metadata(self, doc_id: str, document: dict) -> None:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self.metadata_key(doc_id),
            Body=json.dumps(document).encode("utf-8"),
            ContentType="application/json",
        )

    def get_text(self, key: str) -> str | None:
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            if _is_not_found(exc):
                return None
            raise
        return response["Body"].read().decode("utf-8")

    def get_metadata(self, doc_id: str) -> dict | None:
        try:
            response = self._s3.get_object(
                Bucket=self._bucket, Key=self.metadata_key(doc_id)
            )
        except ClientError as exc:
            if _is_not_found(exc):
                return None
            raise
        return json.loads(response["Body"].read())

    def list_metadata(self) -> list[dict]:
        documents: list[dict] = []
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=METADATA_PREFIX):
            for obj in page.get("Contents", []):
                body = self._s3.get_object(Bucket=self._bucket, Key=obj["Key"])
                documents.append(json.loads(body["Body"].read()))
        return documents

    def delete_document(self, doc_id: str, content_key: str) -> None:
        self._s3.delete_object(Bucket=self._bucket, Key=content_key)
        self._s3.delete_object(Bucket=self._bucket, Key=self.metadata_key(doc_id))


def _is_not_found(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code")
    return code in {"NoSuchKey", "404", "NotFound"}
