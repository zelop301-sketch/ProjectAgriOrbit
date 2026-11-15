"""Phase 4 mission visualization / telemetry API.

Never equate a synthetic 3D landscape with surveyed terrain or a
simulated rover sample with a physical sensor observation. Live rover
actuation is intentionally out of scope.
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from .scoring import Farm, compare

DEFAULT_DB = Path(__file__).resolve().parent.parent / '.cache' / 'mission_samples.sqlite3'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class SensorSample(BaseModel):
    """Explicit provenance contract for measurements vs simulation."""
    device_id: str = Field(default='agro-sentinel-sim-01', min_length=2, max_length=70)
    metric: Literal['soil_moisture_relative', 'soil_temperature', 'air_temperature', 'battery_voltage']
    value: float = Field(ge=-1000, le=1000, allow_inf_nan=False)
    unit: Literal['%', '°C', 'V']
    source_type: Literal['simulated', 'field_measured'] = 'simulated'
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    calibration_reference: str | None = Field(default=None, max_length=120)
    sensor_model: str | None = Field(default=None, max_length=120)
    depth_cm: float | None = Field(default=None, ge=0, le=200)
    notes: str = Field(default='', max_length=500)

    @model_validator(mode='after')
    def validate_sensor(self):
        required = {
            'soil_moisture_relative': '%', 'soil_temperature': '°C',
            'air_temperature': '°C', 'battery_voltage': 'V'
        }
        if self.unit != required[self.metric]:
            raise ValueError('Unit incompatible with metric')
        if self.metric == 'soil_moisture_relative' and not 0 <= self.value <= 100:
            raise ValueError('Relative soil moisture must be 0–100%')
        if self.source_type == 'field_measured' and not all((self.calibration_reference, self.sensor_model, self.latitude is not None, self.longitude is not None)):
            raise ValueError('Measured readings require calibration reference, sensor model, and coordinates')
        if self.timestamp.tzinfo is None:
            raise ValueError('Telemetry timestamp must include a timezone')
        if self.timestamp.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError('Telemetry timestamp cannot be in the future')
        return self


def db_path():
    return Path(os.environ.get('AGRIORBIT_TELEMETRY_DB', str(DEFAULT_DB)))


def persist_sample(sample: SensorSample):
    """Append local audit event, preserving both source_type and calibration metadata."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS samples (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          inserted_utc TEXT NOT NULL,
          source_type TEXT NOT NULL,
          metric TEXT NOT NULL,
          payload TEXT NOT NULL
        )''')
        conn.execute('INSERT INTO samples(inserted_utc,source_type,metric,payload) VALUES(?,?,?,?)',
                     (utc_now(), sample.source_type, sample.metric, sample.model_dump_json()))
        conn.commit()


def latest_samples(limit: int = 12):
    path = db_path()
    if not path.exists():
        return []
    with sqlite3.connect(path) as conn:
        rows = conn.execute('SELECT payload FROM samples ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [json.loads(row[0]) for row in rows]


# Presentation-only normalized field locations. These are not GNSS coordinates.
ROVER_WAYPOINTS = [
    {'id': 'BASE', 'u': 0.13, 'v': 0.78, 'task': 'mission standby'},
    {'id': 'P-01', 'u': 0.29, 'v': 0.64, 'task': 'conceptual soil-probe scan'},
    {'id': 'P-02', 'u': 0.61, 'v': 0.56, 'task': 'conceptual crop-imaging scan'},
    {'id': 'P-03', 'u': 0.78, 'v': 0.30, 'task': 'conceptual atmospheric scan'},
    {'id': 'RETURN', 'u': 0.13, 'v': 0.78, 'task': 'return to simulation base'},
]

ROVER_COMPONENTS = [
    {'id': 'chassis', 'label': '4-wheel all-terrain chassis', 'state': 'concept', 'notes': 'Parametric illustration only; track and suspension design not mechanically validated'},
    {'id': 'battery', 'label': 'Battery / solar assist', 'state': 'concept', 'notes': 'No verified cell chemistry, electrical budget or solar efficiency'},
    {'id': 'camera', 'label': 'Multispectral + hyperspectral camera payload', 'state': 'proposed', 'notes': 'Band calibration, radiometry, NDVI computation and optics absent'},
    {'id': 'probe', 'label': 'Compaction / moisture / temperature probe', 'state': 'proposed', 'notes': 'Soil calibration and probe insertion mechanism not verified'},
    {'id': 'atmosphere', 'label': 'CO2 / humidity / air temperature pod', 'state': 'proposed', 'notes': 'Requires verified instrument specification and span/zero calibration'},
    {'id': 'lidar', 'label': 'LIDAR navigation', 'state': 'proposed', 'notes': 'Grid simulation is not a certified safety or obstacle-detection system'},
]


def rover_model() -> dict:
    return {
        'model_id': 'agro-sentinel-parametric-visual-v0.4',
        'representation': 'CAD_STYLE_PROCEDURAL_3D',
        'source_type': 'simulated',
        'dimensional_accuracy': 'unverified',
        'hardware_connected': False,
        'autonomous_control': 'disabled',
        'components': ROVER_COMPONENTS,
        'layers': [
            {'id': 'structural', 'name': 'Structural / CAD-style', 'data_quality': 'concept geometry'},
            {'id': 'diagnostic', 'name': 'Diagnostic heatmaps', 'data_quality': 'simulated faults/temperatures'},
            {'id': 'navigation', 'name': 'LIDAR navigation grid', 'data_quality': 'synthetic occupancy raster and illustrative waypoints'},
        ],
        'safety': 'NO commands to actuators or physical vehicle. Do not use synthetic route for autonomous driving.',
    }


def mission_plan(farm: Farm) -> dict:
    return {
        'id': 'agro-sentinel-demo-route-v2',
        'source_type': 'simulated',
        'autonomy': 'disabled',
        'hardware_connection': False,
        'safety_state': 'SIMULATOR_ONLY',
        'farm_name': farm.name,
        'coordinates': {'latitude': farm.latitude, 'longitude': farm.longitude, 'source_type': 'farmer_entered'},
        'waypoints': ROVER_WAYPOINTS,
        'spatial_note': 'Waypoint u,v values are normalized presentation-board coordinates; not surveyed GPS, no LIDAR geometry and no safe physical route.',
        'design_note': 'Concept four-wheel vehicle with camera pod, solar panel and soil probe; dimensions and load/collision behavior not verified.',
    }


def rover_step(progress: float) -> dict:
    """Deterministic test telemetry, suitable for UI animation only."""
    if not 0 <= progress <= 1 or not math.isfinite(progress):
        raise ValueError('progress must be within [0, 1]')
    route = ROVER_WAYPOINTS
    pos = progress * (len(route) - 1)
    idx = min(int(pos), len(route) - 2)
    alpha = min(1.0, pos - idx)
    a, b = route[idx], route[idx + 1]
    u = round(a['u'] + (b['u'] - a['u']) * alpha, 5)
    v = round(a['v'] + (b['v'] - a['v']) * alpha, 5)
    moisture = round(41 + 8 * math.sin(progress * math.pi * 2.4), 1)
    soil_temp = round(27.4 + 1.9 * math.cos(progress * math.pi * 2), 1)
    motor_temp = round(35.3 + 11.2 * (0.5 + 0.5 * math.sin(progress * math.pi * 3.4)), 1)
    wheel_slip = round(3.2 + 9 * (0.5 + 0.5 * math.sin(progress * math.pi * 4.2)), 1)
    dust = round(10 + 28 * progress, 1)
    battery = round(92 - 22 * progress, 1)
    solar = round(32 + 18 * math.sin(progress * math.pi), 1)
    ndvi = round(0.51 + 0.11 * math.sin(progress * math.pi * 2.3), 3)
    co2 = round(418 + 12 * math.sin(progress * math.pi * 2.1), 1)
    air_temp = round(29.5 + 0.9 * math.sin(progress * math.pi * 2), 1)
    humidity = round(73 + 7 * math.cos(progress * math.pi * 2), 1)
    compaction = round(980 + 180 * math.cos(progress * math.pi * 2.7), 0)
    return {
        'source_type': 'simulated', 'hardware_connected': False,
        'autonomy': 'disabled', 'mission_phase': idx + 1,
        'phase_name': b['task'], 'waypoint': b['id'], 'progress_pct': round(progress * 100, 1),
        'position': {'u': u, 'v': v, 'unit': 'normalized visualization coordinates'},
        'structural': {
            'battery_percent': {'value': battery, 'unit': '%', 'source_type': 'simulated'},
            'solar_assist_percent': {'value': solar, 'unit': '%', 'source_type': 'simulated'},
            'suspension_load_index': {'value': round(0.4 + .2 * math.sin(progress * 7), 3), 'unit': 'arbitrary', 'source_type': 'simulated'},
        },
        'diagnostics': {
            'wheel_slip_pct': {'value': wheel_slip, 'unit': '%', 'source_type': 'simulated'},
            'motor_temp_c': {'value': motor_temp, 'unit': '°C', 'source_type': 'simulated'},
            'lens_dust_pct': {'value': dust, 'unit': '%', 'source_type': 'simulated'},
        },
        'payload': {
            'soil_moisture_relative': {'value': moisture, 'unit': '%', 'source_type': 'simulated'},
            'soil_temperature': {'value': soil_temp, 'unit': '°C', 'source_type': 'simulated'},
            'soil_compaction_proxy': {'value': compaction, 'unit': 'kPa (synthetic)', 'source_type': 'simulated'},
            'ndvi_proxy': {'value': ndvi, 'unit': 'unitless (synthetic)', 'source_type': 'simulated'},
            'co2': {'value': co2, 'unit': 'ppm (synthetic)', 'source_type': 'simulated'},
            'humidity': {'value': humidity, 'unit': '%', 'source_type': 'simulated'},
            'air_temperature': {'value': air_temp, 'unit': '°C', 'source_type': 'simulated'},
            'hyperspectral': {'value': None, 'unit': None, 'source_type': 'planned', 'note': 'No spectral cube or spectral bands available'},
        },
        'navigation': {
            'source_type': 'simulated', 'lidar_connected': False, 'path_validated': False,
            'grid_resolution': '8×8 schematic',
            'occupancy': [
                [1 if (r, c) in {(2, 6), (3, 6), (5, 2), (6, 2)} else 0 for c in range(8)]
                for r in range(8)
            ],
        },
        'telemetry': [
            {'metric': 'soil_moisture_relative', 'value': moisture, 'unit': '%', 'source_type': 'simulated', 'calibration_reference': None},
            {'metric': 'soil_temperature', 'value': soil_temp, 'unit': '°C', 'source_type': 'simulated', 'calibration_reference': None},
            {'metric': 'battery_voltage', 'value': round(12.5 - 0.65 * progress, 2), 'unit': 'V', 'source_type': 'simulated', 'calibration_reference': None},
        ],
        'timestamp': utc_now(),
        'warning': 'All values, NDVI/compaction estimates, path, diagnostic heatmaps and positions are synthetic; no physical rover or sensor was contacted.',
    }


def farm_scene(farm: Farm, scenario: Literal['A', 'B', 'C'] = 'B') -> dict:
    result = compare(farm)
    chosen = next(x for x in result['scenarios'] if x['id'] == scenario)
    return {
        'field': {'name': farm.name, 'latitude': farm.latitude, 'longitude': farm.longitude,
                  'area_ha_user_reported': farm.area_ha, 'coordinate_source': 'farmer_entered'},
        'visualization': {
            'type': 'PROCEDURAL_3D_DEMONSTRATION', 'source_type': 'simulated',
            'terrain': 'Synthetic gently undulating grid; not NASA elevation, measured slope or a DEM',
            'zones': 'Design illustration only; plot colors are not crop suitability, actual NDVI or yield',
            'boundary': 'Illustrative rectangle, not a cadastral survey or site-safe path',
        },
        'selected_scenario': {'id': chosen['id'], 'title': chosen['title'], 'sequence': chosen['crops'],
                              'heuristic_score': chosen['score'], 'score_kind': 'UNVALIDATED_HEURISTIC'},
        'route': mission_plan(farm),
        'rover_model': rover_model(),
    }


def diagnostics():
    return {
        'build': 'phase4-holographic-rover-integration', 'checked_at_utc': utc_now(),
        'subsystems': [
            {'name': 'fastapi', 'status': 'online', 'verified': True},
            {'name': 'nasa_power', 'status': 'not_checked', 'verified': False, 'note': 'Fetch historical NASA data explicitly in climate panel'},
            {'name': 'soil_sensors', 'status': 'not_connected', 'verified': False},
            {'name': 'rover_actuators', 'status': 'disabled', 'verified': False},
            {'name': 'rover_simulator', 'status': 'available', 'verified': True},
            {'name': '3d_renderer', 'status': 'client_side_canvas3d', 'verified': False, 'note': 'Only client-side WebGL feature detection verifies browser readiness'},
            {'name': 'lidar', 'status': 'simulation_only', 'verified': False},
            {'name': 'multispectral_hyperspectral', 'status': 'planned', 'verified': False},
        ],
        'latency_note': 'Sub-second rendering and telemetry updates are performance goals, not a server guarantee.',
        'interoperability_note': 'NASA POWER gridded climate cannot calibrate a local soil sensor; compare only compatible variables, units, time windows and locations.',
    }
