from __future__ import annotations

import os
from minio import Minio
from minio.error import S3Error
from pathlib import Path
from typing import Optional


def get_minio_client() -> Minio:
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def ensure_bucket(bucket: str) -> None:
    client = get_minio_client()
    found = client.bucket_exists(bucket)
    if not found:
        client.make_bucket(bucket)


def build_public_url(bucket: str, object_name: str) -> str:
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
    scheme = "https" if secure else "http"
    return f"{scheme}://{endpoint}/{bucket}/{object_name}"


def _local_fallback_path(object_name: str) -> Path:
    # save under static/uploads to be served by FastAPI
    local = Path("static/uploads") / object_name
    local.parent.mkdir(parents=True, exist_ok=True)
    return local


def upload_bytes(bucket: str, object_name: str, data: bytes, content_type: str) -> str:
    try:
        client = get_minio_client()
        ensure_bucket(bucket)
        client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=data,
            length=len(data),
            content_type=content_type,
        )
        return build_public_url(bucket, object_name)
    except Exception:
        # Fallback local: write into static/uploads and return app-relative URL
        local = _local_fallback_path(object_name)
        local.write_bytes(data)
        return f"/static/uploads/{object_name}"
