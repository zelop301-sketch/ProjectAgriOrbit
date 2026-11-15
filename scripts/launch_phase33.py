"""Deprecated launcher, kept for compatibility. Launch current Phase 34."""
from runpy import run_path
from pathlib import Path
run_path(str(Path(__file__).with_name("launch_phase34.py")),run_name="__main__")
