"""Inventory binary media; hashes support review, not rights certification."""
from pathlib import Path
import hashlib, csv
ROOT=Path(__file__).resolve().parent.parent
TARGET=ROOT/'docs'/'ASSET_REGISTER_SHA256.csv'
MEDIA={'.png','.jpg','.jpeg','.gif','.webp','.svg','.wav','.mp3','.mp4','.glb','.gltf'}
files=sorted(x for x in ROOT.rglob('*') if x.is_file() and x.suffix.lower() in MEDIA and '.venv' not in x.parts)
with TARGET.open('w',encoding='utf-8',newline='') as fh:
  out=csv.writer(fh)
  out.writerow(['file_path','sha256','size_bytes','author_or_source','rights_status','notes'])
  for file in files:
    sha=hashlib.sha256(file.read_bytes()).hexdigest()
    out.writerow([str(file.relative_to(ROOT)).replace('\\','/'),sha,file.stat().st_size,'UNVERIFIED','NEEDS_HUMAN_REVIEW','Original source, licensing and any AI generation usage must be credited before submission.'])
print(f'Wrote {TARGET} ({len(files)} assets)')
