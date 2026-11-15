"""Python-only launcher for Phase 42; does not require cmd.exe or a batch file."""
from pathlib import Path
import os
import uvicorn

if __name__ == '__main__':
    os.chdir(Path(__file__).resolve().parent)
    print('AgriORBIT Phase 42: original Phase 34 mission-control design preserved.')
    print('Original dashboard: http://127.0.0.1:8034/?force-15=1#botolan')
    print('NASA crop-season evidence: http://127.0.0.1:8034/science')
    print('Use REAL NASA mode for actual historical observations; SYNTHETIC is demonstration only.')
    uvicorn.run('app.main:app',host='127.0.0.1',port=8034,log_level='info')
