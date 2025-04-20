"""
WSGI entry point for production deployment.
This file is used by Gunicorn to run the application.
"""

from app import app

if __name__ == "__main__":
    app.run()
