"""Mock database for the inventory system.

The list below simulates a database. Data lives only in memory, so it
resets whenever the server restarts.
"""

inventory = [
    {
        "id": 1,
        "barcode": "3017620422003",
        "product_name": "Hazelnut Spread",
        "brands": "Ferrero",
        "ingredients_text": "Sugar, palm oil, hazelnuts, cocoa, skimmed milk powder",
        "price": 5.99,
        "stock": 25,
    },
    {
        "id": 2,
        "barcode": "5449000000996",
        "product_name": "Cola Soft Drink",
        "brands": "Coca-Cola",
        "ingredients_text": "Carbonated water, sugar, colour, acid, flavourings",
        "price": 1.50,
        "stock": 60,
    },
    {
        "id": 3,
        "barcode": "0000000000003",
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "ingredients_text": "Filtered water, almonds, cane sugar",
        "price": 3.50,
        "stock": 20,
    },
]


def get_next_id():
    """Return the next unused id (max existing id + 1, or 1 if empty)."""
    if not inventory:
        return 1
    return max(item["id"] for item in inventory) + 1


def find_item(item_id):
    """Return the item with the given id, or None if it doesn't exist."""
    for item in inventory:
        if item["id"] == item_id:
            return item
    return None
