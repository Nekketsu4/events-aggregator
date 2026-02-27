
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client libraries (required by asyncpg)
    libpq-dev \
    # Build tools (needed for compiling some Python packages)
    gcc \
    # curl for healthchecks
    curl \
    # Clean up apt cache to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# # Create non-root user for security
# RUN groupadd --gid 1001 appuser \
#     && useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./

# Install dependencies (without dev extras)
RUN uv sync --no-dev

# Copy application source
COPY . .

# Make run script executable
RUN chmod +x run.sh

# # Change ownership of the app directory to appuser
# RUN chown -R appuser:appuser /app

# # Switch to non-root user
# USER appuser

EXPOSE 8000

CMD ["bash", "./run.sh"]
# CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]