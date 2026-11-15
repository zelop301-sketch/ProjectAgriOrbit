"""Python-only Windows launcher: does not invoke cmd.exe or any .bat file."""
from pathlib import Path
import os
import uvicorn

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    print("AgriORBIT Phase 41 — original Phase 34 premium dashboard + additive science")
    print("Open http://127.0.0.1:8034/?force-15=1#botolan")
    print("Use the NASA daily seasonal button for verified real data; synthetic rehearsal is separate.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8034, log_level="info")
