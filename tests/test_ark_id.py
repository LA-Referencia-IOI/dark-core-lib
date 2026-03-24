"""Tests for ARK identifier helpers."""

import pytest

from dark_core_lib import parse_ark_id
from dark_core_lib.exceptions import ARKError


def test_parse_ark_id_accepts_classic_form():
    parsed = parse_ark_id("ark:/12345/abc")
    assert parsed.naan == "12345"
    assert parsed.name == "abc"
    assert parsed.canonical == "ark:/12345/abc"


def test_parse_ark_id_accepts_compact_form():
    parsed = parse_ark_id("ark:12345/abc")
    assert parsed.naan == "12345"
    assert parsed.name == "abc"
    assert parsed.compact == "ark:12345/abc"


@pytest.mark.parametrize("value", ["", "12345/abc", "ark:/12345", "ark:/"])
def test_parse_ark_id_rejects_invalid_values(value):
    with pytest.raises(ARKError):
        parse_ark_id(value)
