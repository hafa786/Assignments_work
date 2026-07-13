# Supplied dataset notes

- Source files: `data/listings.csv` and `data/helsinki_areas.geojson`
- CSV rows: 850
- Area polygons: 12
- Property types: apartment, studio, townhouse
- One listing has no rent and is skipped because rent is required.
- Missing room count or size is accepted and returned as `null`.
- One valid-coordinate listing lies north of the supplied polygon extent; it remains queryable through the API but has no area statistic assignment.
- Expected imported listing count: 849.
