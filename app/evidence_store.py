"""Small-project persistent evidence index. SQLite/WAL, not a PostGIS replacement.

Retention is explicit: only user-requested reports are stored. Do not put
secrets or precise field identities into the public evidence store.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

DB_FILE=Path(os.environ.get('AGRIORBIT_EVIDENCE_DB', Path(__file__).resolve().parents[1]/'.cache'/'evidence.sqlite3'))

def _connect():
    DB_FILE.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(DB_FILE, timeout=5)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, created_utc TEXT NOT NULL, source_kind TEXT NOT NULL, sha256 TEXT NOT NULL, data TEXT NOT NULL)')
    conn.commit()
    return conn

def save_report(report:dict, source_kind:str):
    canonical=json.dumps(report,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    digest=hashlib.sha256(canonical.encode()).hexdigest()
    record_id=str(uuid4())
    timestamp=datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute('INSERT INTO reports VALUES (?,?,?,?,?)',(record_id,timestamp,source_kind,digest,canonical))
    return {'id':record_id,'created_utc':timestamp,'sha256':digest,'source_kind':source_kind,
            'note':'Saved locally on the machine running this application; not uploaded to NASA.'}

def read_report(record_id:str):
    with _connect() as conn:
        row=conn.execute('SELECT id,created_utc,source_kind,sha256,data FROM reports WHERE id=?',(record_id,)).fetchone()
    return None if row is None else dict(id=row[0],created_utc=row[1],source_kind=row[2],sha256=row[3],report=json.loads(row[4]))
