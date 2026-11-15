"""LOCAL-ONLY KML/KMZ polygon conversion for authorized PHIVOLCS map assets.

This is a best-effort format converter, not a GIS authority or agency certificate.
File licensing, accuracy, legend classes, and CRS must be verified separately.
No network fetches, no KML ground overlays/raster conversion, no archive extraction.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

MAX_KML = 5_000_000
MAX_KMZ = 10_000_000


def kml_coords(s):
    output=[]
    for part in (s or '').strip().split():
        comps=part.split(',')
        if len(comps)<2:
            raise ValueError('KML coordinates must contain longitude,latitude.')
        lon,lat=float(comps[0]),float(comps[1])
        if not -180<=lon<=180 or not -90<=lat<=90:
            raise ValueError('KML coordinates out of WGS84 bounds.')
        output.append([lon,lat])
    if len(output)<3:
        raise ValueError('Polygon has fewer than 3 positions.')
    if output[0]!=output[-1]:output.append(output[0])
    return output


def convert_kml(kml_bytes):
    if len(kml_bytes)>MAX_KML or b'<!DOCTYPE' in kml_bytes.upper() or b'<!ENTITY' in kml_bytes.upper():
        raise ValueError('KML is too large or contains prohibited XML declarations.')
    root=ET.fromstring(kml_bytes)
    ns={'k':'http://www.opengis.net/kml/2.2'}
    features=[]
    for placemark in root.findall('.//k:Placemark',ns):
        name=placemark.findtext('k:name',default='Unclassified map zone',namespaces=ns)
        for pg in placemark.findall('.//k:Polygon',ns):
            outer=pg.find('k:outerBoundaryIs/k:LinearRing/k:coordinates',ns)
            if outer is None:continue
            rings=[kml_coords(outer.text)]
            for inner in pg.findall('k:innerBoundaryIs/k:LinearRing/k:coordinates',ns):
                rings.append(kml_coords(inner.text))
            features.append({'type':'Feature','geometry':{'type':'Polygon','coordinates':rings},
                             'properties':{'name':name[:100],'imported_from':'local KMZ/KML, unverified'}})
            if len(features)>100:
                raise ValueError('Too many polygons. Clip the local map to the pilot area first.')
    if not features:
        raise ValueError('No KML Polygon features found. Raster or GroundOverlay KMZ is not supported.')
    return {'type':'FeatureCollection','features':features}


def convert_file(input_path:Path)->dict:
    if input_path.stat().st_size>MAX_KMZ:
        raise ValueError('Input exceeds 10 MB limit.')
    if input_path.suffix.lower()=='.kmz':
        with zipfile.ZipFile(input_path) as z:
            entries=[e for e in z.infolist() if not e.is_dir() and e.filename.lower().endswith('.kml')]
            if not entries:raise ValueError('KMZ contains no KML file.')
            entry=entries[0]
            if entry.file_size>MAX_KML:raise ValueError('KML payload exceeds size limit.')
            with z.open(entry) as fh:
                data=fh.read(MAX_KML+1)
    elif input_path.suffix.lower()=='.kml':
        data=input_path.read_bytes()
    else:raise ValueError('Expected a local .kml or .kmz file.')
    return convert_kml(data)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Convert authorized local KML/KMZ polygon features to GeoJSON.')
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    data=convert_file(args.input)
    args.output.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(f'Local conversion complete ({len(data["features"])} features). User must verify PHIVOLCS permissions and hazard legend. No official source authenticity is asserted.')
