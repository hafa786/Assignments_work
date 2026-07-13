# Helsinki Rental Explorer

A small full-stack spatial application for exploring rental listings around the Helsinki metro area, filtering the visible listings, and comparing median price per square metre by area.

## Stack

- **API:** Python 3.12, FastAPI, psycopg 3
- **Database:** PostgreSQL 16 + PostGIS
- **Frontend:** React, TypeScript, Vite, React Leaflet
- **Runtime:** Docker Compose

## Included requirements

- Listings stored as `geometry(Point, 4326)`
- Areas stored as `geometry(MultiPolygon, 4326)`
- GiST indexes for geometry and geography radius lookups
- Parameterized SQL through psycopg
- Bounding-box and attribute filters on `GET /listings`
- Point-in-polygon aggregation on `GET /areas/stats`
- Accurate metre-based search using `ST_DWithin(...::geography)` on `GET /listings/near`
- Loader that skips malformed rows instead of terminating the import
- React map with points, choropleth, legend, popups, filters, viewport summary, and debounced refetching

## Run

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:3001/docs`
- Backend health: `http://localhost:8080/health`

Docker Compose idempotently applies the PostGIS schema on every startup, then automatically imports the supplied `listings.csv` and `helsinki_areas.geojson` before starting the API. The loader skips the row with missing rent and safely keeps optional missing size/room values.


## Ports

- Frontend: `http://localhost:3000`
- API documentation proxy: `http://localhost:3001/docs`
- Backend REST API: `http://localhost:8080`
- PostgreSQL is internal to Docker Compose and is not exposed on the host, avoiding local port conflicts.

## Database recovery

The `db-init` service applies `schema.sql` on every startup, not only when the volume is first created. This fixes common errors caused by reusing an older Docker volume with missing tables, columns, PostGIS extensions, or indexes. To fully reset local data, run `docker compose down -v` and then `docker compose up --build`.

## API examples

### Listings in viewport

```bash
curl 'http://localhost:8080/listings?min_lng=24.7&min_lat=60.1&max_lng=25.2&max_lat=60.3&rent_max=1500&rooms=2&property_type=apartment'
```

### Area statistics

```bash
curl 'http://localhost:8080/areas/stats'
```

### Listings within 1 km

```bash
curl 'http://localhost:8080/listings/near?lat=60.1699&lng=24.9384&radius_m=1000'
```

## Data format

`data/listings.csv` accepts these canonical fields:

```text
listing_id,latitude,longitude,rooms,size_m2,rent_eur,property_type,listed_date
```

The loader supports the supplied `rent_eur`, `listing_id`, `latitude`, `longitude`, and `listed_date` columns, plus common aliases such as `rent`, `monthly_rent`, `id`, `lat`, `lng`, and `type`.

`data/helsinki_areas.geojson` must be a GeoJSON FeatureCollection containing Polygon or MultiPolygon features. Area names may be supplied as `name`, `nimi`, `NAME`, or `area_name`.

## Tests

From the backend directory:

```bash
pip install -r requirements.txt
pytest
```

## Design notes

- `geom && envelope` allows PostgreSQL to use the GiST index before the exact `ST_Intersects` test.
- `ST_Covers` includes points on polygon boundaries, unlike a strict `ST_Contains` operation.
- The expression geography index supports metre-based radius queries without storing a second spatial column.
- Median values use PostgreSQL `percentile_cont(0.5)`.
- The API caps response sizes to protect the service. For a larger production dataset, add clustering or vector tiles.


## Future Enhancements

Given more time, I would extend the application with several production-ready features. These include server-side pagination and clustering to improve map performance with larger datasets, Redis caching for frequently requested spatial queries, JWT-based authentication and role-based access control, comprehensive unit and integration tests, and a CI/CD pipeline using GitHub Actions. I would also enhance the user experience by adding advanced search filters, listing comparison, historical rent trends, interactive analytics dashboards, and real-time updates using WebSockets. From a GIS perspective, I would optimize spatial queries further with materialized views and precomputed area statistics, while improving scalability through asynchronous background jobs, monitoring, logging, and deployment to a cloud platform such as Azure or AWS with Kubernetes for high availability.

### Production improvements

For a production deployment, add pagination or map clustering, database migrations with Alembic, request logging/metrics, a tile or CDN strategy, authentication if data is private, and integration tests against a disposable PostGIS database.
