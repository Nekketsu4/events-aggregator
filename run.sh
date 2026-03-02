#!/bin/bash

echo "=== Running migrations ==="
alembic upgrade head || echo "=== WARNING: migrations failed, starting anyway ==="

echo "=== Starting Uvicorn on 0.0.0.0:8000 ==="
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1