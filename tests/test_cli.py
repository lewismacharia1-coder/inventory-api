"""Tests for the CLI.

Keyboard input and HTTP calls are both mocked, so no server is needed.
"""

from unittest.mock import Mock, patch

import requests

import cli

ITEM = {"id": 1, "barcode": "111", "product_name": "Almond Milk",
        "brands": "Silk", "ingredients_text": "water, almonds",
        "price": 3.5, "stock": 20}


def fake_response(status_code=200, body=None):
    """Build a stand-in for a requests.Response."""
    res = Mock()
    res.status_code = status_code
    res.json.return_value = body
    return res


def run(action, inputs, responses=None):
    """Run a CLI action with scripted typing and scripted API responses.

    `responses` is one fake response, or a list used one per API call.
    Returns the mocked requests.request so tests can inspect the calls.
    """
    with patch("builtins.input", side_effect=inputs), \
            patch("cli.requests.request") as mock_request:
        if isinstance(responses, list):
            mock_request.side_effect = responses
        elif responses is not None:
            mock_request.return_value = responses
        action()
    return mock_request


# ---------- call_api ----------

def test_call_api_connection_error_returns_none(capsys):
    with patch("cli.requests.request",
               side_effect=requests.exceptions.ConnectionError()):
        assert cli.call_api("GET", "/inventory") == (None, None)
    assert "cannot reach the API" in capsys.readouterr().out


def test_call_api_timeout_returns_none(capsys):
    with patch("cli.requests.request",
               side_effect=requests.exceptions.Timeout()):
        assert cli.call_api("GET", "/inventory") == (None, None)
    assert "too long" in capsys.readouterr().out


def test_call_api_non_json_body_returns_none_body():
    res = Mock(status_code=500)
    res.json.side_effect = ValueError("not json")
    with patch("cli.requests.request", return_value=res):
        assert cli.call_api("GET", "/inventory") == (500, None)


# ---------- view ----------

def test_view_all_prints_items(capsys):
    run(cli.view_all, [], fake_response(200, [ITEM]))
    assert "Almond Milk" in capsys.readouterr().out


def test_view_all_empty_inventory(capsys):
    run(cli.view_all, [], fake_response(200, []))
    assert "Inventory is empty" in capsys.readouterr().out


def test_view_all_server_down_does_not_crash(capsys):
    with patch("cli.requests.request",
               side_effect=requests.exceptions.ConnectionError()):
        cli.view_all()
    assert "cannot reach the API" in capsys.readouterr().out


def test_view_one_shows_details(capsys):
    run(cli.view_one, ["1"], fake_response(200, ITEM))
    out = capsys.readouterr().out
    assert "Almond Milk" in out
    assert "water, almonds" in out


def test_view_one_not_found_shows_api_error(capsys):
    run(cli.view_one, ["99"], fake_response(404, {"error": "Item not found"}))
    assert "Item not found" in capsys.readouterr().out


def test_view_one_reprompts_on_invalid_id(capsys):
    mock_request = run(cli.view_one, ["abc", "1"], fake_response(200, ITEM))
    assert "valid whole number" in capsys.readouterr().out
    assert mock_request.call_count == 1


# ---------- add ----------

def test_add_item_sends_expected_payload():
    inputs = ["Tea", "Lipton", "", "", "1.5", "10"]
    mock_request = run(cli.add_item, inputs, fake_response(201, ITEM))
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert args[1].endswith("/inventory")
    assert kwargs["json"] == {
        "product_name": "Tea", "brands": "Lipton", "price": 1.5, "stock": 10,
    }


def test_add_item_reprompts_on_invalid_numbers(capsys):
    inputs = ["Tea", "", "", "", "abc", "-5", "2.5", "x", "3"]
    mock_request = run(cli.add_item, inputs, fake_response(201, ITEM))
    out = capsys.readouterr().out
    assert "valid number" in out
    assert "valid whole number" in out
    assert mock_request.call_args.kwargs["json"]["price"] == 2.5
    assert mock_request.call_args.kwargs["json"]["stock"] == 3


