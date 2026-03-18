from datetime import datetime, timezone

from dark_core_lib.models import ARKInfo


def test_ark_id_property():
    ark = ARKInfo(
        naan="12345",
        name="doc-001",
        url="https://example.org",
        cid="Qm123",
        owner="0x" + "a" * 40,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert ark.ark_id == "ark:/12345/doc-001"
