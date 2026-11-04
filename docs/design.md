# Inventory Management System: Design

## Task 1: Define the Problem
- Routes needed:
- User interface for each route (CLI command):
- Flask endpoints triggered by user action:
- OpenFoodFacts connection (what data, when):
- Simulated storage (array):

## Task 2: Route Design

| Route | Input | Output | Changes the array? | CLI trigger |
|---|---|---|---|---|
| GET /inventory | | | | |
| GET /inventory/<id> | | | | |
| POST /inventory | | | | |
| PATCH /inventory/<id> | | | | |
| DELETE /inventory/<id> | | | | |
| GET /inventory/search?name= | | | | |
| GET /external/lookup?barcode= or ?name= | | | | |
| POST /inventory/import/<barcode> | | | | |
| GET /health | | | | |

## Data Model
(one example item with id, barcode, product_name, brands, ingredients_text, price, stock)

## Mock Database
(4 to 6 sample items shaped like OpenFoodFacts data)

## Error Handling Plan
- Invalid input:
- Item not found:
- External API failure: