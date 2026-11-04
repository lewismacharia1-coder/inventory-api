"""Command-line interface for the inventory API.

Start the Flask server first (python app.py), then run this file in a
second terminal:  python cli.py
"""

import math

import requests

API_URL = "http://127.0.0.1:5000"
TIMEOUT = 15  # seconds; the external lookup can be slow


# ---------- helpers: talking to the API ----------

def call_api(method, path, **kwargs):
    """Send a request to the Flask API.

    Returns (status_code, json_body). If the server can't be reached it
    prints a friendly message and returns (None, None) instead of crashing.
    """
    try:
        response = requests.request(
            method, f"{API_URL}{path}", timeout=TIMEOUT, **kwargs
        )
    except requests.exceptions.ConnectionError:
        print("Error: cannot reach the API. Is the server running? (python app.py)")
        return None, None
    except requests.exceptions.Timeout:
        print("Error: the API took too long to respond.")
        return None, None
    except requests.exceptions.RequestException as exc:
        print(f"Error: the request failed ({exc}).")
        return None, None

    try:
        body = response.json()
    except ValueError:
        body = None
    return response.status_code, body


def show_error(status, body):
    """Print the API's error message for a failed request."""
    message = body.get("error") if isinstance(body, dict) else None
    print(f"Error {status}: {message or 'unexpected response from the API'}")


def check(status, body, expected):
    """Return True if the call worked; otherwise print why it didn't."""
    if status is None:  # call_api already explained the problem
        return False
    if status != expected:
        show_error(status, body)
        return False
    return True


# ---------- helpers: reading user input ----------

def ask_text(prompt, required=True):
    """Ask for text. If required, keep asking until something is typed."""
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("This field is required.")


def ask_number(prompt, cast, allow_blank=False):
    """Ask for a number that is 0 or more (cast is int or float).

    Keeps asking until the input is valid. Returns None for blank input
    when allow_blank is True.
    """
    label = "whole number" if cast is int else "number"
    while True:
        raw = input(prompt).strip()
        if not raw and allow_blank:
            return None
        try:
            value = cast(raw)
        except ValueError:
            print(f"Please enter a valid {label}.")
            continue
        if not math.isfinite(value) or value < 0:
            print(f"Please enter a valid {label} that is 0 or more.")
            continue
        return value


def ask_choice(prompt, valid):
    """Ask until the answer is one of the allowed options."""
    while True:
        value = input(prompt).strip().lower()
        if value in valid:
            return value
        print(f"Please type one of: {', '.join(sorted(valid))}.")


def print_item(item):
    """Show one inventory item on two lines."""
    brand = item.get("brands") or "no brand"
    print(f"[{item.get('id')}] {item.get('product_name')} ({brand})")
    print(
        f"     price: {item.get('price', 0):.2f} | stock: {item.get('stock', 0)}"
        f" | barcode: {item.get('barcode') or '-'}"
    )


# ---------- menu actions ----------

def view_all():
    """Option 1: list every item."""
    status, body = call_api("GET", "/inventory")
    if not check(status, body, 200):
        return
    if not body:
        print("Inventory is empty.")
        return
    for item in body:
        print_item(item)


def view_one():
    """Option 2: show the details of one item."""
    item_id = ask_number("Item id: ", int)
    status, body = call_api("GET", f"/inventory/{item_id}")
    if check(status, body, 200):
        print_item(body)
        print(f"     ingredients: {body.get('ingredients_text') or '-'}")


def add_item():
    """Option 3: create a new item."""
    print("--- Add new item ---")
    payload = {"product_name": ask_text("Product name: ")}
    for field, prompt in (
        ("brands", "Brand (optional): "),
        ("ingredients_text", "Ingredients (optional): "),
        ("barcode", "Barcode (optional): "),
    ):
        value = ask_text(prompt, required=False)
        if value:
            payload[field] = value
    payload["price"] = ask_number("Price: ", float)
    payload["stock"] = ask_number("Stock: ", int)

    status, body = call_api("POST", "/inventory", json=payload)
    if check(status, body, 201):
        print("Item added:")
        print_item(body)


def update_item():
    """Option 4: change the price and/or stock of an item."""
    item_id = ask_number("Item id to update: ", int)
    price = ask_number("New price (blank to keep): ", float, allow_blank=True)
    stock = ask_number("New stock (blank to keep): ", int, allow_blank=True)

    changes = {}
    if price is not None:
        changes["price"] = price
    if stock is not None:
        changes["stock"] = stock
    if not changes:
        print("Nothing to update.")
        return

    status, body = call_api("PATCH", f"/inventory/{item_id}", json=changes)
    if check(status, body, 200):
        print("Item updated:")
        print_item(body)


def delete_item():
    """Option 5: delete an item after confirmation."""
    item_id = ask_number("Item id to delete: ", int)
    if ask_choice(f"Delete item {item_id}? (y/n): ", {"y", "n"}) != "y":
        print("Cancelled.")
        return
    status, body = call_api("DELETE", f"/inventory/{item_id}")
    if check(status, body, 200):
        print(body.get("message", "Item deleted."))


def search_items():
    """Option 6: search the local inventory by name."""
    name = ask_text("Name to search for: ")
    status, body = call_api("GET", "/inventory/search", params={"name": name})
    if not check(status, body, 200):
        return
    if not body:
        print("No matching items.")
        return
    for item in body:
        print_item(item)


def find_on_api():
    """Option 7: look a product up on OpenFoodFacts, then optionally import it."""
    mode = ask_choice("Search by (1) barcode or (2) name: ", {"1", "2"})
    if mode == "1":
        params = {"barcode": ask_text("Barcode: ")}
    else:
        params = {"name": ask_text("Product name: ")}

    status, body = call_api("GET", "/external/lookup", params=params)
    if not check(status, body, 200):
        return

    for number, product in enumerate(body, start=1):
        brand = product.get("brands") or "no brand"
        print(
            f"{number}. {product.get('product_name')} ({brand})"
            f" | barcode: {product.get('barcode') or '-'}"
        )

    while True:
        pick = ask_number("Number to add to inventory (0 to skip): ", int)
        if pick <= len(body):
            break
        print(f"Please choose a number from 0 to {len(body)}.")
    if pick == 0:
        return

    barcode = body[pick - 1].get("barcode")
    if not barcode:
        print("That product has no barcode, so it can't be imported.")
        return

    price = ask_number("Price: ", float)
    stock = ask_number("Stock: ", int)
    status, body = call_api(
        "POST", f"/inventory/import/{barcode}", json={"price": price, "stock": stock}
    )
    if check(status, body, 201):
        print("Added to inventory:")
        print_item(body)


# ---------- main menu ----------

MENU = """
==== Inventory Manager ====
1. View all items
2. View item details
3. Add new item
4. Update price or stock
5. Delete product
6. Search inventory
7. Find item on OpenFoodFacts
0. Quit
"""

ACTIONS = {
    "1": view_all,
    "2": view_one,
    "3": add_item,
    "4": update_item,
    "5": delete_item,
    "6": search_items,
    "7": find_on_api,
}


def main():
    """Show the menu until the user quits."""
    try:
        while True:
            print(MENU)
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye!")
                break
            action = ACTIONS.get(choice)
            if action is None:
                print("Invalid option. Please choose a number from the menu.")
                continue
            action()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
