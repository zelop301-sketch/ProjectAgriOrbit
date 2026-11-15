-- REFERENCE SCHEMA ONLY: not deployed or connected to Phase 21.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE farms (
    farm_id UUID PRIMARY KEY,
    created_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    consent_record TEXT,
    geom GEOMETRY(MultiPolygon,4326),
    reported_area_ha NUMERIC CHECK (reported_area_ha>0)
);
CREATE INDEX farms_geom_gix ON farms USING GIST (geom);
CREATE TABLE datasets (
    dataset_id UUID PRIMARY KEY,
    provider TEXT NOT NULL,
    product TEXT NOT NULL,
    version TEXT,
    acquisition_start TIMESTAMPTZ,
    source_url TEXT,
    data_sha256 CHAR(64),
    pixel_resolution_m REAL,
    data_kind TEXT NOT NULL CHECK (data_kind IN ('nasa_api','nasa_cached','local_measured','modeled','synthetic','user_supplied_unverified'))
);
CREATE TABLE observations (
    observation_id UUID PRIMARY KEY,
    farm_id UUID REFERENCES farms(farm_id),
    dataset_id UUID REFERENCES datasets(dataset_id),
    observed_utc TIMESTAMPTZ NOT NULL,
    variable_code TEXT NOT NULL,
    value DOUBLE PRECISION,
    unit TEXT NOT NULL,
    valid_pixel_coverage_pct REAL CHECK(valid_pixel_coverage_pct BETWEEN 0 AND 100),
    qa_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    sensor_calibration_id TEXT
);
CREATE INDEX obs_by_farm_time ON observations(farm_id,observed_utc DESC);
CREATE TABLE screening_runs (
    run_id UUID PRIMARY KEY,
    farm_id UUID REFERENCES farms(farm_id),
    created_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    method_version TEXT NOT NULL,
    data_digest CHAR(64) NOT NULL,
    input_snapshot JSONB NOT NULL,
    result_snapshot JSONB NOT NULL,
    approved_for_planting BOOLEAN NOT NULL DEFAULT FALSE
);
