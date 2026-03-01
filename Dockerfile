FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies into system Python
RUN uv sync --no-dev --frozen

ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY . .

RUN chmod +x run.sh

EXPOSE 8000

CMD ["bash", "./run.sh"]