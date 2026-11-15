# Phase 21 — Scalable architecture and production checklist

## Implemented

* FastAPI Pydantic request validation and endpoint contracts.
* Historical NASA POWER fetch with bounded concurrent requests, cache and raw-payload hashes.
* SQLite/WAL **opt-in** evidence snapshots with immutable SHA-256 and UUID references.
* Local, no-build HTML/CSS/JavaScript client with mobile layout.
* Offline batch HLS raster worker script that avoids live raster computation in the dashboard request path.

## NOT implemented — production priorities

1. **Authorization and privacy.** OIDC login, least-privilege roles, audit logs, data encryption, retention/consent policies, secret management, and secure public hosting; current API binds to localhost only and is **not** cloud-safe.
2. **Geospatial database.** Replace SQLite with PostgreSQL/PostGIS; retain field polygons with SRID 4326; store provenance-linked observations and QA records (example schema under `deploy/postgis_schema.sql`). Use topology checks, proper geodesic area and farm permissions.
3. **Raster object store.** Store original HLS GeoTIFFs and derivations in versioned object storage, with CMR IDs, data license, checksum and retrieval log. Enforce data-level controls and prohibit synthetic imagery masquerading as real.
4. **Async workers.** Move CMR discovery and heavy pixel processing to a durable queue with retry/backoff, idempotent jobs, per-provider rate limits and monitoring.
5. **Scientific reproducibility.** Version crop rule sets, validation data, units, QA thresholds, processing functions and field-review signoffs. Require controlled QA before promoting a research model to decision support.
6. **Field sensors.** Authenticate device messages, verify sensor calibration ID, spatial matching, timestamp, sample depth and quality limits. Separate real rover control into an authorized safety-controller service.
7. **Observability.** API health/error tracing, benchmark fetch failures, cache effectiveness, percent valid HLS pixels, rate limits, database backups, data freshness SLAs. Never promise sub-second remote-sensing downloads.

The included SQL is a schema design/reference only; it is **not deployed** or connected to the FastAPI app.
