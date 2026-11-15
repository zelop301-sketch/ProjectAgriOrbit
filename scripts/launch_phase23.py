"""Use port 8023 and open the Phase 23 scientific core and 15-second boot automatically."""
import socket
import threading
import time
import urllib.request
import webbrowser
import uvicorn

PORT=8023
URL=f"http://127.0.0.1:{PORT}/?force-15=1&v=phase23-permission-nasa"

def is_used():
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1",PORT)) == 0

def open_after_ready():
    for _ in range(70):
        time.sleep(0.2)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health",timeout=1) as r:
                if r.status!=200:continue
                import json
                build=json.load(r).get("build")
                if build != "phase23-permission-nasa-2.3.0":
                    print("Incorrect build on port 8023: ",build,flush=True)
                    return
                print("PHASE 23 VERIFIED - opening browser:",URL,flush=True)
                webbrowser.open(URL,new=2)
                return
        except Exception:
            continue
    print("Browser could not open automatically. Open:",URL,flush=True)

if __name__=="__main__":
    if is_used():
        print("ERROR: Port 8023 is already occupied. Stop the other server with CTRL+C.")
        print("Do not use port 8000: it may still host an older AgriORBIT release.")
        raise SystemExit(2)
    threading.Thread(target=open_after_ready,daemon=True).start()
    uvicorn.run("app.main:app",host="127.0.0.1",port=PORT,log_level="info")
