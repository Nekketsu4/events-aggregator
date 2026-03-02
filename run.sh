#!/bin/bash

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting Uvicorn..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
