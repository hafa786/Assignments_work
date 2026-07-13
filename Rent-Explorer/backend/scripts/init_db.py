#!/usr/bin/env python3
"""Apply the idempotent PostGIS schema, including on existing Docker volumes."""

import argparse
import logging
import time
from pathlib import Path

import psycopg
from psycopg import errors

LOGGER = logging.getLogger("db-init")


def apply_schema(database_url: str, schema_path: Path, retries: int = 30) -> None:
    schema_sql = schema_path.read_text(encoding="utf-8")
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            with psycopg.connect(database_url, autocommit=True) as connection:
                connection.execute(schema_sql)
            LOGGER.info("Database schema applied successfully")
            return
        except (psycopg.OperationalError, errors.CannotConnectNow) as exc:
            last_error = exc
            LOGGER.warning("Database not ready (attempt %s/%s): %s", attempt, retries, exc)
            time.sleep(2)

    raise RuntimeError("Could not initialize the database") from last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--schema", type=Path, default=Path("schema.sql"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    apply_schema(args.database_url, args.schema)


if __name__ == "__main__":
    main()
