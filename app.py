import json
import os
import time
from datetime import datetime, timedelta

import requests
from flask import Flask, jsonify, render_template, request, session

import utils

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Get API key from environment variable
API_KEY = os.environ.get("GOLD_API_KEY", "")

# Cache for gold prices and exchange rates
price_cache = {
    "gold_price_usd": None,
    "exchange_rate": None,
    "timestamp": None,
    "last_updated": None,
}


def get_usd_to_sar_rate(force_refresh=False):
    """
    Get the USD to SAR conversion rate with caching

    Args:
        force_refresh (bool): If True, bypass cache and fetch fresh data
    """
    global price_cache

    # Return cached exchange rate if available and not forced to refresh
    current_time = time.time()
    cache_valid = (
        price_cache["exchange_rate"] is not None
        and price_cache["timestamp"] is not None
        and current_time - price_cache["timestamp"] < 3600  # Cache valid for 1 hour
        and not force_refresh
    )

    if cache_valid:
        return price_cache["exchange_rate"]

    try:
        # Try to fetch from an exchange rate API
        response = requests.get("https://open.er-api.com/v6/latest/USD")
        if response.status_code == 200:
            data = response.json()
            rate = data["rates"]["SAR"]

            # Update cache
            price_cache["exchange_rate"] = rate
            if price_cache["timestamp"] is None:
                price_cache["timestamp"] = current_time

            return rate
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")

    # Fallback to a fixed rate if API fails
    return 3.75  # Fixed approximate USD to SAR rate


