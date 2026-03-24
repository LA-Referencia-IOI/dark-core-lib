from __future__ import annotations

from pathlib import Path

from dark_core_lib.metadata import MetadataService, StoredDocument
from dark_core_lib.metadata.storage import FileSystemMetadataStorage


class InMemoryStorage:
    def __init__(self):
        self.documents = {}

    def store_document(self, content: bytes, content_type: str, schema: str | None = None) -> str:
        cid = f"cid-{len(self.documents) + 1}"
        self.documents[cid] = StoredDocument(content=content, content_type=content_type, schema=schema)
        return cid

    def get_document(self, cid: str) -> StoredDocument:
        return self.documents[cid]

    def health_check(self) -> bool:
        return True


def test_store_level1_with_level2_reference_injects_internal_cid():
    storage = InMemoryStorage()
    service = MetadataService(storage)

    level1, level1_cid = service.store_level1_with_level2_reference(
        {
            "title": "My record",
            "authors": ["Ada Lovelace"],
            "year": 2026,
            "original_metadata": {
                "schema": "datacite",
                "media_type": "application/xml",
            },
        },
        "internal-level2-cid",
    )

    assert level1.original_metadata.cid == "internal-level2-cid"
    stored = storage.get_document(level1_cid)
    assert stored.content_type == "application/json"
    assert b'"cid": "internal-level2-cid"' in stored.content


def test_load_level2_reads_document_from_level1_reference():
    storage = InMemoryStorage()
    service = MetadataService(storage)

    level2_cid = storage.store_document(
        b"<record><title>Demo</title></record>",
        content_type="application/xml",
        schema="datacite",
    )
    level1_cid = storage.store_document(
        (
            b'{"$schema":"x","schema_version":"1.0","title":"Demo","authors":["A"],'
            b'"year":2026,"original_metadata":{"schema":"datacite","media_type":"application/xml","cid":"'
            + level2_cid.encode("utf-8")
            + b'"}}'
        ),
        content_type="application/octet-stream",
    )

    level1 = service.load_level1(level1_cid)
    level2 = service.load_level2(level1)

    assert level2.content == b"<record><title>Demo</title></record>"
    assert level2.content_type == "application/xml"


def test_filesystem_storage_health_check_accepts_read_only_mode(tmp_path: Path):
    storage = FileSystemMetadataStorage(str(tmp_path), read_only=True)

    assert storage.health_check() is True
