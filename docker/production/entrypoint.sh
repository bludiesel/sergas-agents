#!/bin/bash
# Sergas Super Account Manager - Production Entrypoint Script

set -e

echo "==================================="
echo "Sergas Super Account Manager"
echo "Environment: ${ENVIRONMENT:-production}"
echo "Version: ${VERSION:-latest}"
echo "==================================="

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z ${DATABASE_HOST:-localhost} ${DATABASE_PORT:-5432}; do
  sleep 1
done
echo "Database is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-localhost} ${REDIS_PORT:-6379}; do
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
  echo "Migrations completed!"
fi

# Create initial data if needed
if [ "${CREATE_INITIAL_DATA:-false}" = "true" ]; then
  echo "Creating initial data..."
  python -m src.cli init-data
  echo "Initial data created!"
fi

# Start application
echo "Starting application..."
exec "$@"
