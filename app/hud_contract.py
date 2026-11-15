"""Truthful capabilities for the local Phase 5 HUD. Does not certify external hardware."""


def hud_capabilities():
    return {
        "build": "phase5-hud-0.5.0",
        "render_engine": "browser_canvas2d_projected_3d",
        "shader_pipeline": "CPU_color_interpolation_and_CSS_overlays",
        "hardware_acceleration_verified": False,
        "realtime_latency_guarantee": False,
        "visualization_layers": {
            "structural": "concept_geometry",
            "diagnostic": "simulated",
            "navigation": "synthetic_lidar_waypoints",
            "field_thermal": "synthetic_not_ecostress",
            "canopy_density": "synthetic_not_satellite_ndvi",
            "day_night": "illustrative_not_ephemeris",
            "water_exposure": "experimental_unvalidated",
        },
        "integrations": {
            "nasa_power": "manual_historical_point_fetch",
            "modis": "catalog_metadata_only",
            "landsat": "not_ingested",
            "ecostress": "catalog_metadata_only",
            "rover_lidar": "not_connected",
            "rover_camera": "not_connected",
            "browser_camera": "opt_in_local_only",
        },
        "physical_rover_commands_enabled": False,
        "augmented_reality_registration": False,
        "data_notice": "Farm heatmaps, canopy, thermal colors, rover readings, waypoint animations and solar shadows are illustrative. No quantitative raster pixels were ingested.",
    }
