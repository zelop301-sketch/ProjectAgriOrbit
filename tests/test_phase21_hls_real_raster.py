"""Local GeoTIFF I/O test only: synthetic pixels, NEVER NASA imagery."""
import json
from pathlib import Path
import pytest

def test_local_raster_pipeline_with_cloud_mask_and_polygon(tmp_path):
    rasterio=pytest.importorskip('rasterio')
    np=pytest.importorskip('numpy')
    from rasterio.transform import from_origin
    from scripts.hls_field_ndvi import analyze
    shape=(8,8)
    transform=from_origin(120.0200,15.2808,0.0001,0.0001)
    red=np.ones(shape,dtype='int16')*1000
    nir=np.ones(shape,dtype='int16')*3000
    mask=np.zeros(shape,dtype='uint8')
    mask[0,0]=2  # cloud bit 1
    mask[0,1]=32 # water bit 5
    paths=[]
    for name,arr in [('red',red),('nir',nir),('fmask',mask)]:
        path=tmp_path/f'{name}.tif'
        with rasterio.open(path,'w',driver='GTiff',width=8,height=8,count=1,dtype=str(arr.dtype),crs='EPSG:4326',transform=transform,nodata=255 if name=='fmask' else -9999) as dst:
            dst.write(arr,1)
        paths.append(path)
    polygon={'type':'Polygon','coordinates':[[[120.02005,15.28005],[120.02075,15.28005],[120.02075,15.28075],[120.02005,15.28075],[120.02005,15.28005]]]}
    bound=tmp_path/'field.geojson';bound.write_text(json.dumps(polygon))
    d=analyze(paths[0],paths[1],paths[2],bound,granule_id='SYNTHETIC_TEST_NOT_NASA',observation_date='2025-06-01')
    assert d['clear_valid_pixels']>=10
    assert d['ndvi_median']==.5
    assert d['data_class']=='processed_user_supplied_rasters_unverified_source'
    assert d['field_statistic_usable']
    assert len(d['source_files_sha256']['red'])==64
    assert d['raster_crs']=='EPSG:4326'
