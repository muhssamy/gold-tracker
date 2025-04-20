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

# Create data directory if it doesn't exist
RUN mkdir -p data

# Expose port 8080
EXPOSE 8080

# Run with Gunicorn (production server) instead of Flask's development server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]