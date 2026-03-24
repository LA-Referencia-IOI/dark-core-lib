"""HTTP metadata storage backend backed by dark-store-api."""

import logging
from typing import Optional
from urllib.parse import quote

import httpx

from dark_core_lib.metadata.storage.base import MetadataStorage, StoredDocument
from dark_core_lib.metadata.storage.exceptions import MetadataNotFoundError, StorageError


logger = logging.getLogger(__name__)


def _extract_error_detail(response: httpx.Response) -> str:
    """Extract a readable error message from an HTTP response."""
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail

    text = response.text.strip()
    return text or f"HTTP {response.status_code}"


class StoreApiMetadataStorage(MetadataStorage):
    """Metadata storage implementation backed by a remote store API."""

    def __init__(self, base_url: str, timeout_seconds: float = 10.0):
        if not base_url:
            raise ValueError("Store API base_url cannot be empty")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def store_document(
        self,
        content: bytes,
        content_type: str,
        schema: Optional[str] = None,
    ) -> str:
        url = f"{self.base_url}/v1/store"
        headers = {"Content-Type": content_type}
        if schema:
            headers["X-Metadata-Schema"] = schema

        try:
            response = httpx.post(
                url,
                content=content,
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except httpx.RequestError as exc:
            raise StorageError(f"Store API request failed: {exc}") from exc

        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise StorageError(f"Store API store failed ({response.status_code}): {detail}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise StorageError("Store API returned invalid JSON response") from exc

        cid = payload.get("cid") if isinstance(payload, dict) else None
        if not isinstance(cid, str) or not cid:
            raise StorageError("Store API response missing CID")
        return cid

    def get_document(self, cid: str) -> StoredDocument:
        url = f"{self.base_url}/v1/retrieve/{quote(cid, safe='')}"
        try:
            response = httpx.get(url, timeout=self.timeout_seconds)
        except httpx.RequestError as exc:
            raise StorageError(f"Store API request failed: {exc}") from exc

        if response.status_code == 404:
            raise MetadataNotFoundError(f"Metadata not found for CID: {cid}")
        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise StorageError(f"Store API retrieve failed ({response.status_code}): {detail}")

        content_type = response.headers.get("content-type", "application/octet-stream")
        content_type = content_type.split(";", 1)[0].strip()
        return StoredDocument(content=response.content, content_type=content_type)

    def health_check(self) -> bool:
        url = f"{self.base_url}/health"
        try:
            response = httpx.get(url, timeout=self.timeout_seconds)
        except Exception as exc:
            logger.warning(f"Store API health check failed: {exc}")
            return False

        if response.status_code != 200:
            return False

        try:
            payload = response.json()
        except ValueError:
            return False

        if not isinstance(payload, dict):
            return False

        if "backend_healthy" in payload:
            return bool(payload["backend_healthy"])
        return payload.get("status") == "healthy"
