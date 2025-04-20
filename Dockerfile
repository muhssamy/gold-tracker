FROM python:3.9-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-root --no-interaction --no-ansi

# Copy application files
COPY . .

# Create data directory with proper permissions
RUN mkdir -p data && chmod 777 data

# Expose port (PORT can be overridden by environment variable)
EXPOSE 8080

# Set environment variables with defaults
ENV PORT=8080 \
    GOLD_API_KEY="" \
    SECRET_KEY="dev-only-key-replace-in-production" \
    WORKERS=4

# Run with Gunicorn for production
CMD gunicorn --bind 0.0.0.0:${PORT} --workers ${WORKERS} --access-logfile - --error-logfile - app:app