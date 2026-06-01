from typing import Any, Callable, Dict, List


PRODUCT_CATALOG = {
    "iphone": {"price": 20000000, "stock": 5, "weight_kg": 0.5},
    "laptop": {"price": 15000000, "stock": 3, "weight_kg": 2.0},
    "headphone": {"price": 1200000, "stock": 10, "weight_kg": 0.3},
}

COUPONS = {
    "WINNER": 10,
    "STUDENT": 15,
    "FREESHIP": 0,
}

CITY_SHIPPING_BASE = {
    "hanoi": 30000,
    "ho chi minh": 35000,
    "danang": 40000,
}


def normalize_text(value: str) -> str:
    return value.strip().lower()


def get_product_info(item_name: str) -> Dict[str, Any]:
    """
    Return price, stock, and weight for a product.

    Example:
        get_product_info("iphone")
    """
    item_key = normalize_text(item_name)
    product = PRODUCT_CATALOG.get(item_key)

    if product is None:
        return {
            "ok": False,
            "error": f"Product '{item_name}' was not found.",
            "available_products": list(PRODUCT_CATALOG.keys()),
        }

    return {
        "ok": True,
        "item_name": item_key,
        "price_vnd": product["price"],
        "stock": product["stock"],
        "weight_kg": product["weight_kg"],
    }


def check_stock(item_name: str, quantity: int) -> Dict[str, Any]:
    """
    Check whether the requested quantity is available.

    Example:
        check_stock("iphone", 2)
    """
    product_info = get_product_info(item_name)
    if not product_info["ok"]:
        return product_info

    stock = product_info["stock"]
    quantity = int(quantity)

    return {
        "ok": quantity <= stock,
        "item_name": product_info["item_name"],
        "requested_quantity": quantity,
        "available_stock": stock,
        "message": "Enough stock." if quantity <= stock else "Not enough stock.",
    }


def get_discount(coupon_code: str) -> Dict[str, Any]:
    """
    Return the discount percentage for a coupon code.

    Example:
        get_discount("STUDENT")
    """
    coupon_key = coupon_code.strip().upper()
    discount_percent = COUPONS.get(coupon_key)

    if discount_percent is None:
        return {
            "ok": False,
            "coupon_code": coupon_key,
            "discount_percent": 0,
            "error": "Invalid coupon code.",
        }

    return {
        "ok": True,
        "coupon_code": coupon_key,
        "discount_percent": discount_percent,
    }


def calculate_shipping(item_name: str, quantity: int, destination: str) -> Dict[str, Any]:
    """
    Calculate shipping fee from product weight, quantity, and destination city.

    Example:
        calculate_shipping("iphone", 2, "hanoi")
    """
    product_info = get_product_info(item_name)
    if not product_info["ok"]:
        return product_info

    city_key = normalize_text(destination)
    base_fee = CITY_SHIPPING_BASE.get(city_key)

    if base_fee is None:
        return {
            "ok": False,
            "destination": destination,
            "error": "Unsupported destination.",
            "supported_destinations": list(CITY_SHIPPING_BASE.keys()),
        }

    quantity = int(quantity)
    total_weight = product_info["weight_kg"] * quantity
    extra_weight_fee = max(0, total_weight - 1) * 10000

    return {
        "ok": True,
        "destination": city_key,
        "total_weight_kg": total_weight,
        "shipping_fee_vnd": int(base_fee + extra_weight_fee),
    }


def calculate_order_total(
    item_name: str,
    quantity: int,
    coupon_code: str,
    destination: str,
) -> Dict[str, Any]:
    """
    Calculate final order total including discount and shipping.

    Example:
        calculate_order_total("iphone", 2, "WINNER", "hanoi")
    """
    product_info = get_product_info(item_name)
    if not product_info["ok"]:
        return product_info

    stock_info = check_stock(item_name, quantity)
    if not stock_info["ok"]:
        return stock_info

    discount_info = get_discount(coupon_code)
    if not discount_info["ok"]:
        return discount_info

    shipping_info = calculate_shipping(item_name, quantity, destination)
    if not shipping_info["ok"]:
        return shipping_info

    quantity = int(quantity)
    subtotal = product_info["price_vnd"] * quantity
    discount_amount = subtotal * discount_info["discount_percent"] / 100
    final_total = subtotal - discount_amount + shipping_info["shipping_fee_vnd"]

    return {
        "ok": True,
        "item_name": product_info["item_name"],
        "quantity": quantity,
        "unit_price_vnd": product_info["price_vnd"],
        "subtotal_vnd": subtotal,
        "discount_percent": discount_info["discount_percent"],
        "discount_amount_vnd": int(discount_amount),
        "shipping_fee_vnd": shipping_info["shipping_fee_vnd"],
        "final_total_vnd": int(final_total),
    }


ECOMMERCE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_product_info",
        "description": (
            "Get product price, stock, and weight. "
            "Input: item_name as string. Example: get_product_info('iphone')."
        ),
        "function": get_product_info,
    },
    {
        "name": "check_stock",
        "description": (
            "Check if a product has enough stock. "
            "Input: item_name as string, quantity as integer. "
            "Example: check_stock('iphone', 2)."
        ),
        "function": check_stock,
    },
    {
        "name": "get_discount",
        "description": (
            "Get discount percentage for a coupon code. "
            "Input: coupon_code as string. Example: get_discount('STUDENT')."
        ),
        "function": get_discount,
    },
    {
        "name": "calculate_shipping",
        "description": (
            "Calculate shipping fee in VND. "
            "Input: item_name as string, quantity as integer, destination as string. "
            "Example: calculate_shipping('iphone', 2, 'hanoi')."
        ),
        "function": calculate_shipping,
    },
    {
        "name": "calculate_order_total",
        "description": (
            "Calculate final order total in VND including product price, discount, and shipping. "
            "Input: item_name as string, quantity as integer, coupon_code as string, destination as string. "
            "Example: calculate_order_total('iphone', 2, 'WINNER', 'hanoi')."
        ),
        "function": calculate_order_total,
    },
]