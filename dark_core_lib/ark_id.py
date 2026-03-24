"""Helpers for parsing and normalizing ARK identifiers."""

from dataclasses import dataclass

from dark_core_lib.exceptions import ARKError


@dataclass(frozen=True)
class ARKIdentifier:
    """Normalized representation of an ARK identifier."""

    naan: str
    name: str

    @property
    def canonical(self) -> str:
        """Return the canonical classic ARK representation."""
        return f"ark:/{self.naan}/{self.name}"

    @property
    def compact(self) -> str:
        """Return the compact ARK representation."""
        return f"ark:{self.naan}/{self.name}"


def parse_ark_id(raw: str) -> ARKIdentifier:
    """Parse an ARK identifier in compact or classic form."""
    if not isinstance(raw, str):
        raise ARKError("ARK identifier must be a string")

    candidate = raw.strip()
    if not candidate:
        raise ARKError("ARK identifier cannot be empty")
    if not candidate.startswith("ark:"):
        raise ARKError(f"Invalid ARK identifier: {raw}")

    suffix = candidate[4:].lstrip("/")
    parts = suffix.split("/", 1)
    if len(parts) != 2:
        raise ARKError(f"Invalid ARK identifier: {raw}")

    naan, name = parts[0].strip(), parts[1].strip()
    if not naan or not name:
        raise ARKError(f"Invalid ARK identifier: {raw}")

    return ARKIdentifier(naan=naan, name=name)
