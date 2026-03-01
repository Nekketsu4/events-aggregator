#!/bin/bash
#set -e

echo "Starting Uvicorn..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1

#wait -n
#
#exit $?