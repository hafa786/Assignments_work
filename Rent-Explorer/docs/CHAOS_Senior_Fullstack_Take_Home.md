# Full-Stack — Technical Take-Home

## "Rent Explorer" — a mini location-intelligence tool

Thanks for your time. This exercise mirrors the kind of work you'd do on our platform: turning raw property data into an interactive, location-aware view that a non-technical user can explore on a map. It's deliberately small in scope but touches the real stack — a **Python + PostGIS** backend and a **React + TypeScript** map frontend.

We care far more about how you think, structure, and make trade-offs than about polish or completeness. Please **do not gold-plate**. A smaller, clean, well-reasoned solution beats a large unfinished one.

---

## Time expectation

Aim for **one focused day (≈ 5–6 hours)**. If you run short, stop and write down what you'd do next — we treat "what I chose not to build, and why" as a positive signal, not a gap. If it's taking much longer, you're doing too much; trim scope and tell us where.

---

## What we provide

Two self-contained files (no scraping, no external data needed):

- **`listings.csv`** — ~850 synthetic rental listings across the Helsinki metro area. Columns: `listing_id, latitude, longitude, rooms, size_m2, rent_eur, property_type, listed_date`. The data is broadly clean but not perfect — a handful of rows have missing values or an out-of-area coordinate. Handle that sensibly.
- **`helsinki_areas.geojson`** — 12 polygon "areas" tiling the metro region (`area_code`, `area_name`), for aggregation and choropleth rendering.

---

## The task

Build a small full-stack app that lets a user explore the listings on a map, filter them, and see how price varies by area.

### Backend — Python + PostgreSQL/PostGIS (required)

Use **Python** (Flask or FastAPI — your choice) with **PostgreSQL + PostGIS**.

- Load the listings into a spatial table (`geometry(Point, 4326)`), and load the areas as polygons. A small loader script or migration is fine.
- Expose a REST API with at least these endpoints:
  1. **`GET /listings`** — returns listings, with support for a **bounding-box** spatial filter (map viewport: `min_lng, min_lat, max_lng, max_lat`) plus attribute filters (`rent_min/rent_max`, `rooms`, `property_type`).
  2. **`GET /areas/stats`** — for each area polygon, aggregate the listings inside it (spatial point-in-polygon join) and return **GeoJSON** with `median_rent` and `median_eur_per_m2` per area.
  3. **`GET /listings/near`** — given `lat`, `lng`, `radius_m`, return listings within that radius, sorted by distance (use a proper spatial distance, e.g. `ST_DWithin` / geography).
- Use a **spatial index (GiST)** and **parameterized queries**. Handle the messy rows without crashing.

> We use Python/Flask on the platform, so the backend must be Python — that constraint is intentional.

### Frontend — React + TypeScript (required)

Use **React + TypeScript** with a map library of your choice (Leaflet, MapLibre, react-map-gl — whatever you're comfortable with).

- Render the listings as points on a map of the Helsinki metro area.
- Render a **choropleth** layer coloring the area polygons by `median_eur_per_m2` (from `/areas/stats`), with a legend.
- Provide **filter controls** (rent range, rooms, property type) that update the map view (drive the `/listings` bbox endpoint).
- Clicking a listing shows a small popup/detail (rent, size, €/m², rooms).
- Show a small **summary panel** for the current view (e.g., count and median €/m² of the visible listings).

### Stretch goals (optional — only if time allows)

Pick whatever interests you; none are required.

- Radius search UI: click the map, show listings within X metres (wire up `/listings/near`).
- Debounced refetch of listings as the user pans/zooms the map.
- A simple "value" signal per listing (e.g., its €/m² vs. its area median).
- `docker-compose` bringing up Postgres/PostGIS + API + frontend.
- A few meaningful tests, or basic auth on the API.

---

## Deliverables

1. A **Git repository** (link) or a zip, including a **README** that covers:
   - How to run it locally (a single documented path is enough — Docker is a plus).
   - Key **decisions and trade-offs** you made, and **what you'd do with more time**.
2. A short note (a paragraph is fine) on **one non-trivial engineering decision** and the reasoning behind it.

You don't need to deploy anything. Working locally from the README is all we need.

---

## Ground rules

- Use whatever libraries, docs, and AI assistants you'd normally use — we assume modern tooling. Just be ready to explain any part of what you submit in the follow-up conversation.
- If anything is ambiguous, make a reasonable assumption and note it in the README. There's no single "correct" answer.

We'll walk through your solution together afterwards and talking through your decisions. Looking forward to seeing what you build.