"""Tests for the Flask inventory endpoints."""

import pytest

import data
from app import create_app


@pytest.fixture
def client():
    """Give every test a fresh app and a known starting inventory."""
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


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_get_all_items(client):
    res = client.get("/inventory")
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_get_one_item(client):
    res = client.get("/inventory/1")
    assert res.status_code == 200
    assert res.get_json()["product_name"] == "Almond Milk"


def test_get_missing_item_returns_404(client):
    assert client.get("/inventory/999").status_code == 404


def test_add_item_success(client):
    res = client.post("/inventory", json={"product_name": "Tea", "price": 1.2, "stock": 10})
    assert res.status_code == 201
    assert res.get_json()["id"] == 3
    assert len(data.inventory) == 3


def test_add_item_missing_name_returns_400(client):
    res = client.post("/inventory", json={"price": 1.0})
    assert res.status_code == 400


def test_add_item_non_string_name_returns_400(client):
    res = client.post("/inventory", json={"product_name": 123})
    assert res.status_code == 400


def test_add_item_bad_price_returns_400(client):
    res = client.post("/inventory", json={"product_name": "Tea", "price": "cheap"})
    assert res.status_code == 400


def test_add_item_without_json_returns_400(client):
    res = client.post("/inventory", data="not json")
    assert res.status_code == 400


def test_patch_updates_only_sent_fields(client):
    res = client.patch("/inventory/1", json={"stock": 5})
    assert res.status_code == 200
    body = res.get_json()
    assert body["stock"] == 5
    assert body["product_name"] == "Almond Milk"


def test_patch_missing_item_returns_404(client):
    assert client.patch("/inventory/999", json={"stock": 5}).status_code == 404


def test_patch_empty_body_returns_400(client):
    assert client.patch("/inventory/1", json={}).status_code == 400


def test_delete_item(client):
    res = client.delete("/inventory/1")
    assert res.status_code == 200
    assert data.find_item(1) is None


def test_delete_missing_item_returns_404(client):
    assert client.delete("/inventory/999").status_code == 404


def test_search_finds_match(client):
    res = client.get("/inventory/search?name=milk")
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_search_without_name_returns_400(client):
    assert client.get("/inventory/search").status_code == 400
