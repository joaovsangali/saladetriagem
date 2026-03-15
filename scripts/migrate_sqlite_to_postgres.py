#!/usr/bin/env python3
"""Migrate data from SQLite to PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_postgres.py \\
        --sqlite triagem.db \\
        --postgres postgresql://user:pass@localhost/triagem_db
"""

import argparse
import sys


def migrate(sqlite_url: str, postgres_url: str) -> None:
    try:
        import sqlalchemy as sa
    except ImportError:
        print("sqlalchemy is required: pip install sqlalchemy psycopg2-binary")
        sys.exit(1)

    print(f"Source: {sqlite_url}")
    print(f"Target: {postgres_url}")

    src_engine = sa.create_engine(sqlite_url)
    dst_engine = sa.create_engine(postgres_url)

    # Reflect all tables from SQLite
    meta = sa.MetaData()
    meta.reflect(bind=src_engine)

    # Create tables in PostgreSQL
    meta.create_all(dst_engine)

    # Copy data table by table
    with src_engine.connect() as src_conn:
        with dst_engine.connect() as dst_conn:
            for table in meta.sorted_tables:
                rows = src_conn.execute(table.select()).fetchall()
                if not rows:
                    print(f"  {table.name}: (empty, skipped)")
                    continue
                dst_conn.execute(table.insert(), [dict(r._mapping) for r in rows])
                dst_conn.commit()
                print(f"  {table.name}: {len(rows)} rows copied")

    print("Migration complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite → PostgreSQL")
    parser.add_argument("--sqlite", required=True, help="Path to SQLite file")
    parser.add_argument("--postgres", required=True, help="PostgreSQL connection URL")
    args = parser.parse_args()

    sqlite_url = f"sqlite:///{args.sqlite}" if not args.sqlite.startswith("sqlite") else args.sqlite
    migrate(sqlite_url, args.postgres)


if __name__ == "__main__":
    main()
