from datetime import datetime, timedelta, timezone

import pytest

from api42lib import IntraAPIClient

ic = IntraAPIClient(progress_bar=False)


@pytest.fixture
def client():
    return ic


@pytest.fixture
def token():
    return ic.token_v3


def test_token_is_valid(token):
    token.access_token = "dummy"
    token.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert not token.is_valid()
    token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=1)
    assert token.is_valid()


def test_token_request(token):
    token.access_token = None
    token.request_token()
    assert token.access_token is not None
    assert token.is_valid()


def test_freeze_url_1(client):
    response = client.get("https://freeze.42.fr/api/v2/freezes").json()
    assert "items" in response


def test_freeze_url_2(client):
    response = client.get("/v3/freeze/v2/freezes").json()
    assert "items" in response


def test_freeze_url_3(client):
    response = client.get("v3/freeze/v2/freezes").json()
    assert "items" in response


def test_freeze_url_4(client):
    response = client.get("freeze/v2/freezes").json()
    assert "items" in response


def test_freeze_url_5(client):
    response = client.get("/freeze/v2/freezes").json()
    assert "items" in response


def test_freeze_url_6(client):
    response = client.get("   freeze/v2/freezes   ").json()
    assert "items" in response


def test_pace_url_1(client):
    response = client.get("https://pace-system.42.fr/api/v1/paces").json()
    assert "items" in response


def test_pace_url_2(client):
    response = client.get("/v3/pace-system/v1/paces").json()
    assert "items" in response


def test_pace_url_3(client):
    response = client.get("v3/pace-system/v1/paces").json()
    assert "items" in response


def test_pace_url_4(client):
    response = client.get("pace-system/v1/paces").json()
    assert "items" in response


def test_pace_url_5(client):
    response = client.get("/pace-system/v1/paces").json()
    assert "items" in response


def test_pace_url_6(client):
    response = client.get("   pace-system/v1/paces   ").json()
    assert "items" in response


def test_request_with_invalid_token(client):
    client.token_v3.access_token = "21314"
    response = client.get("/v3/freeze/v2/freezes")
    assert response.status_code == 200


def test_request_with_expired_token(client):
    client.token_v3.expires_at = datetime.now(timezone.utc) - timedelta(seconds=5000)
    response = client.get("/v3/freeze/v2/freezes")
    assert response.status_code == 200


def test_pages(client):
    response = client.pages("/v3/freeze/v2/freezes", stop_page=4)
    assert isinstance(response, list) and len(response) > 0


def test_freeze_pages_threaded(client):
    response = client.pages_threaded("/v3/freeze/v2/freezes", stop_page=4)
    assert isinstance(response, list) and len(response) > 0


def test_pace_pages_threaded_invalid_v2param(client):
    response = client.pages_threaded("/v3/pace-system/v1/paces", stop_page=4)
    assert isinstance(response, list) and len(response) > 0


def test_raise_wrong_credentials(client):
    with pytest.raises(Exception):
        client.token_v3.client_id = "wrong"
        client.token_v3.request_token()
