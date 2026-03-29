#!/usr/bin/env bash
set -euo pipefail

# Production deployment script
# Usage: ./scripts/deploy.sh

echo "🚀 Starting production deployment..."

# 1. Validate .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found"
    echo "   Copy .env.production.example to .env and fill in values"
    exit 1
fi

# 2. Validate required env vars
source .env
required_vars=(
    "SECRET_KEY"
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "S3_BUCKET"
    "S3_ACCESS_KEY"
    "S3_SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "❌ ERROR: $var is not set in .env"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# 3. Build images
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# 4. Start infrastructure (db, redis)
echo "🗄️  Starting database and Redis..."
docker-compose -f docker-compose.prod.yml up -d db redis

# Wait for db to be ready
echo "⏳ Waiting for database..."
until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}; do
    sleep 2
done

# 5. Run migrations
echo "🔄 Running migrations..."
docker-compose -f docker-compose.prod.yml run --rm web flask db upgrade

# 6. Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# 7. Wait for health check
echo "⏳ Waiting for application to be healthy..."
sleep 10

max_attempts=30
attempt=0
until curl -f http://localhost/health > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ Health check failed after $max_attempts attempts"
        docker-compose -f docker-compose.prod.yml logs --tail=50 web
        exit 1
    fi
    echo "   Attempt $attempt/$max_attempts..."
    sleep 2
done

echo "✅ Deployment successful!"
echo ""
echo "📊 Service status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🔍 Health check:"
curl -s http://localhost/health | python -m json.tool

echo ""
echo "📝 Next steps:"
echo "   - Configure HTTPS: edit nginx.conf and add TLS certificates"
echo "   - Test file upload"
echo "   - Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
