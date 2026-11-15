"""Optional NASA HLS v2 local COG processing, read only.

Run on COGs downloaded from NASA Earthdata. The user supplies the red,
NIR and Fmask bands from ONE matching HLS granule; raster filenames and
NASA authenticity are not independently verified by this CLI.

Requires optional `pip install rasterio numpy` on supported Python versions.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def calculate_ndvi(red, nir, fmask, inside, *, nodata=-9999):
    import numpy as np
    if red.shape != nir.shape or red.shape != fmask.shape or red.shape != inside.shape:
        raise ValueError('All arrays must have equal shape')
    r=np.asarray(red, dtype='float64')
    n=np.asarray(nir, dtype='float64')
    qa=np.asarray(fmask, dtype='uint8')
    footprint=inside.astype(bool)
    qa_bad=(qa & sum(1<<i for i in (1,2,3,4,5))) != 0
    valid=footprint & ~qa_bad & np.isfinite(r) & np.isfinite(n)
    valid &= (r != nodata) & (n != nodata) & (r >= 0) & (n >= 0)
    valid &= ((r+n) > 0)
    n_valid=int(valid.sum()); n_total=int(footprint.sum())
    fraction=round(100*n_valid/n_total,1) if n_total else 0.0
    ndvi=(n[valid]-r[valid])/(n[valid]+r[valid]) if n_valid else np.asarray([])
    summary={'field_pixels_total':n_total, 'clear_valid_pixels':n_valid,
             'valid_pixel_coverage_pct':fraction,
             'cloud_or_invalid_pixels':max(0,n_total-n_valid),
             'ndvi_median':round(float(np.median(ndvi)),4) if n_valid else None,
             'ndvi_mean':round(float(ndvi.mean()),4) if n_valid else None,
             'ndvi_min':round(float(ndvi.min()),4) if n_valid else None,
             'ndvi_max':round(float(ndvi.max()),4) if n_valid else None,
             'field_statistic_usable':n_valid>=10 and fraction>=60,
             'note':'NDVI is a vegetation greenness indicator, NOT a direct crop diagnosis or soil-moisture measurement. 10 clear 30 m pixels and 60% valid coverage are conservative prototype thresholds, not mission-specified QA requirements.'}
    return summary


def analyze(red_path, nir_path, fmask_path, boundary_path, *, granule_id:str, observation_date:str) -> dict:
    try:
        import numpy as np
        import rasterio
        from rasterio.features import geometry_mask
        from rasterio.warp import transform_geom
    except ImportError as exc:
        raise RuntimeError('Optional dependencies missing: pip install rasterio numpy (use compatible Python version).') from exc
    geometry=json.loads(Path(boundary_path).read_text(encoding='utf-8'))
    if geometry.get('type') == 'Feature': geometry=geometry['geometry']
    if geometry.get('type') not in ('Polygon', 'MultiPolygon'):
        raise ValueError('Expected GeoJSON Polygon or MultiPolygon; input CRS must be EPSG:4326')
    with rasterio.open(red_path) as src, rasterio.open(nir_path) as nirs, rasterio.open(fmask_path) as qa:
        if not src.crs or src.crs != nirs.crs or src.crs != qa.crs or src.transform != nirs.transform or src.transform != qa.transform or src.shape != nirs.shape or src.shape != qa.shape:
            raise ValueError('Red, NIR and Fmask must be co-registered: CRS, shape and pixel transform identical')
        if src.width*src.height > 20_000_000:
            raise ValueError('Raster too large for local MVP. Subset COGs first to avoid excess memory.')
        field_geom=transform_geom('EPSG:4326',src.crs.to_string(),geometry,precision=8)
        inside=geometry_mask([field_geom], out_shape=src.shape, transform=src.transform, invert=True)
        # Three co-registered HLS reflectance bands with 0.0001 scale; ratio cancels scale factor.
        result=calculate_ndvi(src.read(1), nirs.read(1), qa.read(1), inside, nodata=src.nodata if src.nodata is not None else -9999)
        result['raster_pixel_size_m']=tuple(round(abs(v),2) for v in src.res)
        result['raster_crs']=src.crs.to_string()
    result.update({'product':'NASA HLS v2 (user-supplied local COG bands)',
       'data_class':'processed_user_supplied_rasters_unverified_source',
       'granule_id_user_supplied':granule_id, 'observation_date_user_supplied':observation_date,
       'analysis_timestamp_utc':datetime.now(timezone.utc).isoformat(),
       'source_files_sha256':{tag:hashlib.sha256(Path(path).read_bytes()).hexdigest() for tag,path in [('red',red_path),('nir',nir_path),('fmask',fmask_path)]},
       'qa_mask':'HLS v2 Fmask bits 1,2,3,4,5: cloud, cloud adjacency, shadow, snow, water excluded',
       'field_boundary_source':'user-supplied GeoJSON EPSG:4326; not a cadastral survey',
       'warning':'File identity and Earthdata provenance cannot be proven by filename. Require NASA granule link, observation timestamp, exact band mapping and local crop context before interpreting NDVI.',
       'reference':'https://hls.gsfc.nasa.gov/data-access-and-tools/'})
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--red', required=True,help='HLS L30 B4 or HLS S30 B4 raster')
    parser.add_argument('--nir', required=True,help='HLS L30 B5 or S30 B8A raster')
    parser.add_argument('--fmask',required=True,help='Matching HLS Fmask raster')
    parser.add_argument('--boundary', required=True,help='WGS84 GeoJSON Polygon')
    parser.add_argument('--granule',required=True,help='NASA HLS granule ID for audit')
    parser.add_argument('--date',required=True,help='Observation date YYYY-MM-DD')
    parser.add_argument('--out',required=True,help='Output JSON file')
    args=parser.parse_args()
    report=analyze(args.red,args.nir,args.fmask,args.boundary,granule_id=args.granule,observation_date=args.date)
    Path(args.out).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'out':args.out,'valid_pixel_coverage_pct':report['valid_pixel_coverage_pct'],'field_statistic_usable':report['field_statistic_usable']},indent=2))
