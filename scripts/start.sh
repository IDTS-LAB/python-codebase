#!/bin/bash
# start.sh

echo "Running database migrations..."
poetry run alembic upgrade head

if [ $? -ne 0 ]; then
    echo "Migration failed!"
    exit 1
fi

echo "Starting FastAPI application..."
exec poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4