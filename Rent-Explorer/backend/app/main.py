from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg import sql

from .config import settings
from .db import get_connection, pool
from .models import AreaFeatureCollection, ListingFeatureCollection


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool.open()
    pool.wait()
    try:
        yield
    finally:
        pool.close()


app = FastAPI(
    title="Helsinki Listings Spatial API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    with get_connection() as connection:
        connection.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/listings", response_model=ListingFeatureCollection)
def get_listings(
    min_lng: Annotated[float, Query(ge=-180, le=180)],
    min_lat: Annotated[float, Query(ge=-90, le=90)],
    max_lng: Annotated[float, Query(ge=-180, le=180)],
    max_lat: Annotated[float, Query(ge=-90, le=90)],
    rent_min: Annotated[float | None, Query(ge=0)] = None,
    rent_max: Annotated[float | None, Query(ge=0)] = None,
    rooms: Annotated[int | None, Query(ge=1, le=20)] = None,
    property_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 2000,
) -> dict:
    if min_lng >= max_lng or min_lat >= max_lat:
        raise HTTPException(status_code=422, detail="Invalid bounding box")
    if rent_min is not None and rent_max is not None and rent_min > rent_max:
        raise HTTPException(status_code=422, detail="rent_min must not exceed rent_max")

    conditions = [
        sql.SQL("geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)"),
        sql.SQL("ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))"),
    ]
    params: list[object] = [
        min_lng,
        min_lat,
        max_lng,
        max_lat,
        min_lng,
        min_lat,
        max_lng,
        max_lat,
    ]

    if rent_min is not None:
        conditions.append(sql.SQL("rent >= %s"))
        params.append(rent_min)
    if rent_max is not None:
        conditions.append(sql.SQL("rent <= %s"))
        params.append(rent_max)
    if rooms is not None:
        conditions.append(sql.SQL("rooms = %s"))
        params.append(rooms)
    if property_type:
        conditions.append(sql.SQL("LOWER(property_type) = LOWER(%s)"))
        params.append(property_type.strip())

    query = sql.SQL(
        """
        SELECT id, external_id, title, rent, size_m2,
               CASE WHEN size_m2 > 0 THEN rent / size_m2 END AS eur_per_m2,
               rooms, property_type, address, listed_date,
               ST_X(geom) AS lng, ST_Y(geom) AS lat
        FROM listings
        WHERE {where_clause}
        ORDER BY id
        LIMIT %s
        """
    ).format(where_clause=sql.SQL(" AND ").join(conditions))
    params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lng"], row["lat"]]},
            "properties": {
                "id": row["id"],
                "external_id": row["external_id"],
                "title": row["title"],
                "rent": float(row["rent"]),
                "size_m2": float(row["size_m2"]) if row["size_m2"] is not None else None,
                "eur_per_m2": float(row["eur_per_m2"]) if row["eur_per_m2"] is not None else None,
                "rooms": row["rooms"],
                "property_type": row["property_type"],
                "address": row["address"],
                "listed_date": row["listed_date"].isoformat() if row["listed_date"] else None,
            },
        }
        for row in rows
    ]

    visible_prices = sorted(
        feature["properties"]["eur_per_m2"]
        for feature in features
        if feature["properties"]["eur_per_m2"] is not None
    )
    median = None
    if visible_prices:
        midpoint = len(visible_prices) // 2
        median = (
            visible_prices[midpoint]
            if len(visible_prices) % 2
            else (visible_prices[midpoint - 1] + visible_prices[midpoint]) / 2
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"count": len(features), "median_eur_per_m2": median, "limit": limit},
    }


@app.get("/areas/stats", response_model=AreaFeatureCollection)
def get_area_stats() -> dict:
    query = """
        SELECT
            a.id,
            a.name,
            COUNT(l.id)::int AS listing_count,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY l.rent)
                FILTER (WHERE l.rent IS NOT NULL) AS median_rent,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY l.rent / NULLIF(l.size_m2, 0))
                FILTER (WHERE l.rent IS NOT NULL AND l.size_m2 > 0) AS median_eur_per_m2,
            ST_AsGeoJSON(a.geom)::json AS geometry
        FROM areas a
        LEFT JOIN listings l
          ON a.geom && l.geom
         AND ST_Covers(a.geom, l.geom)
        GROUP BY a.id, a.name, a.geom
        ORDER BY a.name
    """
    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "id": row["id"],
                    "name": row["name"],
                    "listing_count": row["listing_count"],
                    "median_rent": float(row["median_rent"]) if row["median_rent"] is not None else None,
                    "median_eur_per_m2": float(row["median_eur_per_m2"])
                    if row["median_eur_per_m2"] is not None
                    else None,
                },
            }
            for row in rows
        ],
    }


@app.get("/listings/near", response_model=ListingFeatureCollection)
def get_listings_near(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    radius_m: Annotated[float, Query(gt=0, le=50000)] = 1000,
    rent_min: Annotated[float | None, Query(ge=0)] = None,
    rent_max: Annotated[float | None, Query(ge=0)] = None,
    rooms: Annotated[int | None, Query(ge=1, le=20)] = None,
    property_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
) -> dict:
    conditions = [
        sql.SQL(
            "ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)"
        )
    ]
    params: list[object] = [lng, lat, radius_m]

    if rent_min is not None:
        conditions.append(sql.SQL("rent >= %s"))
        params.append(rent_min)
    if rent_max is not None:
        conditions.append(sql.SQL("rent <= %s"))
        params.append(rent_max)
    if rooms is not None:
        conditions.append(sql.SQL("rooms = %s"))
        params.append(rooms)
    if property_type:
        conditions.append(sql.SQL("LOWER(property_type) = LOWER(%s)"))
        params.append(property_type.strip())

    query = sql.SQL(
        """
        SELECT id, external_id, title, rent, size_m2,
               CASE WHEN size_m2 > 0 THEN rent / size_m2 END AS eur_per_m2,
               rooms, property_type, address, listed_date,
               ST_X(geom) AS lng, ST_Y(geom) AS lat,
               ST_Distance(
                   geom::geography,
                   ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
               ) AS distance_m
        FROM listings
        WHERE {where_clause}
        ORDER BY distance_m
        LIMIT %s
        """
    ).format(where_clause=sql.SQL(" AND ").join(conditions))
    query_params = [lng, lat, *params, limit]

    with get_connection() as connection:
        rows = connection.execute(query, query_params).fetchall()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lng"], row["lat"]]},
            "properties": {
                "id": row["id"],
                "external_id": row["external_id"],
                "title": row["title"],
                "rent": float(row["rent"]),
                "size_m2": float(row["size_m2"]) if row["size_m2"] is not None else None,
                "eur_per_m2": float(row["eur_per_m2"]) if row["eur_per_m2"] is not None else None,
                "rooms": row["rooms"],
                "property_type": row["property_type"],
                "address": row["address"],
                "listed_date": row["listed_date"].isoformat() if row["listed_date"] else None,
                "distance_m": round(float(row["distance_m"]), 1),
            },
        }
        for row in rows
    ]
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"count": len(features), "radius_m": radius_m, "limit": limit},
    }
