CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS areas (
    id BIGSERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    name TEXT NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS listings (
    id BIGSERIAL PRIMARY KEY,
    external_id TEXT UNIQUE,
    title TEXT,
    rent NUMERIC(12, 2),
    size_m2 NUMERIC(10, 2),
    rooms INTEGER,
    property_type TEXT,
    address TEXT,
    listed_date DATE,
    geom geometry(Point, 4326),
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Idempotent upgrades for databases created by older versions of the app.
ALTER TABLE areas ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE areas ADD COLUMN IF NOT EXISTS name TEXT;
ALTER TABLE areas ADD COLUMN IF NOT EXISTS geom geometry(MultiPolygon, 4326);

ALTER TABLE listings ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS rent NUMERIC(12, 2);
ALTER TABLE listings ADD COLUMN IF NOT EXISTS size_m2 NUMERIC(10, 2);
ALTER TABLE listings ADD COLUMN IF NOT EXISTS rooms INTEGER;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS property_type TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS listed_date DATE;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
ALTER TABLE listings ADD COLUMN IF NOT EXISTS raw_data JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS idx_areas_external_id_unique ON areas (external_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_listings_external_id_unique ON listings (external_id);
CREATE INDEX IF NOT EXISTS idx_areas_geom_gist ON areas USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_listings_geom_gist ON listings USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_listings_geography_gist ON listings USING GIST ((geom::geography));
CREATE INDEX IF NOT EXISTS idx_listings_filters ON listings (rent, rooms, property_type);
