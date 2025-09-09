from datetime import datetime, timedelta, timezone

import pytest

from api42lib import IntraAPIClient

ic = IntraAPIClient(progress_bar=False)


@pytest.fixture
def client():
    return ic


@pytest.fixture
def token():
    return ic.token_v2


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


def test_url_1(client):
    response = client.get("https://api.intra.42.fr/v2/users/42berlin_tech")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_url_2(client):
    response = client.get("/v2/users/42berlin_tech")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_url_3(client):
    response = client.get("v2/users/42berlin_tech")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_url_4(client):
    response = client.get("users/42berlin_tech")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_url_5(client):
    response = client.get("/users/42berlin_tech")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_url_6(client):
    response = client.get("    users/42berlin_tech    ")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_request_with_invalid_token(client):
    client.token_v2.access_token = "21314"
    response = client.get("https://api.intra.42.fr/v2/users/42berlin_tech")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_request_with_expired_token(client):
    client.token_v2.expires_at = datetime.now(timezone.utc) - timedelta(seconds=5000)
    response = client.get("https://api.intra.42.fr/v2/users/42berlin_tech")
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == 147888


def test_pages(client):
    params = {"filter[pool_month]": "october"}
    response = client.pages("campus/berlin/users", params=params, stop_page=4)
    assert isinstance(response, list) and len(response) > 0


def test_pages_threaded(client):
    params = {"filter[pool_month]": "october"}
    response = client.pages("campus/berlin/users", params=params, stop_page=4)
    assert isinstance(response, list) and len(response) > 0


def test_raise_wrong_credentials(client):
    with pytest.raises(Exception):
        client.token_v2.client_id = "wrong"
        client.token_v2.request_token()
