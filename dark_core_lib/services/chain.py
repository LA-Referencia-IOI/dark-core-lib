"""Chain utility service."""

import time
from typing import Optional

from dark_core_lib.models import ChainCapacityInfo


class ChainService:
    """Read-only chain health and balance helpers."""

    def __init__(self, w3, admin_account=None):
        self.w3 = w3
        self.admin_account = admin_account
        self._last_capacity_block_number: Optional[int] = None
        self._last_capacity_block_progress_monotonic = time.monotonic()

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    def get_block_number(self) -> int:
        return self.w3.eth.block_number

    def get_capacity(
        self, max_page_size: int = 20, *, include_txpool: bool = True
    ) -> ChainCapacityInfo:
        """Return a semantic capacity recommendation for chain writes."""
        safe_max = max(int(max_page_size or 0), 1)
        min_page_size = 1

        try:
            if not self.is_connected():
                return ChainCapacityInfo(
                    available=False,
                    state="unavailable",
                    recommended_page_size=0,
                    max_page_size=safe_max,
                    reason="RPC is not connected",
                    block_number=None,
                    txpool_pending=None,
                )

            block_number = int(self.get_block_number())
        except Exception as exc:
            return ChainCapacityInfo(
                available=False,
                state="unavailable",
                recommended_page_size=0,
                max_page_size=safe_max,
                reason=f"Failed to read block number: {exc}",
                block_number=None,
                txpool_pending=None,
            )

        now = time.monotonic()
        if (
            self._last_capacity_block_number is None
            or block_number != self._last_capacity_block_number
        ):
            self._last_capacity_block_number = block_number
            self._last_capacity_block_progress_monotonic = now

        block_age_seconds = now - self._last_capacity_block_progress_monotonic
        txpool_pending = self._read_txpool_pending() if include_txpool else None

        txpool_high_watermark = max(safe_max * 2, 40)
        txpool_pause_watermark = max(safe_max * 5, 100)
        slow_block_seconds = 30
        stalled_block_seconds = 120

        if block_age_seconds >= stalled_block_seconds:
            return ChainCapacityInfo(
                available=True,
                state="stalled",
                recommended_page_size=0,
                max_page_size=safe_max,
                reason=f"Block {block_number} has not advanced for {int(block_age_seconds)}s",
                block_number=block_number,
                txpool_pending=txpool_pending,
            )

        if txpool_pending is not None and txpool_pending >= txpool_pause_watermark:
            return ChainCapacityInfo(
                available=True,
                state="congested",
                recommended_page_size=0,
                max_page_size=safe_max,
                reason=f"Txpool pending {txpool_pending} >= pause watermark {txpool_pause_watermark}",
                block_number=block_number,
                txpool_pending=txpool_pending,
            )

        if block_age_seconds >= slow_block_seconds:
            return ChainCapacityInfo(
                available=True,
                state="slow",
                recommended_page_size=max(min_page_size, safe_max // 4),
                max_page_size=safe_max,
                reason=f"Block {block_number} has not advanced for {int(block_age_seconds)}s",
                block_number=block_number,
                txpool_pending=txpool_pending,
            )

        if txpool_pending is not None and txpool_pending >= txpool_high_watermark:
            return ChainCapacityInfo(
                available=True,
                state="congested",
                recommended_page_size=max(min_page_size, safe_max // 2),
                max_page_size=safe_max,
                reason=f"Txpool pending {txpool_pending} >= high watermark {txpool_high_watermark}",
                block_number=block_number,
                txpool_pending=txpool_pending,
            )

        reason = "Chain capacity is healthy"
        if txpool_pending is None:
            reason = "Chain capacity is healthy; txpool statistics unavailable"

        return ChainCapacityInfo(
            available=True,
            state="healthy",
            recommended_page_size=safe_max,
            max_page_size=safe_max,
            reason=reason,
            block_number=block_number,
            txpool_pending=txpool_pending,
        )

    def _read_txpool_pending(self) -> Optional[int]:
        """Read pending txpool size from Besu-compatible RPC methods."""
        provider = getattr(self.w3, "provider", None)
        make_request = getattr(provider, "make_request", None)
        if make_request is None:
            return None

        for method in ("txpool_besuStatistics", "txpool_status"):
            try:
                response = make_request(method, [])
            except Exception:
                continue

            if not isinstance(response, dict) or response.get("error"):
                continue

            pending = self._extract_txpool_pending(response.get("result"))
            if pending is not None:
                return pending

        return None

    @classmethod
    def _extract_txpool_pending(cls, result) -> Optional[int]:
        if not isinstance(result, dict):
            return None

        pending = cls._first_int(
            result,
            (
                "pending",
                "pendingCount",
                "pending_count",
                "pendingTransactions",
                "pendingTransactionCount",
            ),
        )
        queued = cls._first_int(
            result,
            (
                "queued",
                "queuedCount",
                "queued_count",
                "queuedTransactions",
                "queuedTransactionCount",
            ),
        )
        if pending is not None:
            return pending + (queued or 0)

        local = cls._first_int(result, ("localCount", "local_count"))
        remote = cls._first_int(result, ("remoteCount", "remote_count"))
        if local is not None or remote is not None:
            return (local or 0) + (remote or 0)

        return None

    @staticmethod
    def _first_int(result: dict, keys: tuple[str, ...]) -> Optional[int]:
        for key in keys:
            if key in result:
                value = ChainService._to_int(result[key])
                if value is not None:
                    return value
        return None

    @staticmethod
    def _to_int(value) -> Optional[int]:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value, 16) if value.startswith("0x") else int(value)
            except ValueError:
                return None
        return None

    def get_admin_balance(self) -> Optional[float]:
        if self.admin_account is None:
            return None
        balance_wei = self.w3.eth.get_balance(self.admin_account.address)
        return float(self.w3.from_wei(balance_wei, "ether"))
