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


@dataclass
class ChainCapacityInfo:
    """Semantic blockchain capacity snapshot for write pacing."""

    available: bool
    state: str
    recommended_page_size: int
    max_page_size: int
    reason: str
    block_number: Optional[int]
    txpool_pending: Optional[int] = None


@dataclass
class ARKPublishOperation:
    """Semantic ARK write operation for pipelined publication."""

    ref: str
    action: str
    naan: str
    name: str
    url: str
    cid: str


@dataclass
class ARKPublishResult:
    """Semantic result for one pipelined ARK write operation."""

    ref: str
    action: str
    status: str
    error: Optional[str] = None
    gas_limit: Optional[int] = None
    gas_used: Optional[int] = None
    gas_estimate: Optional[int] = None
