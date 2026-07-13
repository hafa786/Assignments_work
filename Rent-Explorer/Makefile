DATABASE_URL ?= postgresql://postgres:postgres@localhost:5432/listings

up:
	docker compose up --build -d

load:
	docker compose run --rm api python scripts/load_data.py \
		--database-url postgresql://postgres:postgres@db:5432/listings \
		--listings /data/listings.csv --areas /data/areas.geojson

logs:
	docker compose logs -f api frontend

down:
	docker compose down

reset:
	docker compose down -v
