# Phase 22 — DOST-PHIVOLCS Hazard Context: Methods and Data-Use Policy

## Scope and ethical boundaries

**Phase 22 is a research / portfolio prototype.** It does not ingest authenticated PHIVOLCS data automatically, issue government hazard certificates, create disaster alerts, forecast lahars, or guarantee that land is safe. Official hazard maps may be incomplete, revised, or spatially coarse. A lack of overlap with an *uploaded subset* only means that subset has no mapped intersection: **it is not evidence of no hazard**.

DOST-PHIVOLCS provides official Pinatubo lahar hazard material and instructions on downloading KMZ maps, and HazardHunterPH provides location-based indicative assessments. These maps are intended for preparedness and planning; they do not substitute for official site-specific advice. PHIVOLCS vector files are subject to an access/request and Data User Agreement or similar terms where applicable. Obtain and verify reuse rights before publicly republishing or sharing vector data or generated overlays.

**No copyrighted or permission-limited PHIVOLCS map is included in the ZIP.** The bundled sample polygon is FICTIONAL and not a hazard finding for Botolan. The import tool accepts locally chosen vector geometry and processes it inside the local app; the upload is not persisted as a complete source layer in the app. The API returns only polygons **clipped to the field** and a source file SHA-256 identifier; even these derived outputs require reuse permissions before publication.

## Official starting points (check latest agency advisories)

- PHIVOLCS Volcano Hazard Maps: https://www.phivolcs.dost.gov.ph/volcano-hazard/
- PHIVOLCS Map Portal: https://maps.phivolcs.dost.gov.ph/
- PHIVOLCS KMZ download instructions: https://www.phivolcs.dost.gov.ph/gisweb-download-hazard-maps-instruction/
- HazardHunterPH: https://hazardhunter.georisk.gov.ph/
- PHIVOLCS geomatics/vector-data request: https://gisweb.phivolcs.dost.gov.ph/gisweb/geomatics-services-request
- PHIVOLCS 2026 Pinatubo lahars bulletin: https://www.phivolcs.dost.gov.ph/2026-pinatubo-volcano-lahars-and-related-flooding/
- NASA POWER: https://power.larc.nasa.gov/

Some agency services may be unavailable or temporarily under maintenance. The app does **not** pretend to have loaded maps when those services cannot be accessed.

## Scientific algorithm

1. The user supplies an actual, locally validated farm polygon in RFC 7946 WGS84 longitude/latitude GeoJSON.
2. The user supplies a permitted hazard Polygon/MultiPolygon/FeatureCollection in the same geographic CRS, with explicit map title, date/edition, source URL, and permission status.
3. Inputs are screened for geometry validity; farm boundaries must be local-scale, hazard polygons cannot exceed size and vertex limits, and malformed rings or custom coordinate systems are rejected.
4. The farm centroid chooses its appropriate UTM zone. Both geometries are projected into that zone; their intersection areas and the farm area are computed in square metres and converted to hectares. This is an **indicative projected area, not a cadastral/geodetic survey**.
5. The union of intersecting features prevents double counting when hazard polygons overlap. Per-feature overlap is also shown for interpreting the source legend.
6. Intersections are projected back to WGS84 for the local geospatial SVG view. The output includes the uploaded map's SHA-256, claimed source metadata, permission warnings, overlap status, and clipped polygons.
7. Optionally retrieve a **server-side NASA POWER multi-year same-season precipitation comparison** for the farm's validated coordinates. It is explicitly historical regional climate context and cannot be used to infer future lahar occurrence, field safety, flood depth, or hazard probability.

### Provenance constraints

Even if a file URL points to a PHIVOLCS domain, the system labels its contents **USER_SUPPLIED_UNVERIFIED**. HTTPS URL and user's rights declaration are not authentication. No numerical crop-yield or soil-quality claims are computed from lahar maps. Hazard zones are displayed with the exact *legend category supplied by the source file*, not translated into invented hazard scores.

### Spatial limitations

- Farm boundary must be within one half-degree in width/height; GIS topology must be valid.
- UTM zone projection is useful for a local-scale farm but still an approximation.
- If a hazard map covers only part of a region, zero mapped overlap cannot establish absence of hazards.
- Raster-based image maps, GroundOverlay KMZ files, coordinate-system mixtures, and very large official national vector layers must be converted/clipped by an authorized GIS specialist first.
- Legal property boundaries, coastal/river dynamics, terrain subsidence, lahar channel dynamics, and source map positional accuracy are **not** validated here.

## Real-world deployment checklist

- Get landowner permission; confirm the field boundary with local technical staff.
- Seek written map-data permissions as required; record the map's original legend, edition/date, native scale, and acquisition method.
- Ask PHIVOLCS and the local DRRM office for official interpretation of mapped exposures.
- Verify NASA source metadata and quality coverage separately. Never present a NASA precipitation anomaly as a lahar forecast.
- Link hazards to the farm report as an **additional land-exposure constraint**, not crop fertility, crop yield, or automatic rover path clearance.
- Never send a rover or team member into lahar channels, unstable volcanic deposits, or restricted areas.

## API and local converter

- `GET /api/hazards/capabilities` lists exact functionality and official reference links.
- `GET /api/hazards/demo` provides a synthetic example only.
- `POST /api/hazards/screen` calculates indicative overlap with independently labeled historical climate context (if requested).
- `python scripts/convert_hazard_kmz.py "authorized_download.kmz" "local_hazard.geojson"` converts locally stored KML Polygon/Placemark geometry **without network access**. Source rights and accuracy remain the user's responsibility. The converter does **not** support KMZ GroundOverlay rasters.

## Future work (not included)

- Official PHIVOLCS agency-authenticated GIS access where a data-sharing agreement permits it.
- Quality-controlled PHIVOLCS raster/vector product ingestion with version and coordinate-system review.
- Parcel-level uncertainty calculation using map scale and position accuracy metadata.
- Secure multiple-farm cloud database with licensed restricted-data access controls.
- Local DRRM validation and official field assessment workflow.
