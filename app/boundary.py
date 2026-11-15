"""Geographic area sanity check for farmer-entered small farm polygons.

Approximates area using a local equirectangular projection; not a survey and
not a replacement for geodesic/cadastral geometry validation.
"""
from __future__ import annotations

import math
from pydantic import BaseModel, Field


class BoundaryRequest(BaseModel):
    geometry: dict
    reported_area_ha: float = Field(gt=0, le=100000)
    farm_latitude: float = Field(ge=-90, le=90)
    farm_longitude: float = Field(ge=-180, le=180)


def check_boundary(request: BoundaryRequest) -> dict:
    geo = request.geometry
    if geo.get("type") == "Feature":
        geo = geo.get("geometry") or {}
    if geo.get("type") != "Polygon":
        raise ValueError("Expected a GeoJSON Polygon or Feature (Polygon only).")
    rings = geo.get("coordinates")
    if not isinstance(rings, list) or len(rings) != 1:
        raise ValueError("Exactly one exterior ring is supported; holes are not supported.")
    points = rings[0]
    if not isinstance(points, list) or not 4 <= len(points) <= 501:
        raise ValueError("Boundary must have 4–501 coordinate positions.")
    try:
        xy = [(float(p[0]), float(p[1])) for p in points]
    except (IndexError, TypeError, ValueError) as exc:
        raise ValueError("Invalid point; coordinates must be [longitude, latitude].") from exc
    if not all(math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90 for lon, lat in xy):
        raise ValueError("Coordinates must be finite WGS84 degrees.")
    if xy[0] != xy[-1]:
        raise ValueError("GeoJSON ring must close (first point = last point).")
    xs = [p[0] for p in xy]
    ys = [p[1] for p in xy]
    if max(xs)-min(xs) >= 1 or max(ys)-min(ys) >= 1:
        raise ValueError("Only local farm-scale polygons under one degree per axis are supported.")
    avg_lat = sum(ys[:-1]) / (len(ys)-1)
    x_factor = 111320 * math.cos(math.radians(avg_lat))
    y_factor = 110574
    projected = [(lon*x_factor, lat*y_factor) for lon, lat in xy]
    area_m2 = abs(sum(projected[i][0]*projected[i+1][1] - projected[i+1][0]*projected[i][1]
                      for i in range(len(projected)-1)) / 2)
    if area_m2 < 1:
        raise ValueError("Polygon has zero or implausibly small mapped area.")
    area_ha = area_m2 / 10000
    difference = 100*(area_ha/request.reported_area_ha - 1)
    inside_bounds = min(xs) <= request.farm_longitude <= max(xs) and min(ys) <= request.farm_latitude <= max(ys)
    flags = []
    if abs(difference) > 25:
        flags.append("Reported field area differs from approximate polygon area by more than 25%.")
    if not inside_bounds:
        flags.append("Farm point lies outside the polygon bounding box; check coordinates.")
    return {"source_type": "user_supplied_geometry", "geometry_validated": True,
            "surveyed": False, "area_method": "Local equirectangular approximate area, not a geodesic survey",
            "approximate_area_ha": round(area_ha, 3),
            "reported_area_ha": request.reported_area_ha,
            "difference_pct": round(difference, 1), "farm_point_inside_bounding_box": inside_bounds,
            "flags": flags,
            "warning": "This rough geometry check does not establish legal boundaries, positional accuracy, ground elevation, or exact area."}
