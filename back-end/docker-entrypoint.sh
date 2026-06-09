#!/bin/sh
set -e

# Apply any pending Prisma migrations before the API starts.
echo "Running database migrations..."
npx prisma migrate deploy

echo "Starting server..."
exec "$@"
