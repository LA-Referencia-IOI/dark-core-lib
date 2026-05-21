from types import SimpleNamespace
from unittest.mock import Mock, patch

from dark_core_lib.models import ARKInfo, ARKPublishOperation, TxReceiptInfo
from dark_core_lib.services.ark import ARKService


def _build_service():
    account = SimpleNamespace(address="0x" + "a" * 40, key="0x" + "1" * 64)
    w3 = SimpleNamespace(
        eth=SimpleNamespace(
            account=SimpleNamespace(from_key=Mock(return_value=account)),
        )
    )
    contract_func = Mock()
    contract = SimpleNamespace(
        functions=SimpleNamespace(
            create_ark=Mock(return_value=contract_func),
            update_ark=Mock(return_value=contract_func),
        )
    )
    config = SimpleNamespace(read_only=False, default_gas_limit=500000, tx_timeout_seconds=120)
    authority_service = Mock()
    authority_service.get_signing_credentials.return_value = ("0x" + "b" * 40, account.key)
    return ARKService(w3, contract, config, authority_service), contract_func


def _ark_info(name="name", url="https://example.com", cid="cid"):
    return ARKInfo(
        naan="12345",
        name=name,
        url=url,
        cid=cid,
        owner="0x" + "c" * 40,
        created_at=None,
        updated_at=None,
    )


def test_create_returns_ark_info_by_default_without_exists():
    service, contract_func = _build_service()
    service.exists = Mock(side_effect=AssertionError("exists should not be called"))
    service.get = Mock(return_value=_ark_info())
    receipt = TxReceiptInfo(tx_hash="0xabc", status=1, gas_used=21000, block_number=12)

    with patch("dark_core_lib.services.ark.send_contract_tx", return_value=receipt) as send_tx:
        result = service.create("auth-uuid", "12345", "name", "https://example.com", "cid")

    assert result == service.get.return_value
    service.get.assert_called_once_with("12345", "name")
    send_tx.assert_called_once_with(
        service.w3,
        contract_func,
        service.w3.eth.account.from_key.return_value,
        gas_limit=500000,
        timeout_seconds=120,
    )


def test_create_fetch_result_false_skips_get():
    service, contract_func = _build_service()
    service.exists = Mock(side_effect=AssertionError("exists should not be called"))
    service.get = Mock(side_effect=AssertionError("get should not be called"))
    receipt = TxReceiptInfo(tx_hash="0xabc", status=1, gas_used=21000, block_number=12)

    with patch("dark_core_lib.services.ark.send_contract_tx", return_value=receipt) as send_tx:
        result = service.create("auth-uuid", "12345", "name", "https://example.com", "cid", fetch_result=False)

    assert result is None
    send_tx.assert_called_once_with(
        service.w3,
        contract_func,
        service.w3.eth.account.from_key.return_value,
        gas_limit=500000,
        timeout_seconds=120,
    )


def test_update_returns_ark_info_by_default_without_exists():
    service, contract_func = _build_service()
    service.exists = Mock(side_effect=AssertionError("exists should not be called"))
    service.get = Mock(return_value=_ark_info(url="https://example.com/new", cid="cid-new"))
    receipt = TxReceiptInfo(tx_hash="0xdef", status=1, gas_used=22000, block_number=13)

    with patch("dark_core_lib.services.ark.send_contract_tx", return_value=receipt) as send_tx:
        result = service.update("auth-uuid", "12345", "name", "https://example.com/new", "cid-new")

    assert result == service.get.return_value
    service.get.assert_called_once_with("12345", "name")
    send_tx.assert_called_once_with(
        service.w3,
        contract_func,
        service.w3.eth.account.from_key.return_value,
        gas_limit=500000,
        timeout_seconds=120,
    )


def test_update_fetch_result_false_skips_get():
    service, contract_func = _build_service()
    service.exists = Mock(side_effect=AssertionError("exists should not be called"))
    service.get = Mock(side_effect=AssertionError("get should not be called"))
    receipt = TxReceiptInfo(tx_hash="0xdef", status=1, gas_used=22000, block_number=13)

    with patch("dark_core_lib.services.ark.send_contract_tx", return_value=receipt) as send_tx:
        result = service.update(
            "auth-uuid",
            "12345",
            "name",
            "https://example.com/new",
            "cid-new",
            fetch_result=False,
        )

    assert result is None
    send_tx.assert_called_once_with(
        service.w3,
        contract_func,
        service.w3.eth.account.from_key.return_value,
        gas_limit=500000,
        timeout_seconds=120,
    )


class _PipelineTxHash:
    def __init__(self, value):
        self.value = value

    def hex(self):
        return self.value


class _PipelineSigned:
    raw_transaction = b"signed"


class _PipelineAccountApi:
    def __init__(self, account, eth):
        self._account = account
        self._eth = eth

    def from_key(self, _private_key):
        return self._account

    def sign_transaction(self, tx, _key):
        self._eth.signed_payloads.append(tx)
        return _PipelineSigned()