def get_gold_price_usd(force_refresh=False):
    """
    Get the current gold price in USD with caching

    Args:
        force_refresh (bool): If True, bypass cache and fetch fresh data
    """
    global price_cache

    # Return cached gold price if available and not forced to refresh
    current_time = time.time()
    cache_valid = (
        price_cache["gold_price_usd"] is not None
        and price_cache["timestamp"] is not None
        and current_time - price_cache["timestamp"] < 3600  # Cache valid for 1 hour
        and not force_refresh
    )

    if cache_valid:
        return price_cache["gold_price_usd"]

    try:
        # Call GoldAPI to get current gold price in USD
        headers = {"x-access-token": API_KEY, "Content-Type": "application/json"}
        response = requests.get("https://www.goldapi.io/api/XAU/USD", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Extract price data
            if "price_gram_24k" in data:
                price_per_gram_usd = data["price_gram_24k"]
            elif "price" in data and data["price"] is not None:
                price_per_gram_usd = data["price"] / 31.1035
            else:
                return None

            # Update cache
            price_cache["gold_price_usd"] = price_per_gram_usd
            price_cache["timestamp"] = current_time
            price_cache["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return price_per_gram_usd
    except Exception as e:
        print(f"Error fetching gold price: {e}")

    return None


@app.route("/")
def index():
    """Render the main page"""
    return render_template("index.html")


@app.route("/api/current-price", methods=["GET"])
def get_current_price():
    """Get the current gold price from cache or API"""
    try:
        # Check if we should force a refresh
        force_refresh = request.args.get("refresh", "false").lower() == "true"

        # Get gold price in USD (from cache or API)
        price_per_gram_usd = get_gold_price_usd(force_refresh)

        if price_per_gram_usd is None:
            return jsonify(
                {"success": False, "message": "Failed to get gold price data"}
            )

        # Get USD to SAR conversion rate (from cache or API)
        usd_to_sar = get_usd_to_sar_rate(force_refresh)

        # Convert to SAR
        price_per_gram_sar = price_per_gram_usd * usd_to_sar

        return jsonify(
            {
                "success": True,
                "price": price_per_gram_sar,
                "price_usd": price_per_gram_usd,
                "currency": "SAR",
                "exchange_rate": usd_to_sar,
                "timestamp": price_cache["timestamp"],
                "last_updated": price_cache["last_updated"],
                "cached": not force_refresh and price_cache["timestamp"] is not None,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route("/api/historical-price", methods=["GET"])
def get_historical_price():
    """Get the historical gold price from GoldAPI in USD and convert to SAR"""
    try:
        date = request.args.get("date")
        if not date:
            return jsonify({"success": False, "message": "Date parameter is required"})

        # Format date as YYYYMMDD for the API
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%Y%m%d")

        # Call GoldAPI to get historical gold price in USD
        headers = {"x-access-token": API_KEY, "Content-Type": "application/json"}
        url = f"https://www.goldapi.io/api/XAU/USD/{formatted_date}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Get USD to SAR conversion rate (use cached rate)
            usd_to_sar = get_usd_to_sar_rate(False)

            # Use price_gram_24k directly (already in price per gram)
            if "price_gram_24k" in data:
                price_per_gram_usd = data["price_gram_24k"]
                # Convert to SAR
                price_per_gram_sar = price_per_gram_usd * usd_to_sar
            # Fallback to calculating from price if available
            elif "price" in data and data["price"] is not None:
                price_per_gram_usd = data["price"] / 31.1035
                # Convert to SAR
                price_per_gram_sar = price_per_gram_usd * usd_to_sar
            else:
                return jsonify(
                    {
                        "success": False,
                        "message": "Gold price data not available in API response",
                    }
                )

            return jsonify(
                {
                    "success": True,
                    "price": price_per_gram_sar,
                    "price_usd": price_per_gram_usd,
                    "currency": "SAR",
                    "exchange_rate": usd_to_sar,
                    "date": date,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": f"API Error: {response.status_code} - {response.text}",
                }
            )
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route("/api/purchases", methods=["GET"])
def get_purchases():
    """Get all purchases with profit/loss calculation"""
    purchases = utils.get_all_purchases()

    try:
        # Check if we should force a refresh
        force_refresh = request.args.get("refresh", "false").lower() == "true"

        # Get gold price in USD (from cache or API)
        price_per_gram_usd = get_gold_price_usd(force_refresh)

        if price_per_gram_usd is None:
            return jsonify(
                {"success": False, "message": "Failed to get gold price data"}
            )

        # Get USD to SAR conversion rate (from cache or API)
        usd_to_sar = get_usd_to_sar_rate(force_refresh)

        # Convert to SAR
        current_price = price_per_gram_usd * usd_to_sar

        # Calculate profit/loss for each purchase
        total_investment = 0
        total_current_value = 0

        for purchase in purchases:
            # Calculate individual purchase values
            result = utils.calculate_profit_loss(
                float(purchase["purchase_price"]),
                current_price,
                float(purchase["grams"]),
            )

            purchase.update(result)
            purchase["current_price"] = current_price

            # Add to totals
            total_investment += result["purchase_value"]
            total_current_value += result["current_value"]

        # Calculate total profit/loss
        total_profit_loss = total_current_value - total_investment
        total_profit_loss_percentage = (
            (total_profit_loss / total_investment) * 100 if total_investment > 0 else 0
        )

        return jsonify(
            {
                "success": True,
                "purchases": purchases,
                "summary": {
                    "total_investment": round(total_investment, 2),
                    "total_current_value": round(total_current_value, 2),
                    "total_profit_loss": round(total_profit_loss, 2),
                    "total_profit_loss_percentage": round(
                        total_profit_loss_percentage, 2
                    ),
                    "is_profit": total_profit_loss >= 0,
                    "current_price": current_price,
                    "exchange_rate": usd_to_sar,
                    "last_updated": price_cache["last_updated"],
                    "cached": not force_refresh
                    and price_cache["timestamp"] is not None,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route("/api/purchases", methods=["POST"])
def add_purchase():
    """Add a new purchase"""
    try:
        data = request.json
        purchase = {
            "id": utils.generate_id(),
            "purchase_date": data.get("purchase_date"),
            "purchase_price": float(data.get("purchase_price", 0)),
            "grams": float(data.get("grams", 0)),
            "description": data.get("description", ""),
        }

        utils.add_purchase(purchase)

        return jsonify({"success": True, "purchase": purchase})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route("/api/purchases/<purchase_id>", methods=["DELETE"])
def delete_purchase(purchase_id):
    """Delete a purchase"""
    try:
        success = utils.delete_purchase(purchase_id)

        if success:
            return jsonify({"success": True})
        else:
            return jsonify(
                {
                    "success": False,
                    "message": f"Purchase not found with ID: {purchase_id}",
                }
            )
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
