#!/usr/bin/env bash
# scripts/backup.sh — Automated database backup script
# Usage: ./scripts/backup.sh
# Requires: DATABASE_URL env var, pg_dump for PostgreSQL

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/triagem}"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_URL="${DATABASE_URL:-}"

if [ -z "$DB_URL" ]; then
    echo "ERROR: DATABASE_URL is not set"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

if [[ "$DB_URL" == postgresql* ]]; then
    FILENAME="$BACKUP_DIR/triagem_pg_${DATE}.dump"
    echo "Backing up PostgreSQL to $FILENAME ..."
    pg_dump --dbname="$DB_URL" --format=custom --file="$FILENAME"
    echo "✅ PostgreSQL backup complete: $FILENAME"
elif [[ "$DB_URL" == sqlite* ]]; then
    # Extract path from sqlite:///path
    SQLITE_PATH="${DB_URL#sqlite:///}"
    FILENAME="$BACKUP_DIR/triagem_sqlite_${DATE}.db"
    echo "Backing up SQLite ($SQLITE_PATH) to $FILENAME ..."
    cp "$SQLITE_PATH" "$FILENAME"
    echo "✅ SQLite backup complete: $FILENAME"
else
    echo "ERROR: Unsupported database URL: $DB_URL"
    exit 1
fi

# Keep only the last 7 backups
find "$BACKUP_DIR" -name "triagem_*" -mtime +7 -delete
echo "Old backups cleaned up."

