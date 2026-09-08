"""HTTP metadata storage backend backed by dark-store-api."""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import httpx

from dark_core_lib.metadata.storage.base import MetadataStorage, ReplicationStatus, StoredDocument
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
        self.client = httpx.Client(
            timeout=timeout_seconds,
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
        )

    def store_document(
        self,
        content: bytes,
        content_type: str,
        schema: Optional[str] = None,
    ) -> str:
        url = f"{self.base_url}/v1/store"
        headers = {"Content-Type": content_type}

        try:
            response = self.client.post(
                url,
                content=content,
                headers=headers,
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
            response = self.client.get(url)
        except httpx.RequestError as exc:
            raise StorageError(f"Store API request failed: {exc}") from exc

        if response.status_code == 404:
            raise MetadataNotFoundError(f"Metadata not found for CID: {cid}")
        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise StorageError(f"Store API retrieve failed ({response.status_code}): {detail}")

        content_type = response.headers.get("content-type", "application/octet-stream")
        content_type = content_type.split(";", 1)[0].strip()
        schema_header = response.headers.get("x-metadata-schema")
        schema = schema_header.strip() if isinstance(schema_header, str) and schema_header.strip() else None
        return StoredDocument(content=response.content, content_type=content_type, schema=schema)

    def health_check(self) -> bool:
        url = f"{self.base_url}/health"
        try:
            response = self.client.get(url)
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

    def get_replication_status(self, cid: str) -> ReplicationStatus:
        """Read the live per-site replication snapshot for a CID."""
        url = f"{self.base_url}/v1/status/{quote(cid, safe='')}"
        try:
            response = self.client.get(url)
        except httpx.RequestError as exc:
            raise StorageError(f"Store API request failed: {exc}") from exc
        if response.status_code == 404:
            return ReplicationStatus(
                cid=cid,
                status="unpinned",
                total_replicas=0,
            )
        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise StorageError(f"Store API status failed ({response.status_code}): {detail}")
        try:
            payload = response.json()
            return self._replication_status_from_payload(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageError(f"Store API returned invalid status response: {exc}") from exc

    @staticmethod
    def _replication_status_from_payload(payload: dict) -> ReplicationStatus:
        replication = payload["replication"]
        checked_at_value = replication.get("checked_at")
        checked_at = (
            datetime.fromisoformat(
                checked_at_value[:-1] + "+00:00"
                if isinstance(checked_at_value, str) and checked_at_value.endswith("Z")
                else checked_at_value
            )
            if checked_at_value
            else None
        )
        return ReplicationStatus(
            cid=str(payload["cid"]),
            status=str(payload["status"]),
            total_replicas=int(replication["total_replicas"]),
            queued_replicas=int(replication.get("queued_replicas", 0) or 0),
            pinning_replicas=int(replication.get("pinning_replicas", 0) or 0),
            error_replicas=int(replication.get("error_replicas", 0) or 0),
            assigned_replicas=int(replication.get("assigned_replicas", 0) or 0),
            checked_at=checked_at,
        )

    def get_replication_statuses(self, cids: list[str]) -> dict[str, ReplicationStatus]:
        unique_cids = list(dict.fromkeys(cid for cid in cids if cid))
        if not unique_cids:
            return {}
        try:
            response = self.client.post(f"{self.base_url}/v1/status/batch", json={"cids": unique_cids})
        except httpx.RequestError as exc:
            raise StorageError(f"Store API batch status request failed: {exc}") from exc
        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise StorageError(f"Store API batch status failed ({response.status_code}): {detail}")
        try:
            payload = response.json()
            return {
                str(row["cid"]): self._replication_status_from_payload(row)
                for row in payload["statuses"]
                if isinstance(row, dict)
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageError(f"Store API returned invalid batch status response: {exc}") from exc

    def ensure_replication(self, cids: list[str], target_replicas: int) -> dict[str, str]:
        unique_cids = list(dict.fromkeys(cid for cid in cids if cid))
        if not unique_cids:
            return {}
        try:
            response = self.client.post(
                f"{self.base_url}/v1/replication/ensure",
                json={"cids": unique_cids, "target_replicas": target_replicas},
            )
        except httpx.RequestError as exc:
            raise StorageError(f"Store API replication promotion failed: {exc}") from exc
        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise StorageError(f"Store API replication promotion failed ({response.status_code}): {detail}")
        try:
            payload = response.json()
            return {str(cid): str(status) for cid, status in payload["results"].items()}
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageError(f"Store API returned invalid replication response: {exc}") from exc

    def close(self) -> None:
        self.client.close()
