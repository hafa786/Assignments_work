import { useMapEvents } from 'react-leaflet';
import type { LatLngBounds } from 'leaflet';

export function MapEvents({
  onBoundsChanged,
}: {
  onBoundsChanged: (bounds: LatLngBounds) => void;
}) {
  useMapEvents({
    moveend: (event) => onBoundsChanged(event.target.getBounds()),
    zoomend: (event) => onBoundsChanged(event.target.getBounds()),
  });
  return null;
}
