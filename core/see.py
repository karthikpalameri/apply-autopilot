#!/usr/bin/env python3
"""see.py — screenshot + OCR vision. Usage: see.py [name] — prints OCR text (~3s)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ctl import call as ctl  # single owner (:9000 socket) — DRY
from core.ocr import read as ocr   # single owner (tesseract)

name = sys.argv[1] if len(sys.argv) > 1 else "view"
ctl({"op": "snap", "name": name, "full": False})
print(ocr(f"logs/{name}.png")[:2500])
