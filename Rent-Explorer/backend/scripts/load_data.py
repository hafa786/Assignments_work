#!/usr/bin/env python3
"""Load listings CSV and area GeoJSON while skipping malformed records.

Expected listing columns (aliases accepted):
external_id/id, title, rent/monthly_rent, size_m2/size, rooms,
property_type/type, address, lat/latitude, lng/lon/longitude.
"""

import argparse
import csv
import json
import logging
import math
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

LOGGER = logging.getLogger("loader")


def first_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip().replace(",", "."))
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def parse_int(value: Any) -> int | None:
    parsed = parse_float(value)
    return int(parsed) if parsed is not None and parsed.is_integer() else None


def load_areas(connection: psycopg.Connection, path: Path) -> tuple[int, int]:
    document = json.loads(path.read_text(encoding="utf-8"))
    loaded = skipped = 0
    for index, feature in enumerate(document.get("features", [])):
        geometry = feature.get("geometry")
        props = feature.get("properties") or {}
        name = first_value(props, "name", "nimi", "NAME", "area_name")
        external_id = str(first_value(props, "id", "external_id", "area_id", "area_code") or index)
        if not geometry or not name:
            skipped += 1
            LOGGER.warning("Skipping area row %s: missing geometry/name", index)
            continue
        try:
            with connection.transaction():
                connection.execute(
                    """
                    INSERT INTO areas (external_id, name, geom)
                    VALUES (%s, %s, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)))
                    ON CONFLICT (external_id) DO UPDATE
                    SET name = EXCLUDED.name, geom = EXCLUDED.geom
                    """,
                    (external_id, str(name), json.dumps(geometry)),
                )
            loaded += 1
        except Exception as exc:  # isolate malformed source features
            skipped += 1
            LOGGER.warning("Skipping area row %s: %s", index, exc)
    connection.commit()
    return loaded, skipped


def load_listings(connection: psycopg.Connection, path: Path) -> tuple[int, int]:
    loaded = skipped = 0
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        for line_number, row in enumerate(csv.DictReader(csv_file), start=2):
            rent = parse_float(first_value(row, "rent", "rent_eur", "monthly_rent", "price"))
            size_m2 = parse_float(first_value(row, "size_m2", "size", "area_m2"))
            rooms = parse_int(first_value(row, "rooms", "room_count"))
            lat = parse_float(first_value(row, "lat", "latitude"))
            lng = parse_float(first_value(row, "lng", "lon", "longitude"))
            external_id = str(first_value(row, "external_id", "id", "listing_id") or f"row-{line_number}")

            if (
                rent is None
                or rent < 0
                or lat is None
                or lng is None
                or not (-90 <= lat <= 90)
                or not (-180 <= lng <= 180)
            ):
                skipped += 1
                LOGGER.warning("Skipping listing line %s: invalid rent/coordinates", line_number)
                continue
            if size_m2 is not None and size_m2 <= 0:
                size_m2 = None
            if rooms is not None and rooms <= 0:
                rooms = None

            try:
                with connection.transaction():
                    connection.execute(
                        """
                        INSERT INTO listings (
                            external_id, title, rent, size_m2, rooms,
                            property_type, address, listed_date, geom, raw_data
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s
                        )
                        ON CONFLICT (external_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            rent = EXCLUDED.rent,
                            size_m2 = EXCLUDED.size_m2,
                            rooms = EXCLUDED.rooms,
                            property_type = EXCLUDED.property_type,
                            address = EXCLUDED.address,
                            listed_date = EXCLUDED.listed_date,
                            geom = EXCLUDED.geom,
                            raw_data = EXCLUDED.raw_data
                        """,
                        (
                            external_id,
                            first_value(row, "title", "name"),
                            rent,
                            size_m2,
                            rooms,
                            first_value(row, "property_type", "type"),
                            first_value(row, "address", "street_address"),
                            first_value(row, "listed_date", "date", "published_date"),
                            lng,
                            lat,
                            Jsonb(row),
                        ),
                    )
                loaded += 1
            except Exception as exc:
                skipped += 1
                LOGGER.warning("Skipping listing line %s: %s", line_number, exc)
    connection.commit()
    return loaded, skipped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--listings", type=Path, required=True)
    parser.add_argument("--areas", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with psycopg.connect(args.database_url) as connection:
        areas_loaded, areas_skipped = load_areas(connection, args.areas)
        listings_loaded, listings_skipped = load_listings(connection, args.listings)

    LOGGER.info("Areas: loaded=%s skipped=%s", areas_loaded, areas_skipped)
    LOGGER.info("Listings: loaded=%s skipped=%s", listings_loaded, listings_skipped)


if __name__ == "__main__":
    main()
