"""Tests for ARK identifier helpers."""

import pytest

from dark_core_lib import parse_ark_id
from dark_core_lib.exceptions import ARKError


def test_parse_ark_id_accepts_classic_form():
    parsed = parse_ark_id("ark:/12345/abc")
    assert parsed.naan == "12345"
    assert parsed.name == "abc"
    assert parsed.canonical == "ark:12345/abc"


def test_parse_ark_id_accepts_compact_form():
    parsed = parse_ark_id("ark:12345/abc")
    assert parsed.naan == "12345"
    assert parsed.name == "abc"
    assert parsed.compact == "ark:12345/abc"


@pytest.mark.parametrize("value", ["", "12345/abc", "ark:/12345", "ark:/"])
def test_parse_ark_id_rejects_invalid_values(value):
    with pytest.raises(ARKError):
        parse_ark_id(value)


@pytest.mark.parametrize("value", ["ark://12345/abc", "ark:///12345/abc"])
def test_repeated_prefix_slashes_are_rejected(value):
    with pytest.raises(ARKError):
        parse_ark_id(value)


def test_level1_normalizes_classic_identifier():
    from dark_core_lib.metadata.schemas import Level1Metadata
    model = Level1Metadata(ark="ark:/12345/example", title="Example", authors=["A"],
        year=2026, original_metadata={"schema": "dc", "media_type": "text/plain"})
    assert model.model_dump()["ark"] == "ark:12345/example"
