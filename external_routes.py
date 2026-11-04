"""Routes that use the OpenFoodFacts API (kept separate from app.py)."""

from flask import Blueprint, jsonify, request

import data
import openfoodfacts_client
from openfoodfacts_client import ExternalAPIError

external_bp = Blueprint("external", __name__)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@external_bp.route("/external/lookup", methods=["GET"])
def lookup():
    """Look a product up on OpenFoodFacts by ?barcode= or ?name=.

    Read-only: nothing is added to the inventory.
    """
    barcode = request.args.get("barcode", "").strip()
    name = request.args.get("name", "").strip()
    if not barcode and not name:
        return jsonify({"error": "Provide a 'barcode' or 'name' query parameter"}), 400

    try:
        if barcode:
            product = openfoodfacts_client.fetch_by_barcode(barcode)
            results = [product] if product else []
        else:
            results = openfoodfacts_client.search_by_name(name)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502

    if not results:
        return jsonify({"error": "No matching product found"}), 404
    return jsonify(results), 200


@external_bp.route("/inventory/import/<barcode>", methods=["POST"])
def import_product(barcode):
    """Fetch a product by barcode and add it to the inventory array."""
    payload = request.get_json(silent=True) or {}
    price = payload.get("price", 0.0)
    stock = payload.get("stock", 0)

    # Validate before touching the network.
    if not _is_number(price) or price < 0:
        return jsonify({"error": "price must be a non-negative number"}), 400
    if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
        return jsonify({"error": "stock must be a non-negative integer"}), 400

    try:
        product = openfoodfacts_client.fetch_by_barcode(barcode)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    if product is None:
        return jsonify({"error": "Product not found on OpenFoodFacts"}), 404

    if any(item["barcode"] == product["barcode"] for item in data.inventory):
        return jsonify({"error": "A product with this barcode is already in inventory"}), 409

    item = {"id": data.get_next_id(), **product, "price": price, "stock": stock}
    data.inventory.append(item)
    return jsonify(item), 201
