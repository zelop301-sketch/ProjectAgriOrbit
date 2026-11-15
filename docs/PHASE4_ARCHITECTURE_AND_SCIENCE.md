# Phase 4 architecture, scientific evidence and hardware limitations

## Practical architecture

```
NASA POWER (on request) --- server-validated historical climate ---> crop comparison
NASA CMR (on request) ----- granule titles + timestamps only -----> source metadata panel
Farmer inputs -----------------------------------------------> farm profile / scenario engine
Hypothetical management/weather assumptions ---> 3-zone counterfactual screening ---> 3D scene colors
Deterministic simulator ---> structural + payload + diagnostic JSON ---> Canvas3D rover & HUD
Optional telemetry packet, validated/tagged by API ---> local SQLite audit (not proof of calibration)
```

`app/main.py` owns API routing, `app/climate.py` the NASA POWER service, `app/scoring.py` scenario scoring, `app/assessment.py` historical seasonal context, `app/environment.py` counterfactuals, `app/earth_catalog.py` NASA CMR granule metadata, `app/mission.py` rover simulation and telemetry, `web/rover3d.js` the projected 3D renderer, `web/mission-ui.js` UI-to-API bridge and `web/app.js` the existing dashboard/calibration.

## NASA data source truth

- NASA POWER daily point API documentation: https://power.larc.nasa.gov/docs/services/api/temporal/daily/ . NASA POWER is a gridded, time series climate context, not high-resolution soil data. Existing Phase 2 logic displays source/units/dates and handles cached and synthetic modes differently.
- NASA MODIS vegetation indices product family: https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/science-domain/vegetation-indices/ . MODIS NDVI and EVI are quality-controlled composites, often at coarser resolution than small farm plots. CMR lookup is metadata-only. Before rendering values: acquire authentic granules, unpack arrays, apply QA masks, georeference fields, track acquisition time and plot pixel coverage, inspect cloud artifacts and data gaps.
- USGS/NASA Landsat Collection 2 surface reflectance: https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance . Landsat pixels need radiometric scaling, QA and georeferencing. This phase lists the source but does not ingest it.
- NASA ECOSTRESS products: https://ecostress.jpl.nasa.gov/data . ECOSTRESS L3 ET products require real pixel retrieval, scene coverage/temporal validation and clouds/QA. Metadata listing alone is not ET or drought estimation.

## Quantitative boundaries

The simulated farm world uses an arbitrary local x/y/z grid. Heights are smooth math functions for display only. Soil bands are illustrations, not measured horizons. The three-zone exposure index uses intentionally simple arithmetic on a rainfall multiplier, management intensity and an illustrative scenario factor. No actual field soil hydraulic parameters, ET curves, crop calendars, nutrient measurements, aquifer model, surveyed slope, channel hydraulics or empirical coefficients were supplied. The color bands (green lower exposure, yellow moderate, red critical) **must never be interpreted as measured/observed crop health**.

NDVI in the rover panel is a synthetic numeric proxy, **not derived from sensor bands or satellite imagery**. The atmosphere, soil compaction and telemetry values are simulated and have no physical calibration. The displayed `u/v` route is not a coordinate path, geofenced control route, obstacle map or safety plan. No rover movement commands exist in the API.

## Security and safety

The `AGRIORBIT_SENSOR_TOKEN` environment variable, if configured, gates `field_measured` telemetry **declarations**; it is not secure instrument attestation. The storage does not certify instrument calibration, location, identity or accuracy. No autonomous control is enabled. Before real hardware, implement isolated control system, keyed authorization, interlocks, geofence, obstacle checks, emergency stop, human approval, sensor checks and supervised safe-zone trials. Do not test in lahar channels or unstable ground.

## Acceptance verification

- Browser renders the projected 3D field canvas rather than a static image.
- Scenario, environment, lighting, camera, timeline and engineering layer controls visibly change the renderer/HUD.
- NASA POWER data is never silently upgraded from synthetic to measured.
- CMR granule metadata is never represented as image pixels.
- All hypothetical water-management results are labeled and lack crop-yield/profit promises.
- Sensor inputs are marked by source type and no route claims real GNSS/LIDAR.
- Windows batch launcher sets its working directory to the extracted folder.

## Upgrading with genuine imagery later

1. Obtain an approved farm polygon and consent. Require coordinate reference system and polygon validation.
2. Choose one NASA product per scientific question and retrieve date-specific pixels from its provider with credentials if needed.
3. Persist origin, grant/access metadata, product short name/version, quality flags, resolution, cloud coverage, acquisition time, pixel footprints and processing steps.
4. Resample only when justified, flag field/pixel spatial mismatch, mask bad pixels, and show unknown zones rather than fabricating values.
5. Compare validated ground observations only when variables/units, time, depth and spatial support match. NASA POWER air temperature and rain cannot calibrate a soil pH probe.
6. Get local agronomic review before making crop or irrigation recommendations.
