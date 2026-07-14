import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CircleMarker, GeoJSON, MapContainer, Popup, TileLayer } from 'react-leaflet';
import type { LatLngBounds, PathOptions } from 'leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './styles.css';
import { MapEvents } from './components/MapEvents';
import type { AreaCollection, AreaProperties, ListingCollection } from './types/geo';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8080';
const initialBounds = L.latLngBounds([60.145, 24.63], [60.31, 25.13]);

type Filters = { rentMin: string; rentMax: string; rooms: string; propertyType: string };

function colorFor(value: number | null | undefined): string {
  if (value == null) return '#d8dee9';
  if (value < 16) return '#edf8e9';
  if (value < 20) return '#bae4b3';
  if (value < 24) return '#74c476';
  if (value < 28) return '#31a354';
  return '#006d2c';
}

function App() {
  const [bounds, setBounds] = useState<LatLngBounds>(initialBounds);
  const [filters, setFilters] = useState<Filters>({
    rentMin: '',
    rentMax: '',
    rooms: '',
    propertyType: '',
  });
  const [listings, setListings] = useState<ListingCollection>({
    type: 'FeatureCollection',
    features: [],
    meta: { count: 0 },
  });
  const [areas, setAreas] = useState<AreaCollection>({ type: 'FeatureCollection', features: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    fetch(`${API_URL}/areas/stats`)
      .then((response) => {
        if (!response.ok) throw new Error('Could not load area statistics');
        return response.json();
      })
      .then(setAreas)
      .catch((err: Error) => setError(err.message));
  }, []);

  const fetchListings = useCallback(async (nextBounds: LatLngBounds, nextFilters: Filters) => {
    const params = new URLSearchParams({
      min_lng: String(nextBounds.getWest()),
      min_lat: String(nextBounds.getSouth()),
      max_lng: String(nextBounds.getEast()),
      max_lat: String(nextBounds.getNorth()),
    });
    if (nextFilters.rentMin) params.set('rent_min', nextFilters.rentMin);
    if (nextFilters.rentMax) params.set('rent_max', nextFilters.rentMax);
    if (nextFilters.rooms) params.set('rooms', nextFilters.rooms);
    if (nextFilters.propertyType) params.set('property_type', nextFilters.propertyType);

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/listings?${params}`);
      if (!response.ok) throw new Error(`Listings request failed (${response.status})`);
      setListings(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected request error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => fetchListings(bounds, filters), 300);
    return () => window.clearTimeout(debounceRef.current);
  }, [bounds, filters, fetchListings]);

  const onBoundsChanged = useCallback((nextBounds: LatLngBounds) => setBounds(nextBounds), []);

  const areaStyle = useCallback((feature?: GeoJSON.Feature): PathOptions => {
    const props = feature?.properties as AreaProperties | undefined;
    return {
      fillColor: colorFor(props?.median_eur_per_m2),
      fillOpacity: 0.48,
      color: '#455a64',
      weight: 1,
    };
  }, []);

  const areaLayer = useMemo(
    () => (
      <GeoJSON
        key={JSON.stringify(areas.features.map((feature) => feature.properties?.median_eur_per_m2))}
        data={areas}
        style={areaStyle}
        onEachFeature={(feature, layer) => {
          const props = feature.properties as AreaProperties;
          layer.bindTooltip(
            `<strong>${props.name}</strong><br/>Listings: ${props.listing_count}<br/>Median: ${
              props.median_eur_per_m2 == null
                ? 'No data'
                : `€${props.median_eur_per_m2.toFixed(2)}/m²`
            }`,
          );
        }}
      />
    ),
    [areas, areaStyle],
  );

  return (
    <div className="app-shell">
      <header>
        <div>
          <p className="eyebrow">Spatial rental intelligence</p>
          <h1>Helsinki Rental Explorer</h1>
        </div>
        <div className="status">
          {loading ? 'Updating map…' : `${listings.meta.count} visible listings`}
        </div>
      </header>

      <aside className="filters panel">
        <h2>Filters</h2>
        <label>
          Minimum rent (€)
          <input
            type="number"
            min="0"
            value={filters.rentMin}
            onChange={(e) => setFilters({ ...filters, rentMin: e.target.value })}
          />
        </label>
        <label>
          Maximum rent (€)
          <input
            type="number"
            min="0"
            value={filters.rentMax}
            onChange={(e) => setFilters({ ...filters, rentMax: e.target.value })}
          />
        </label>
        <label>
          Rooms
          <select
            value={filters.rooms}
            onChange={(e) => setFilters({ ...filters, rooms: e.target.value })}
          >
            <option value="">Any</option>
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          Property type
          <select
            value={filters.propertyType}
            onChange={(e) => setFilters({ ...filters, propertyType: e.target.value })}
          >
            <option value="">Any</option>
            <option>apartment</option>
            <option>studio</option>
            <option>townhouse</option>
          </select>
        </label>
        <button
          onClick={() => setFilters({ rentMin: '', rentMax: '', rooms: '', propertyType: '' })}
        >
          Clear filters
        </button>
      </aside>

      <main>
        {error && <div className="error-banner">{error}</div>}
        <MapContainer bounds={initialBounds} className="map" zoomControl>
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {areaLayer}
          {listings.features.map((feature) => {
            const [lng, lat] = feature.geometry.coordinates;
            const p = feature.properties;
            return (
              <CircleMarker
                key={p.id}
                center={[lat, lng]}
                radius={6}
                pathOptions={{ fillOpacity: 0.85, weight: 1 }}
              >
                <Popup>
                  <div className="popup">
                    <strong>{p.title || p.address || `Listing ${p.id}`}</strong>
                    <span>Rent: €{p.rent.toFixed(0)}/month</span>
                    <span>Size: {p.size_m2 ? `${p.size_m2.toFixed(1)} m²` : 'Unknown'}</span>
                    <span>
                      Price: {p.eur_per_m2 ? `€${p.eur_per_m2.toFixed(2)}/m²` : 'Unknown'}
                    </span>
                    <span>Rooms: {p.rooms ?? 'Unknown'}</span>
                    <span>Type: {p.property_type ?? 'Unknown'}</span>
                    <span>Listed: {p.listed_date ?? 'Unknown'}</span>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
          <MapEvents onBoundsChanged={onBoundsChanged} />
        </MapContainer>

        <section className="summary panel">
          <h2>Current view</h2>
          <div>
            <strong>{listings.meta.count}</strong>
            <span>Listings</span>
          </div>
          <div>
            <strong>
              {listings.meta.median_eur_per_m2 == null
                ? '—'
                : `€${listings.meta.median_eur_per_m2.toFixed(2)}`}
            </strong>
            <span>Median €/m²</span>
          </div>
        </section>

        <section className="legend panel">
          <h2>Median €/m²</h2>
          {[
            ['< 16', 14],
            ['16–20', 18],
            ['20–24', 22],
            ['24–28', 26],
            ['28+', 30],
          ].map(([label, value]) => (
            <div className="legend-row" key={String(label)}>
              <span style={{ background: colorFor(Number(value)) }} />
              {label}
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}

export default App;
