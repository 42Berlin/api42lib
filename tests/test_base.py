import time

import pytest

from api42lib import IntraAPIClient


@pytest.fixture
def ic():
    client = IntraAPIClient(progress_bar=False)
    return client


def test_singleton_pattern(ic):
    new_ic = IntraAPIClient()
    assert ic is new_ic, "IC should follow the singleton pattern"


def test_initialization(ic):
    assert hasattr(ic, "token_v2"), "IC should have token_v2 after initialization"
    assert hasattr(ic, "token_v3"), "IC should have token_v3 after initialization"


def test_retry_on_5xx(monkeypatch, ic):
    max_retries = 42
    call_count = 0

    ic.retry_on_5xx = True
    ic.server_max_retries = max_retries

    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            self.headers = {}

        def json(self):
            return {}

    def mock_request(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < max_retries:
            return MockResponse(500)
        return MockResponse(200)

    monkeypatch.setattr("requests.get", mock_request)
    monkeypatch.setattr(time, "sleep", lambda *_: None)

    response = ic.get("/v2/users/42berlin_tech")
    assert response.status_code == 200, "Request should eventually succeed"
    assert (
        call_count == max_retries
    ), f"Should have retried {max_retries} times before succeeding"
