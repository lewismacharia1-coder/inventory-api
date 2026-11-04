"""Flask REST API for the inventory management system."""

from flask import Flask, jsonify, request

import data

ALLOWED_FIELDS = {
    "barcode", "product_name", "brands", "ingredients_text", "price", "stock"
}


def validate_payload(payload, partial=False):
    """Validate item data from a request body.

    partial=False is used for POST (product_name is required).
    partial=True is used for PATCH (any subset of fields is allowed).
    Returns an error message string, or None if the data is valid.
    """
    if not isinstance(payload, dict):
        return "Request body must be a JSON object"

    unknown = set(payload) - ALLOWED_FIELDS
    if unknown:
        return f"Unknown fields: {', '.join(sorted(unknown))}"

    if not partial and "product_name" not in payload:
        return "product_name is required"

    if "product_name" in payload:
        name = payload["product_name"]
        if not isinstance(name, str) or not name.strip():
            return "product_name must be a non-empty string"

    if "price" in payload:
        price = payload["price"]
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            return "price must be a non-negative number"

    if "stock" in payload:
        stock = payload["stock"]
        if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
            return "stock must be a non-negative integer"

    return None


def create_app():
    """Application factory: builds a fresh Flask app (easy to test)."""
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        """Simple check that the server is running."""
        return jsonify({"status": "ok"}), 200

    @app.route("/inventory", methods=["GET"])
    def get_inventory():
        """Return all inventory items."""
        return jsonify(data.inventory), 200

    @app.route("/inventory/search", methods=["GET"])
    def search_inventory():
        """Return items whose product_name contains ?name= (case-insensitive)."""
        name = request.args.get("name", "").strip().lower()
        if not name:
            return jsonify({"error": "Query parameter 'name' is required"}), 400
        matches = [
            item for item in data.inventory
            if name in item["product_name"].lower()
        ]
        return jsonify(matches), 200

    @app.route("/inventory/<int:item_id>", methods=["GET"])
    def get_item(item_id):
        """Return a single item by id."""
        item = data.find_item(item_id)
        if item is None:
            return jsonify({"error": "Item not found"}), 404
        return jsonify(item), 200

    @app.route("/inventory", methods=["POST"])
    def add_item():
        """Create a new item from a JSON body."""
        payload = request.get_json(silent=True)
        error = validate_payload(payload)
        if error:
            return jsonify({"error": error}), 400

        item = {
            "id": data.get_next_id(),
            "barcode": payload.get("barcode", ""),
            "product_name": payload["product_name"].strip(),
            "brands": payload.get("brands", ""),
            "ingredients_text": payload.get("ingredients_text", ""),
            "price": payload.get("price", 0.0),
            "stock": payload.get("stock", 0),
        }
        data.inventory.append(item)
        return jsonify(item), 201

    @app.route("/inventory/<int:item_id>", methods=["PATCH"])
    def update_item(item_id):
        """Update only the fields sent in the JSON body."""
        item = data.find_item(item_id)
        if item is None:
            return jsonify({"error": "Item not found"}), 404

        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"error": "Provide at least one field to update"}), 400
        error = validate_payload(payload, partial=True)
        if error:
            return jsonify({"error": error}), 400

        item.update(payload)
        return jsonify(item), 200

    @app.route("/inventory/<int:item_id>", methods=["DELETE"])
    def delete_item(item_id):
        """Remove an item by id."""
        item = data.find_item(item_id)
        if item is None:
            return jsonify({"error": "Item not found"}), 404
        data.inventory.remove(item)
        return jsonify({"message": f"Item {item_id} deleted"}), 200

    @app.errorhandler(404)
    def not_found(_error):
        """Return JSON instead of HTML for unknown URLs."""
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        """Return JSON when the wrong HTTP method is used."""
        return jsonify({"error": "Method not allowed"}), 405

    return app


if __name__ == "__main__":
    create_app().run(debug=True)  # Flask debug mode, as required in Task 4
