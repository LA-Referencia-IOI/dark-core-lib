"""Chain utility service."""

from typing import Optional


class ChainService:
    """Read-only chain health and balance helpers."""

    def __init__(self, w3, admin_account=None):
        self.w3 = w3
        self.admin_account = admin_account

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    def get_block_number(self) -> int:
        return self.w3.eth.block_number

    def get_admin_balance(self) -> Optional[float]:
        if self.admin_account is None:
            return None
        balance_wei = self.w3.eth.get_balance(self.admin_account.address)
        return float(self.w3.from_wei(balance_wei, "ether"))
