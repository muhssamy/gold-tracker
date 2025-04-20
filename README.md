# Gold Price Tracker - Docker Usage Instructions

This document explains how to use the Gold Price Tracker Docker image with your own API key.

## Getting the Docker Image

```bash
# Pull the image from GitHub Container Registry
docker pull ghcr.io/YOUR-USERNAME/gold-tracker:latest
```

## Running with Docker Run

You can run the container directly with `docker run` by passing your API key as an environment variable:

```bash
# Run with your API key
docker run -d \
  -p 8080:8080 \
  -e GOLD_API_KEY=your_goldapi_key_here \
  -e SECRET_KEY=random_secure_string \
  -v gold_data:/app/data \
  --name gold-tracker \
  ghcr.io/YOUR-USERNAME/gold-tracker:latest
```

## Running with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  gold-tracker:
    image: ghcr.io/YOUR-USERNAME/gold-tracker:latest
    ports:
      - "8080:8080"
    environment:
      - GOLD_API_KEY=${GOLD_API_KEY}  # Use from .env file or environment
      - SECRET_KEY=${SECRET_KEY:-random_secure_string}
    volumes:
      - gold_data:/app/data
    restart: unless-stopped

volumes:
  gold_data:
    # This creates a named volume that persists even if containers are removed
```

Then create a `.env` file in the same directory (do not commit this to version control):

```
GOLD_API_KEY=your_goldapi_key_here
SECRET_KEY=your_random_secure_string
```

Now start the service:

```bash
docker-compose up -d
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOLD_API_KEY` | Your API key from GoldAPI.io | Yes |
| `SECRET_KEY` | A random string for session security | Recommended |
| `PORT` | Port to run the application on (default: 8080) | No |

## Data Persistence

The application stores your gold purchase data in a volume mounted at `/app/data`. This data will persist across container restarts or upgrades.

To view or backup this data:

```bash
# Create a backup of your data
docker run --rm -v gold_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar czvf /backup/gold-data-backup.tar.gz ."
```

## Accessing the Application

After starting the container, access the application at:
```
http://localhost:8080
```

## Troubleshooting

If you encounter issues:

1. Check container logs:
   ```bash
   docker logs gold-tracker
   ```

2. Verify your API key is correct and has not expired

3. Ensure volume permissions are correct