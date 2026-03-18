import pytest

from dark_core_lib.exceptions import TransactionError
from dark_core_lib.services.tx import send_contract_tx, send_native_transfer


class DummyTxHash:
    def hex(self):
        return "0xabc123"


class DummySignedSnake:
    raw_transaction = b"\x01\x02"


class DummySignedCamel:
    rawTransaction = b"\x03\x04"


class DummyAccountApi:
    def __init__(self, signed):
        self._signed = signed

    def sign_transaction(self, tx, key):
        return self._signed


class DummyEth:
    def __init__(self, signed):
        self.account = DummyAccountApi(signed)
        self.gas_price = 7

    def get_transaction_count(self, _address):
        return 3

    def send_raw_transaction(self, _raw):
        return DummyTxHash()

    def wait_for_transaction_receipt(self, _tx_hash, timeout):
        assert timeout == 120
        return {"status": 1, "gasUsed": 21000, "blockNumber": 11}


class DummyW3:
    def __init__(self, signed):
        self.eth = DummyEth(signed)


class DummyContractFunc:
    def build_transaction(self, payload):
        return {"to": "0x" + "a" * 40, **payload}


class DummyAccount:
    address = "0x" + "b" * 40
    key = "0x" + "1" * 64


def test_send_contract_tx_accepts_raw_transaction_attr():
    w3 = DummyW3(DummySignedSnake())
    receipt = send_contract_tx(
        w3=w3,
        contract_func=DummyContractFunc(),
        account=DummyAccount(),
        gas_limit=500000,
        timeout_seconds=120,
    )
    assert receipt.status == 1


def test_send_native_transfer_accepts_rawTransaction_attr():
    w3 = DummyW3(DummySignedCamel())
    receipt = send_native_transfer(
        w3=w3,
        sender_account=DummyAccount(),
        to_address="0x" + "c" * 40,
        amount_wei=123,
        timeout_seconds=120,
    )
    assert receipt.status == 1


def test_send_native_transfer_errors_when_no_raw_bytes_attr():
    w3 = DummyW3(object())
    with pytest.raises(TransactionError):
        send_native_transfer(
            w3=w3,
            sender_account=DummyAccount(),
            to_address="0x" + "c" * 40,
            amount_wei=123,
            timeout_seconds=120,
        )
