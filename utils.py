import json
import os
import uuid
from datetime import datetime

# File to store purchases
DATA_DIR = "data"
PURCHASES_FILE = os.path.join(DATA_DIR, "purchases.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


def generate_id():
    """Generate a unique ID for a purchase"""
    return str(uuid.uuid4())


def calculate_profit_loss(purchase_price, current_price, grams):
    """
    Calculate profit/loss based on purchase and current prices

    Args:
        purchase_price (float): Price per gram at time of purchase (SAR)
        current_price (float): Current price per gram (SAR)
        grams (float): Amount of gold in grams

    Returns:
        dict: Dictionary containing calculation results
    """
    purchase_value = purchase_price * grams
    current_value = current_price * grams

    profit_loss = current_value - purchase_value
    profit_loss_percentage = (
        (profit_loss / purchase_value) * 100 if purchase_value > 0 else 0
    )

    return {
        "purchase_value": round(purchase_value, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "profit_loss_percentage": round(profit_loss_percentage, 2),
        "is_profit": profit_loss >= 0,
    }


def get_all_purchases():
    """Get all purchases from storage"""
    if not os.path.exists(PURCHASES_FILE):
        return []

    try:
        with open(PURCHASES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_purchases(purchases):
    """Save purchases to storage"""
    with open(PURCHASES_FILE, "w") as f:
        json.dump(purchases, f, indent=2)


def add_purchase(purchase):
    """Add a new purchase"""
    purchases = get_all_purchases()
    purchases.append(purchase)
    save_purchases(purchases)
    return purchase


def delete_purchase(purchase_id):
    """Delete a purchase by ID"""
    purchases = get_all_purchases()
    initial_count = len(purchases)

    purchases = [p for p in purchases if p.get("id") != purchase_id]

    if len(purchases) < initial_count:
        save_purchases(purchases)
        return True

    return False
