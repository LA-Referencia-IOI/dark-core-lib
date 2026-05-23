import time
from types import SimpleNamespace

from dark_core_lib.services.chain import ChainService


class _Provider:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def make_request(self, method, params):
        self.calls.append((method, params))
        response = self.responses.get(method)
        if isinstance(response, Exception):
            raise response
        return response


class _Eth:
    def __init__(self, block_number=100):
        self.block_number = block_number


class _W3:
    def __init__(self, *, connected=True, block_number=100, responses=None):
        self.eth = _Eth(block_number=block_number)
        self.provider = _Provider(responses=responses)
        self._connected = connected

    def is_connected(self):
        return self._connected


def test_chain_capacity_healthy_with_low_txpool():
    w3 = _W3(responses={"txpool_besuStatistics": {"result": {"localCount": 2, "remoteCount": 3}}})
    service = ChainService(w3)

    capacity = service.get_capacity(max_page_size=20)

    assert capacity.available is True
    assert capacity.state == "healthy"
    assert capacity.recommended_page_size == 20
    assert capacity.txpool_pending == 5


def test_chain_capacity_congested_with_high_txpool():
    w3 = _W3(responses={"txpool_besuStatistics": {"result": {"pendingCount": 45}}})
    service = ChainService(w3)

    capacity = service.get_capacity(max_page_size=20)

    assert capacity.available is True
    assert capacity.state == "congested"
    assert capacity.recommended_page_size == 10
    assert capacity.txpool_pending == 45


def test_chain_capacity_pauses_with_critical_txpool():
    w3 = _W3(responses={"txpool_besuStatistics": {"result": {"pendingCount": 120}}})
    service = ChainService(w3)

    capacity = service.get_capacity(max_page_size=20)

    assert capacity.available is True
    assert capacity.state == "congested"
    assert capacity.recommended_page_size == 0


def test_chain_capacity_reports_stalled_when_block_does_not_progress():
    w3 = _W3(responses={"txpool_besuStatistics": {"result": {"pendingCount": 0}}})
    service = ChainService(w3)
    service._last_capacity_block_number = 100
    service._last_capacity_block_progress_monotonic = time.monotonic() - 121

    capacity = service.get_capacity(max_page_size=20)

    assert capacity.available is True
    assert capacity.state == "stalled"
    assert capacity.recommended_page_size == 0


def test_chain_capacity_tolerates_missing_txpool_stats():
    w3 = _W3(responses={"txpool_besuStatistics": {"error": {"message": "method missing"}}})
    service = ChainService(w3)

    capacity = service.get_capacity(max_page_size=20)

    assert capacity.available is True
    assert capacity.state == "healthy"
    assert capacity.recommended_page_size == 20
    assert capacity.txpool_pending is None


def test_chain_capacity_unavailable_when_rpc_disconnected():
    service = ChainService(SimpleNamespace(is_connected=lambda: False))

    capacity = service.get_capacity(max_page_size=20)

    assert capacity.available is False
    assert capacity.state == "unavailable"
    assert capacity.recommended_page_size == 0
