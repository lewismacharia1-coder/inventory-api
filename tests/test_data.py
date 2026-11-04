"""Tests for the helper functions in data.py."""

import data


def test_get_next_id_with_empty_inventory(monkeypatch):
    monkeypatch.setattr(data, "inventory", [])
    assert data.get_next_id() == 1


def test_get_next_id_uses_highest_id_not_list_length(monkeypatch):
    monkeypatch.setattr(data, "inventory", [{"id": 1}, {"id": 7}])
    assert data.get_next_id() == 8


def test_find_item_returns_match_or_none(monkeypatch):
    monkeypatch.setattr(data, "inventory", [{"id": 3, "product_name": "Tea"}])
    assert data.find_item(3)["product_name"] == "Tea"
    assert data.find_item(4) is None
