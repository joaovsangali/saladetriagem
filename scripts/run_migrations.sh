#!/usr/bin/env bash
set -euo pipefail

# Run database migrations safely in production
# Usage: ./scripts/run_migrations.sh

echo "🔄 Running database migrations..."

docker-compose -f docker-compose.prod.yml exec -T web flask db upgrade

echo "✅ Migrations completed successfully"
