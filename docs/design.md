# Inventory Management System: Design

## Task 1: Define the Problem
- Routes needed: five CRUD routes (list, get one, add, update, delete) plus search, external lookup, import and health
- User interface for each route (CLI command): a numbered CLI menu where each option calls one route
- Flask endpoints triggered by user action: the CLI sends HTTP requests to the Flask server
- OpenFoodFacts connection (what data, when): product name, brands and ingredients, fetched by barcode or name when the user picks "Find item on API"
- Simulated storage (array): a Python list of dicts in data.py; it resets when the server restarts

## Task 2: Route Design

| Route | Input | Output | Changes the array? | CLI trigger |
|---|---|---|---|---|
| GET /inventory | none | list of all items, 200 | No | View all items |
| GET /inventory/<id> | id in URL | item, 200; error JSON, 404 | No | View item details |
| POST /inventory | JSON: product_name (required), brands, ingredients_text, barcode, price, stock | new item with generated id, 201; 400 if invalid | Yes, appends | Add new item |
| PATCH /inventory/<id> | id in URL + JSON with fields to change | updated item, 200; 400 or 404 | Yes, modifies | Update price or stock |
| DELETE /inventory/<id> | id in URL | confirmation message, 200; 404 | Yes, removes | Delete product |
| GET /inventory/search?name= | query param name | matching items, 200 | No | Search inventory |
| GET /external/lookup?barcode= or ?name= | query param | cleaned OpenFoodFacts data, 200; 404; 502 if API down | No | Find item on API |
| POST /inventory/import/<barcode> | barcode in URL, optional JSON price and stock | new item, 201; 404; 502 | Yes, appends | "Add to inventory?" after a lookup |
| GET /health | none | {"status": "ok"}, 200 | No | Not in the menu (server check) |

## Data Model
```json
{
  "id": 1,
  "barcode": "3017620422003",
  "product_name": "Hazelnut Spread",
  "brands": "Ferrero",
  "ingredients_text": "Sugar, palm oil, hazelnuts, cocoa, skimmed milk powder",
  "price": 5.99,
  "stock": 25
}
```

## Mock Database
Three starting items live in data.py, shaped like OpenFoodFacts data: Hazelnut Spread, Cola Soft Drink and Organic Almond Milk. Every item has a unique id.

## Error Handling Plan
- Invalid input: return 400 with a clear message (missing product_name, price or stock not a number)
- Item not found: return 404 with {"error": "Item not found"}
- External API failure: catch request errors and timeouts, return 502; the CLI shows the message without crashing