def test_add_item_shows_api_validation_error(capsys):
    inputs = ["Tea", "", "", "", "1", "1"]
    run(cli.add_item, inputs, fake_response(400, {"error": "bad data"}))
    assert "bad data" in capsys.readouterr().out


# ---------- update ----------

def test_update_item_nothing_to_update(capsys):
    mock_request = run(cli.update_item, ["1", "", ""])
    mock_request.assert_not_called()
    assert "Nothing to update" in capsys.readouterr().out


def test_update_item_sends_only_changed_fields():
    mock_request = run(cli.update_item, ["1", "", "7"], fake_response(200, ITEM))
    args, kwargs = mock_request.call_args
    assert args[0] == "PATCH"
    assert args[1].endswith("/inventory/1")
    assert kwargs["json"] == {"stock": 7}


# ---------- delete ----------

def test_delete_item_confirmed(capsys):
    mock_request = run(cli.delete_item, ["2", "y"],
                       fake_response(200, {"message": "Item 2 deleted"}))
    assert mock_request.call_args.args[0] == "DELETE"
    assert "Item 2 deleted" in capsys.readouterr().out


def test_delete_item_cancelled(capsys):
    mock_request = run(cli.delete_item, ["2", "n"])
    mock_request.assert_not_called()
    assert "Cancelled" in capsys.readouterr().out


# ---------- search ----------

def test_search_items_no_matches(capsys):
    run(cli.search_items, ["zzz"], fake_response(200, []))
    assert "No matching items" in capsys.readouterr().out


# ---------- external API ----------

def test_find_on_api_then_import():
    product = {"barcode": "999", "product_name": "Test Milk", "brands": "X"}
    inputs = ["1", "999", "1", "4.5", "10"]
    mock_request = run(cli.find_on_api, inputs,
                       [fake_response(200, [product]), fake_response(201, ITEM)])
    args, kwargs = mock_request.call_args  # the second call is the import
    assert args[0] == "POST"
    assert args[1].endswith("/inventory/import/999")
    assert kwargs["json"] == {"price": 4.5, "stock": 10}


def test_find_on_api_skip_does_not_import():
    product = {"barcode": "999", "product_name": "Test Milk", "brands": "X"}
    mock_request = run(cli.find_on_api, ["2", "milk", "0"],
                       fake_response(200, [product]))
    assert mock_request.call_count == 1


def test_find_on_api_reprompts_when_choice_out_of_range(capsys):
    product = {"barcode": "999", "product_name": "Test Milk", "brands": "X"}
    run(cli.find_on_api, ["2", "milk", "5", "0"], fake_response(200, [product]))
    assert "from 0 to 1" in capsys.readouterr().out


def test_find_on_api_product_without_barcode_cannot_import(capsys):
    product = {"barcode": "", "product_name": "Mystery", "brands": ""}
    mock_request = run(cli.find_on_api, ["2", "mystery", "1"],
                       fake_response(200, [product]))
    assert mock_request.call_count == 1
    assert "no barcode" in capsys.readouterr().out


def test_find_on_api_shows_api_failure(capsys):
    run(cli.find_on_api, ["1", "999"],
        fake_response(502, {"error": "Could not reach OpenFoodFacts"}))
    out = capsys.readouterr().out
    assert "502" in out
    assert "Could not reach OpenFoodFacts" in out


# ---------- main menu ----------

def test_main_invalid_option_then_quit(capsys):
    run(cli.main, ["9", "0"])
    out = capsys.readouterr().out
    assert "Invalid option" in out
    assert "Goodbye" in out


def test_main_runs_chosen_action(capsys):
    run(cli.main, ["1", "0"], fake_response(200, []))
    assert "Inventory is empty" in capsys.readouterr().out


def test_main_handles_ctrl_c(capsys):
    run(cli.main, KeyboardInterrupt())
    assert "Goodbye" in capsys.readouterr().out
