import csv
import io
import os
import time
from datetime import datetime

import requests
from flask import jsonify, render_template, request, send_file, session

import utils

# Get API key from environment variable
API_KEY = os.environ.get("GOLD_API_KEY", "")


def register_routes(app):
    """Register all routes with the Flask application"""

    def get_usd_to_sar_rate(force_refresh=False):
        """
        Get the USD to SAR conversion rate with caching

        Args:
            force_refresh (bool): If True, bypass cache and fetch fresh data
        """
        price_cache = app.config["PRICE_CACHE"]

        # Return cached exchange rate if available and not forced to refresh
        current_time = time.time()
        cache_valid = (
            price_cache["exchange_rate"] is not None
            and price_cache["timestamp"] is not None
            and current_time - price_cache["timestamp"] < 3600  # Cache valid for 1 hour
            and not force_refresh
        )

        if cache_valid:
            app.logger.debug("Using cached exchange rate")
            return price_cache["exchange_rate"]

        try:
            app.logger.info("Fetching fresh exchange rate data")
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
            app.logger.error(f"Error fetching exchange rate: {e}")

        # Fallback to a fixed rate if API fails
        app.logger.warning("Using fallback exchange rate")
        return 3.75  # Fixed approximate USD to SAR rate

    def get_gold_price_usd(force_refresh=False):
        """
        Get the current gold price in USD with caching

        Args:
            force_refresh (bool): If True, bypass cache and fetch fresh data
        """
        price_cache = app.config["PRICE_CACHE"]

        # Return cached gold price if available and not forced to refresh
        current_time = time.time()
        cache_valid = (
            price_cache["gold_price_usd"] is not None
            and price_cache["timestamp"] is not None
            and current_time - price_cache["timestamp"] < 3600  # Cache valid for 1 hour
            and not force_refresh
        )

        if cache_valid:
            app.logger.debug("Using cached gold price")
            return price_cache["gold_price_usd"]

        try:
            app.logger.info("Fetching fresh gold price data")
            # Call GoldAPI to get current gold price in USD
            headers = {"x-access-token": API_KEY, "Content-Type": "application/json"}
            response = requests.get(
                "https://www.goldapi.io/api/XAU/USD", headers=headers
            )

            if response.status_code == 200:
                data = response.json()

                # Extract price data
                if "price_gram_24k" in data:
                    price_per_gram_usd = data["price_gram_24k"]
                    app.logger.debug(f"Got price_gram_24k: {price_per_gram_usd}")
                elif "price" in data and data["price"] is not None:
                    price_per_gram_usd = data["price"] / 31.1035
                    app.logger.debug(f"Calculated price per gram: {price_per_gram_usd}")
                else:
                    app.logger.error("No price data found in API response")
                    return None

                # Update cache
                price_cache["gold_price_usd"] = price_per_gram_usd
                price_cache["timestamp"] = current_time
                price_cache["last_updated"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                return price_per_gram_usd
        except Exception as e:
            app.logger.error(f"Error fetching gold price: {e}")

        return None

    @app.route("/")
    def index():
        """Render the main page"""
        app.logger.info("Serving index page")
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
                app.logger.error("Failed to get gold price data")
                return jsonify(
                    {"success": False, "message": "Failed to get gold price data"}
                )

            # Get USD to SAR conversion rate (from cache or API)
            usd_to_sar = get_usd_to_sar_rate(force_refresh)

            # Convert to SAR
            price_per_gram_sar = price_per_gram_usd * usd_to_sar
            price_cache = app.config["PRICE_CACHE"]

            app.logger.info(
                f"Current gold price: {price_per_gram_sar} SAR/g (from {'API' if force_refresh else 'cache'})"
            )
            return jsonify(
                {
                    "success": True,
                    "price": price_per_gram_sar,
                    "price_usd": price_per_gram_usd,
                    "currency": "SAR",
                    "exchange_rate": usd_to_sar,
                    "timestamp": price_cache["timestamp"],
                    "last_updated": price_cache["last_updated"],
                    "cached": not force_refresh
                    and price_cache["timestamp"] is not None,
                }
            )
        except Exception as e:
            app.logger.error(f"Error in get_current_price: {str(e)}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})

    @app.route("/api/historical-price", methods=["GET"])
    def get_historical_price():
        """Get the historical gold price from GoldAPI in USD and convert to SAR"""
        try:
            date = request.args.get("date")
            if not date:
                app.logger.warning("Missing date parameter in historical price request")
                return jsonify(
                    {"success": False, "message": "Date parameter is required"}
                )

            # Format date as YYYYMMDD for the API
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%Y%m%d")

            # Call GoldAPI to get historical gold price in USD
            headers = {"x-access-token": API_KEY, "Content-Type": "application/json"}
            url = f"https://www.goldapi.io/api/XAU/USD/{formatted_date}"
            app.logger.info(f"Fetching historical price for date: {date}")
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
                    app.logger.debug(
                        f"Historical price from price_gram_24k: {price_per_gram_sar} SAR/g"
                    )
                # Fallback to calculating from price if available
                elif "price" in data and data["price"] is not None:
                    price_per_gram_usd = data["price"] / 31.1035
                    # Convert to SAR
                    price_per_gram_sar = price_per_gram_usd * usd_to_sar
                    app.logger.debug(
                        f"Historical price calculated from price: {price_per_gram_sar} SAR/g"
                    )
                else:
                    app.logger.error("No price data found in historical API response")
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
                app.logger.error(f"API Error: {response.status_code} - {response.text}")
                return jsonify(
                    {
                        "success": False,
                        "message": f"API Error: {response.status_code} - {response.text}",
                    }
                )
        except Exception as e:
            app.logger.error(f"Error in get_historical_price: {str(e)}")
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
                app.logger.error("Failed to get gold price data for purchases")
                return jsonify(
                    {"success": False, "message": "Failed to get gold price data"}
                )

            # Get USD to SAR conversion rate (from cache or API)
            usd_to_sar = get_usd_to_sar_rate(force_refresh)

            # Convert to SAR
            current_price = price_per_gram_usd * usd_to_sar
            price_cache = app.config["PRICE_CACHE"]

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
                (total_profit_loss / total_investment) * 100
                if total_investment > 0
                else 0
            )

            app.logger.info(
                f"Calculated purchases profit/loss. Total: {total_profit_loss} SAR"
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
            app.logger.error(f"Error in get_purchases: {str(e)}")
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
            app.logger.info(
                f"Added new purchase: {purchase['grams']}g at {purchase['purchase_price']} SAR/g"
            )

            return jsonify({"success": True, "purchase": purchase})
        except Exception as e:
            app.logger.error(f"Error adding purchase: {str(e)}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})

    @app.route("/api/purchases/<purchase_id>", methods=["DELETE"])
    def delete_purchase(purchase_id):
        """Delete a purchase"""
        try:
            success = utils.delete_purchase(purchase_id)

            if success:
                app.logger.info(f"Deleted purchase: {purchase_id}")
                return jsonify({"success": True})
            else:
                app.logger.warning(f"Purchase not found for deletion: {purchase_id}")
                return jsonify(
                    {
                        "success": False,
                        "message": f"Purchase not found with ID: {purchase_id}",
                    }
                )
        except Exception as e:
            app.logger.error(f"Error deleting purchase: {str(e)}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})

    @app.route("/api/export", methods=["GET"])
    def export_data():
        """Export all purchase data as CSV"""
        try:
            purchases = utils.get_all_purchases()

            if not purchases:
                return jsonify(
                    {"success": False, "message": "No purchase data to export"}
                )

            # Create in-memory CSV file
            output = io.StringIO()
            fieldnames = [
                "id",
                "purchase_date",
                "purchase_price",
                "grams",
                "description",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)

            writer.writeheader()
            for purchase in purchases:
                # Only write the fields we want to export
                export_row = {field: purchase.get(field, "") for field in fieldnames}
                writer.writerow(export_row)

            # Prepare the CSV for download
            output.seek(0)

            # Generate a filename with current date
            filename = f"gold_purchases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            app.logger.info(f"Exporting {len(purchases)} purchases to CSV")
            return send_file(
                io.BytesIO(output.getvalue().encode("utf-8")),
                mimetype="text/csv",
                as_attachment=True,
                download_name=filename,
            )
        except Exception as e:
            app.logger.error(f"Error exporting data: {str(e)}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})

    @app.route("/api/import", methods=["POST"])
    def import_data():
        """Import purchase data from CSV"""
        try:
            if "file" not in request.files:
                return jsonify({"success": False, "message": "No file part"})

            file = request.files["file"]

            if file.filename == "":
                return jsonify({"success": False, "message": "No selected file"})

            if not file.filename.endswith(".csv"):
                return jsonify(
                    {"success": False, "message": "Only CSV files are supported"}
                )

            # Read CSV file
            content = file.read().decode("utf-8")
            csv_data = csv.DictReader(io.StringIO(content))

            # Validate CSV structure
            required_fields = ["purchase_date", "purchase_price", "grams"]
            for field in required_fields:
                if field not in csv_data.fieldnames:
                    return jsonify(
                        {
                            "success": False,
                            "message": f"Missing required field: {field}",
                        }
                    )

            # Process rows
            imported_count = 0
            error_count = 0

            for row in csv_data:
                try:
                    # Skip rows with missing required fields
                    if not all(row.get(field) for field in required_fields):
                        error_count += 1
                        continue

                    # Create purchase record
                    purchase = {
                        "id": utils.generate_id(),  # Generate new ID even if one exists in CSV
                        "purchase_date": row["purchase_date"],
                        "purchase_price": float(row["purchase_price"]),
                        "grams": float(row["grams"]),
                        "description": row.get("description", ""),
                    }

                    # Validate date format
                    try:
                        datetime.strptime(purchase["purchase_date"], "%Y-%m-%d")
                    except ValueError:
                        error_count += 1
                        continue

                    # Add to database
                    utils.add_purchase(purchase)
                    imported_count += 1

                except Exception as e:
                    app.logger.error(f"Error importing row: {str(e)}")
                    error_count += 1

            app.logger.info(
                f"Imported {imported_count} purchases with {error_count} errors"
            )
            return jsonify(
                {
                    "success": True,
                    "imported_count": imported_count,
                    "error_count": error_count,
                    "message": f"Successfully imported {imported_count} purchases"
                    + (f" with {error_count} errors" if error_count > 0 else ""),
                }
            )

        except Exception as e:
            app.logger.error(f"Error importing data: {str(e)}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})

    # Health check endpoint for monitoring
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint for monitoring"""
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
