#!/usr/bin/env bash
# scripts/health_check.sh
# Quick health check for the running application.

HOST="${1:-localhost}"
PORT="${2:-8000}"
URL="http://${HOST}:${PORT}/health"

echo "Checking $URL ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Health check passed (HTTP $HTTP_CODE)"
    exit 0
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    exit 1
fi
