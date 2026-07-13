export type ListingProperties = {
  id: number
  external_id?: string | null
  title?: string | null
  rent: number
  size_m2?: number | null
  eur_per_m2?: number | null
  rooms?: number | null
  property_type?: string | null
  address?: string | null
  listed_date?: string | null
  distance_m?: number
}

export type ListingFeature = GeoJSON.Feature<GeoJSON.Point, ListingProperties>
export type ListingCollection = GeoJSON.FeatureCollection<GeoJSON.Point, ListingProperties> & {
  meta: { count: number; median_eur_per_m2?: number | null; limit?: number }
}

export type AreaProperties = {
  id: number
  name: string
  listing_count: number
  median_rent?: number | null
  median_eur_per_m2?: number | null
}
export type AreaCollection = GeoJSON.FeatureCollection<GeoJSON.MultiPolygon | GeoJSON.Polygon, AreaProperties>
