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

## Helsinki Listings App Architecture

```



                           USER
                            │
                            ▼
                 +----------------------+
                 | React + TypeScript   |
                 |  (Frontend :3000)    |
                 +----------------------+
                            │
                            │ REST API
                            ▼
                 +----------------------+
                 | FastAPI Backend      |
                 |      (:8080)         |
                 +----------------------+
                     │       │       │
      ┌──────────────┘       │       └──────────────┐
      ▼                      ▼                      ▼
GET /listings        GET /areas/stats      GET /listings/near
(Viewport Filter)    (Area Statistics)      (Radius Search)

                     │
                     ▼
          PostgreSQL + PostGIS
          --------------------
          Listings (Points)
          Areas (Polygons)
          Spatial Indexes (GiST)
          Spatial Queries
```


## Complete System Architecture

```

                          USER
                            │
                            ▼
                 React + TypeScript
                    Leaflet Map
                         :3000
                            │
            ┌───────────────┼────────────────┐
            ▼               ▼                ▼
      /listings      /areas/stats     /listings/near
            │               │                │
            └───────────────┼────────────────┘
                            ▼
                     FastAPI Backend
                          :8080
                            │
                Parameterized SQL Queries
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
   ST_Intersects      ST_Contains         ST_DWithin
        │                   │                    │
        └───────────────────┼────────────────────┘
                            ▼
                   PostgreSQL + PostGIS
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
   Listings Table                      Areas Table
    (Spatial Points)                 (Spatial Polygons)
          │                                   │
          └──────────── GiST Indexes ─────────┘


```

## 🚀 Future Enhancements

Given more development time, the following enhancements would further improve the application's performance, scalability, security, and overall user experience.

### Performance & Scalability
- Implement server-side pagination for efficient handling of large datasets.
- Add marker clustering to improve map rendering performance.
- Introduce Redis caching for frequently executed spatial queries.
- Optimize spatial queries using materialized views and precomputed area statistics.
- Process long-running tasks asynchronously using background workers.

### Security
- Implement JWT-based authentication.
- Add Role-Based Access Control (RBAC) to secure API endpoints.

### User Experience
- Add advanced search and filtering options.
- Allow users to compare multiple listings.
- Display historical rent trends and market insights.
- Build interactive analytics dashboards.
- Enable real-time updates using WebSockets.

### GIS & Spatial Analytics
- Add a property **Value Score** by comparing each listing's €/m² against its area's median.
- Support custom polygon drawing for user-defined search areas.
- Add heatmaps and rental density visualizations.
- Integrate travel-time and isochrone analysis using public transport data.
- Continue optimizing PostGIS spatial queries for larger datasets.

### Testing & Quality Assurance
- Expand unit, integration, and end-to-end (E2E) test coverage.
- Increase API validation and error handling.
- Improve code quality with automated linting, formatting, and static analysis.

### DevOps & Cloud Deployment
- Implement a CI/CD pipeline using GitHub Actions.
- Automate testing, linting, and deployments.
- Deploy the application to Azure or AWS.
- Use Kubernetes for container orchestration and high availability.
- Add production monitoring, centralized logging, and alerting.

These enhancements would make the application more scalable, secure, and production-ready while showcasing modern full-stack development, GIS best practices, and cloud-native architecture.
### Production improvements

For a production deployment, add pagination or map clustering, database migrations with Alembic, request logging/metrics, a tile or CDN strategy, authentication if data is private, and integration tests against a disposable PostGIS database.
