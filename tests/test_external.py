"""Tests for the OpenFoodFacts client and the external routes.

Every HTTP call is mocked, so these tests never touch the network.
"""

from unittest.mock import Mock, patch

import pytest
import requests

import data
import openfoodfacts_client as off
from app import create_app

SAMPLE = {
    "barcode": "999",
    "product_name": "Test Milk",
    "brands": "X",
    "ingredients_text": "water, milk",
}


def fake_response(status_code=200, body=None):
    """Build a stand-in for a requests.Response."""
    res = Mock()
    res.status_code = status_code
    res.json.return_value = body if body is not None else {}
    if status_code >= 400:
        res.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"HTTP {status_code}"
        )
    return res


# ---------- client functions ----------

@patch("openfoodfacts_client.requests.get")
def test_fetch_by_barcode_success(mock_get):
    mock_get.return_value = fake_response(200, {
        "status": 1,
        "product": {"code": "123", "product_name": "Test Milk",
                    "brands": "X", "ingredients_text": "a, b"},
    })
    result = off.fetch_by_barcode("123")
    assert result["product_name"] == "Test Milk"
    assert result["barcode"] == "123"


@patch("openfoodfacts_client.requests.get")
def test_fetch_by_barcode_status_zero_returns_none(mock_get):
    mock_get.return_value = fake_response(200, {"status": 0})
    assert off.fetch_by_barcode("000") is None


@patch("openfoodfacts_client.requests.get")
def test_fetch_by_barcode_http_404_returns_none(mock_get):
    mock_get.return_value = fake_response(404, {"status": 0})
    assert off.fetch_by_barcode("000") is None


@patch("openfoodfacts_client.requests.get")
def test_fetch_by_barcode_network_failure_raises(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("down")
    with pytest.raises(off.ExternalAPIError):
        off.fetch_by_barcode("123")


@patch("openfoodfacts_client.requests.get")
def test_fetch_by_barcode_server_error_raises(mock_get):
    mock_get.return_value = fake_response(500)
    with pytest.raises(off.ExternalAPIError):
        off.fetch_by_barcode("123")


@patch("openfoodfacts_client.requests.get")
def test_search_by_name_returns_cleaned_list(mock_get):
    mock_get.return_value = fake_response(200, {"products": [
        {"code": "1", "product_name": "Milk A"},
        {"code": "2", "product_name": "Milk B"},
    ]})
    results = off.search_by_name("milk")
    assert [p["product_name"] for p in results] == ["Milk A", "Milk B"]


# ---------- Flask routes ----------

@pytest.fixture
def client():
    data.inventory.clear()
    data.inventory.append({
        "id": 1, "barcode": "111", "product_name": "Almond Milk",
        "brands": "Silk", "ingredients_text": "water, almonds",
        "price": 3.5, "stock": 20,
    })
    return create_app().test_client()


@patch("openfoodfacts_client.fetch_by_barcode")
def test_lookup_by_barcode(mock_fetch, client):
    mock_fetch.return_value = SAMPLE
    res = client.get("/external/lookup?barcode=999")
    assert res.status_code == 200
    assert res.get_json()[0]["product_name"] == "Test Milk"
    assert len(data.inventory) == 1  # lookup must not change the array


@patch("openfoodfacts_client.search_by_name")
def test_lookup_by_name(mock_search, client):
    mock_search.return_value = [SAMPLE]
    res = client.get("/external/lookup?name=milk")
    assert res.status_code == 200
    assert len(res.get_json()) == 1


@patch("openfoodfacts_client.fetch_by_barcode")
def test_lookup_not_found_returns_404(mock_fetch, client):
    mock_fetch.return_value = None
    assert client.get("/external/lookup?barcode=000").status_code == 404


def test_lookup_without_params_returns_400(client):
    assert client.get("/external/lookup").status_code == 400


@patch("openfoodfacts_client.fetch_by_barcode")
def test_lookup_api_down_returns_502(mock_fetch, client):
    mock_fetch.side_effect = off.ExternalAPIError("down")
    assert client.get("/external/lookup?barcode=999").status_code == 502


@patch("openfoodfacts_client.fetch_by_barcode")
def test_import_adds_item_to_inventory(mock_fetch, client):
    mock_fetch.return_value = SAMPLE
    res = client.post("/inventory/import/999", json={"price": 4.0, "stock": 10})
    assert res.status_code == 201
    body = res.get_json()
    assert body["id"] == 2
    assert body["price"] == 4.0
    assert len(data.inventory) == 2


@patch("openfoodfacts_client.fetch_by_barcode")
def test_import_duplicate_barcode_returns_409(mock_fetch, client):
    mock_fetch.return_value = {**SAMPLE, "barcode": "111"}
    res = client.post("/inventory/import/111", json={})
    assert res.status_code == 409
    assert len(data.inventory) == 1


@patch("openfoodfacts_client.fetch_by_barcode")
def test_import_not_found_returns_404(mock_fetch, client):
    mock_fetch.return_value = None
    assert client.post("/inventory/import/000", json={}).status_code == 404


@patch("openfoodfacts_client.fetch_by_barcode")
def test_import_api_down_returns_502(mock_fetch, client):
    mock_fetch.side_effect = off.ExternalAPIError("down")
    assert client.post("/inventory/import/999", json={}).status_code == 502


def test_import_bad_price_returns_400(client):
    res = client.post("/inventory/import/999", json={"price": "cheap"})
    assert res.status_code == 400
