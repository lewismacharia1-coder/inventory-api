"""Extra tests for error handling and edge cases in the API."""

import pytest

import data
from app import create_app


@pytest.fixture
def client():
    """Fresh app and a known starting inventory for every test."""
    data.inventory.clear()
    data.inventory.extend([
        {"id": 1, "barcode": "111", "product_name": "Almond Milk",
         "brands": "Silk", "ingredients_text": "water, almonds",
         "price": 3.5, "stock": 20},
        {"id": 2, "barcode": "222", "product_name": "Brown Rice",
         "brands": "Pishori", "ingredients_text": "rice",
         "price": 2.0, "stock": 50},
    ])
    return create_app().test_client()


def test_unknown_route_returns_json_404(client):
    res = client.get("/does-not-exist")
    assert res.status_code == 404
    assert res.get_json() == {"error": "Route not found"}


def test_wrong_http_method_returns_json_405(client):
    res = client.put("/inventory")
    assert res.status_code == 405
    assert "error" in res.get_json()


def test_patch_unknown_field_returns_400(client):
    assert client.patch("/inventory/1", json={"colour": "red"}).status_code == 400


def test_patch_negative_stock_returns_400(client):
    assert client.patch("/inventory/1", json={"stock": -1}).status_code == 400


def test_patch_negative_price_returns_400(client):
    assert client.patch("/inventory/1", json={"price": -0.5}).status_code == 400


def test_post_boolean_stock_returns_400(client):
    res = client.post("/inventory", json={"product_name": "Tea", "stock": True})
    assert res.status_code == 400


def test_post_trims_product_name(client):
    res = client.post("/inventory", json={"product_name": "  Tea  "})
    assert res.get_json()["product_name"] == "Tea"


def test_post_fills_default_price_and_stock(client):
    body = client.post("/inventory", json={"product_name": "Tea"}).get_json()
    assert body["price"] == 0.0
    assert body["stock"] == 0


def test_search_is_case_insensitive(client):
    res = client.get("/inventory/search?name=ALMOND")
    assert len(res.get_json()) == 1


def test_search_with_no_match_returns_empty_list(client):
    res = client.get("/inventory/search?name=zzz")
    assert res.status_code == 200
    assert res.get_json() == []


def test_import_bad_stock_returns_400(client):
    res = client.post("/inventory/import/999", json={"stock": -2})
    assert res.status_code == 400
