"""Tests for the pooled Store API metadata backend."""

from unittest.mock import Mock

import httpx

from dark_core_lib.metadata import StoreApiMetadataStorage


def _response(method: str, url: str, status_code: int, payload=None) -> httpx.Response:
    return httpx.Response(
        status_code,
        request=httpx.Request(method, url),
        json=payload,
    )


def test_reuses_client_for_store_status_and_close():
    storage = StoreApiMetadataStorage("http://store-api:8003")
    client = Mock()
    client.post.return_value = _response(
        "POST", "http://store-api:8003/v1/store", 200, {"cid": "bafy", "size": 4}
    )
    client.get.return_value = _response(
        "GET",
        "http://store-api:8003/v1/status/bafy",
        200,
        {
            "cid": "bafy",
            "status": "pinned",
            "replication": {
                "total_replicas": 3,
                "local_replicas": 2,
                "remote_replicas": 1,
                "sites": {"site-a": 2, "site-b": 1},
                "purge_target_met": True,
                "checked_at": "2026-08-21T12:00:00+00:00",
            },
        },
    )
    original_client = storage.client
    original_client.close()
    storage.client = client

    assert storage.store_document(b"data", "application/json") == "bafy"
    status = storage.get_replication_status("bafy")
    assert status.total_replicas == 3
    assert status.checked_at is not None

    storage.close()
    client.close.assert_called_once_with()


def test_missing_status_is_zero_copy_and_not_purgeable():
    storage = StoreApiMetadataStorage("http://store-api:8003")
    client = Mock()
    client.get.return_value = _response(
        "GET", "http://store-api:8003/v1/status/missing", 404, {"detail": "missing"}
    )
    original_client = storage.client
    original_client.close()
    storage.client = client

    status = storage.get_replication_status("missing")

    assert status.total_replicas == 0
    assert status.status == "unpinned"
    storage.close()


def test_replication_status_accepts_rfc3339_utc_z_suffix():
    storage = StoreApiMetadataStorage("http://store-api:8003")
    client = Mock()
    client.get.return_value = _response(
        "GET",
        "http://store-api:8003/v1/status/bafy",
        200,
        {
            "cid": "bafy",
            "status": "pinned",
            "replication": {
                "total_replicas": 2,
                "checked_at": "2026-09-06T17:06:20.460243Z",
            },
        },
    )
    storage.client.close()
    storage.client = client

    status = storage.get_replication_status("bafy")

    assert status.total_replicas == 2
    assert status.checked_at is not None
    assert status.checked_at.utcoffset().total_seconds() == 0
    storage.close()