class _PipelineEth:
    def __init__(self, receipts=None, send_failure_at=None, receipt_failure_at=None):
        self.account_obj = SimpleNamespace(address="0x" + "a" * 40, key="0x" + "1" * 64)
        self.account = _PipelineAccountApi(self.account_obj, self)
        self.gas_price = 7
        self.nonce_calls = []
        self.signed_payloads = []
        self.sent_raw = []
        self.receipts = list(receipts or [])
        self.send_failure_at = send_failure_at
        self.receipt_failure_at = receipt_failure_at

    def get_transaction_count(self, address, block_identifier=None):
        self.nonce_calls.append((address, block_identifier))
        return 3

    def send_raw_transaction(self, raw):
        index = len(self.sent_raw)
        if self.send_failure_at == index:
            raise RuntimeError("send exploded")
        self.sent_raw.append(raw)
        return _PipelineTxHash(f"0x{index}")

    def wait_for_transaction_receipt(self, tx_hash, timeout):
        index = int(tx_hash.hex()[2:])
        assert timeout == 120
        if self.receipt_failure_at == index:
            raise TimeoutError("receipt timeout")
        return self.receipts[index]


class _PipelineContractFunc:
    def __init__(self, action, args):
        self.action = action
        self.args = args

    def build_transaction(self, payload):
        return {"action": self.action, "args": self.args, **payload}


class _PipelineContractFunctions:
    def create_ark(self, naan, name, url, cid):
        return _PipelineContractFunc("create", (naan, name, url, cid))

    def update_ark(self, naan, name, url, cid):
        return _PipelineContractFunc("update", (naan, name, url, cid))


def _build_pipeline_service(**eth_kwargs):
    eth = _PipelineEth(**eth_kwargs)
    w3 = SimpleNamespace(eth=eth)
    contract = SimpleNamespace(functions=_PipelineContractFunctions())
    config = SimpleNamespace(
        read_only=False,
        chain_id=31337,
        default_gas_limit=500000,
        tx_timeout_seconds=120,
    )
    authority_service = Mock()
    authority_service.get_signing_credentials.return_value = ("0x" + "b" * 40, eth.account_obj.key)
    return ARKService(w3, contract, config, authority_service), eth


def _operation(ref, action="create"):
    return ARKPublishOperation(
        ref=ref,
        action=action,
        naan="12345",
        name=ref,
        url=f"https://example.com/{ref}",
        cid=f"cid-{ref}",
    )


def test_publish_operations_uses_pending_wallet_nonce_and_sequential_nonces():
    service, eth = _build_pipeline_service(
        receipts=[
            {"status": 1, "gasUsed": 21000, "blockNumber": 11},
            {"status": 1, "gasUsed": 22000, "blockNumber": 12},
        ]
    )
    operations = [_operation("one", "create"), _operation("two", "update")]

    results = service.publish_operations("auth-uuid", operations, pipeline_size=20)

    assert [result.status for result in results] == ["confirmed", "confirmed"]
    assert eth.nonce_calls == [(eth.account_obj.address, "pending")]
    assert [payload["nonce"] for payload in eth.signed_payloads] == [3, 4]
    assert [payload["action"] for payload in eth.signed_payloads] == ["create", "update"]
    assert all(payload["from"] == eth.account_obj.address for payload in eth.signed_payloads)
    assert all(payload["gas"] == 500000 for payload in eth.signed_payloads)
    assert all(payload["gasPrice"] == 7 for payload in eth.signed_payloads)
    assert all(payload["chainId"] == 31337 for payload in eth.signed_payloads)
    assert len(eth.sent_raw) == 2


def test_publish_operations_classifies_reverted_receipt():
    service, _eth = _build_pipeline_service(
        receipts=[{"status": 0, "gasUsed": 999, "blockNumber": 22}]
    )

    results = service.publish_operations("auth-uuid", [_operation("one")])

    assert results[0].ref == "one"
    assert results[0].status == "reverted"
    assert "reverted" in results[0].error


def test_publish_operations_stops_window_on_send_failure():
    service, eth = _build_pipeline_service(
        receipts=[{"status": 1, "gasUsed": 21000, "blockNumber": 11}],
        send_failure_at=1,
    )
    operations = [_operation("one"), _operation("two"), _operation("three")]

    results = service.publish_operations("auth-uuid", operations, pipeline_size=20)
    results_by_ref = {result.ref: result for result in results}

    assert results_by_ref["one"].status == "confirmed"
    assert results_by_ref["two"].status == "send_failed"
    assert results_by_ref["three"].status == "not_sent"
    assert len(eth.sent_raw) == 1


def test_publish_operations_marks_remaining_sent_as_ambiguous_on_receipt_failure():
    service, _eth = _build_pipeline_service(
        receipts=[
            {"status": 1, "gasUsed": 21000, "blockNumber": 11},
            {"status": 1, "gasUsed": 22000, "blockNumber": 12},
            {"status": 1, "gasUsed": 23000, "blockNumber": 13},
        ],
        receipt_failure_at=1,
    )
    operations = [_operation("one"), _operation("two"), _operation("three")]

    results = service.publish_operations("auth-uuid", operations, pipeline_size=20)

    assert [result.status for result in results] == ["confirmed", "ambiguous", "ambiguous"]
