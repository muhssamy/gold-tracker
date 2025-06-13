import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask


def create_app():
    """Create and configure the Flask application"""
    # Create application instance
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Configure logging
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Set up logging
    file_handler = RotatingFileHandler(
        "logs/gold_tracker.log", maxBytes=10240, backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)

    # Add console handler for Docker logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Gold Tracker startup")

    # Set production mode
    app.config["ENV"] = "production"
    app.config["DEBUG"] = False

    # Initialize cache for gold prices and exchange rates
    app.config["PRICE_CACHE"] = {
        "gold_price_usd": None,
        "exchange_rate": None,
        "timestamp": None,
        "last_updated": None,
    }

    # Register API routes
    from routes import register_routes

    register_routes(app)

    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Get port from environment variable
    port = int(os.environ.get("PORT", 8855))

    # Log startup
    app.logger.info(f"Starting Gold Tracker on port {port}")

    # Run the app
    app.run(host="0.0.0.0", port=port)
