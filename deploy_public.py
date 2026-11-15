"""Safe public-demo ASGI entrypoint for AgriORBIT Phase 42.

Preserves the original FastAPI routes and every 3D/dashboard asset.
On public hosting, disable unauthenticated writes to SQLite records that
were designed for a single local machine, not a multi-tenant website.
"""
import os
from fastapi import Request
from fastapi.responses import JSONResponse
from app.main import app

@app.middleware('http')
async def public_demo_protection(request: Request, call_next):
    if os.getenv('AGRIORBIT_PUBLIC_DEMO', '0') == '1':
        path = request.url.path
        if ((request.method == 'POST' and path in {'/api/science/evidence', '/api/mission/telemetry'})
            or (request.method == 'GET' and path.startswith('/api/science/evidence/'))):
            return JSONResponse(status_code=403, content={
                'detail': 'Local evidence and telemetry storage is disabled on the public demo. '
                          'The NASA science page can still export its evidence as a local JSON download.'
            })
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response
