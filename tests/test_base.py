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
