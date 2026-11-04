"""Client for the OpenFoodFacts API.

Two public functions fetch product data and return it in the same shape
as our inventory items (without price and stock, which are ours to set).
"""

import requests

BASE_URL = "https://world.openfoodfacts.org"
# OpenFoodFacts asks API users to identify their app. Put your own email here.
HEADERS = {"User-Agent": "InventoryLab/1.0 (your-email@example.com)"}
TIMEOUT = 10  # seconds; never call an external API without a timeout


class ExternalAPIError(Exception):
    """Raised when OpenFoodFacts can't be reached or returns unusable data."""


def _clean(product, barcode=""):
    """Keep only the fields our inventory stores."""
    return {
        "barcode": product.get("code", barcode),
        "product_name": (product.get("product_name") or "").strip() or "Unknown product",
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
    }


def fetch_by_barcode(barcode):
    """Return a cleaned product dict, or None if the barcode isn't found.

    Raises ExternalAPIError if the API is unreachable or misbehaves.
    """
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code == 404:
            return None  # OpenFoodFacts uses 404 for unknown barcodes
        response.raise_for_status()
        body = response.json()
    except (requests.exceptions.RequestException, ValueError) as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts: {exc}") from exc

    if body.get("status") != 1:
        return None
    return _clean(body.get("product", {}), barcode)


def search_by_name(name, limit=5):
    """Return a list of cleaned products matching a name (may be empty).

    Raises ExternalAPIError if the API is unreachable or misbehaves.
    """
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit,
    }
    try:
        response = requests.get(
            f"{BASE_URL}/cgi/search.pl", params=params, headers=HEADERS, timeout=TIMEOUT
        )
        response.raise_for_status()
        body = response.json()
    except (requests.exceptions.RequestException, ValueError) as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts: {exc}") from exc

    return [_clean(product) for product in body.get("products", [])]
