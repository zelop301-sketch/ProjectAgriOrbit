"""Download *real* historical NASA POWER data using the Phase 23 server-side client.
Fail loudly when unavailable. Never save a synthetic response as NASA evidence.
"""
import argparse,asyncio,json,sys
from pathlib import Path
from app.phase23_integrations import nasa_observation_receipt

def main():
    parser=argparse.ArgumentParser(description='NASA POWER verified-source annual evidence fetch')
    parser.add_argument('--lat',type=float,default=15.289,help='Latitude WGS84; default is UNSURVEYED Botolan-area illustration')
    parser.add_argument('--lon',type=float,default=120.024,help='Longitude WGS84; default is UNSURVEYED Botolan-area illustration')
    parser.add_argument('--year',type=int,default=2025)
    parser.add_argument('--refresh',action='store_true')
    args=parser.parse_args()
    if not (-90<=args.lat<=90 and -180<=args.lon<=180 and 1981<=args.year<=2025):
        parser.error('Coordinates or historical year out of range')
    try:
        payload=asyncio.run(nasa_observation_receipt(args.lat,args.lon,args.year,refresh=args.refresh,include_daily=True))
    except Exception as exc:
        print(f'NO NASA EVIDENCE SAVED: {exc}',file=sys.stderr)
        return 2
    if payload.get('data_class')!='historical_nasa':
        print('NO NASA EVIDENCE SAVED: unexpected data class',file=sys.stderr)
        return 2
    dest=Path('reports');dest.mkdir(exist_ok=True)
    out=dest/f'nasa_power_{args.year}_{args.lat:.5f}_{args.lon:.5f}.json'
    out.write_text(json.dumps(payload,indent=2),encoding='utf8')
    print('NASA POWER actual API/cache evidence:',out)
    print('Source:',payload['metadata']['source_type'])
    print('Retrieved at:',payload['metadata']['retrieved_at'])
    print('SHA256:',payload['metadata']['raw_payload_sha256'])
    print('Quality:',payload['annual_quality_gate'])
    return 0
if __name__=='__main__':raise SystemExit(main())
