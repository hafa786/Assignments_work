from typing import Any, Literal

from pydantic import BaseModel, Field


class ListingProperties(BaseModel):
    id: int
    external_id: str | None = None
    title: str | None = None
    rent: float
    size_m2: float | None = None
    eur_per_m2: float | None = None
    rooms: int | None = None
    property_type: str | None = None
    address: str | None = None
    listed_date: str | None = None
    distance_m: float | None = None


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(min_length=2, max_length=2)


class ListingFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: ListingProperties


class ListingFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[ListingFeature]
    meta: dict[str, Any]


class AreaFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict[str, Any]]
