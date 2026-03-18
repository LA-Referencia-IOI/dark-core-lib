"""Public data models for dark-core-lib."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AuthorityInfo:
    """Information about a registered authority."""

    uuid: str
    wallet_address: str
    naans: list[str]
    active: bool


@dataclass
class ARKInfo:
    """Information about an ARK identifier."""

    naan: str
    name: str
    url: str
    cid: str
    owner: str
    created_at: datetime
    updated_at: datetime

    @property
    def ark_id(self) -> str:
        """Return fully qualified ARK identifier."""
        return f"ark:/{self.naan}/{self.name}"


@dataclass
class TxReceiptInfo:
    """Normalized transaction receipt info."""

    tx_hash: str
    status: int
    gas_used: Optional[int]
    block_number: Optional[int]
