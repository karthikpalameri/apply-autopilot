#!/usr/bin/env python3
"""core/ocr.py — the ONE owner of "read text out of a screenshot".

Three scripts called `tesseract` directly, each with a different flag set and a
different failure story:

  core/hard_assert.py  caught it and printed "OCR unavailable"   (fine)
  core/see.py          crashed with a raw FileNotFoundError      (traceback to the user)
  core/verify.py       `except Exception: "(ocr fail)"`          (invisible)

On a machine without tesseract — which this repo's own INSTALL.md lists as a
prerequisite, and which was NOT installed when this was written — that meant one
script crashed, one lied quietly, and one behaved.

Perf note, measured on a real page: the screenshot itself costs 79 ms on the ctl
transport and 440 ms on the MCP transport. OCR adds ~200-400 ms on top. If a
script only needs to know "did the confirmation text appear", read the DOM — it
is ~1 ms — and keep OCR for what DOM cannot see (canvas, images, rendering bugs).
"""
import os
import shutil
import subprocess

from core.logger import log

DEFAULT_TIMEOUT = 15
_available = None


def available():
    """True when a `tesseract` binary is on PATH. Checked once, then cached."""
    global _available
    if _available is None:
        _available = shutil.which("tesseract") is not None
        if not _available:
            log.warning("tesseract not installed — OCR text will be empty. "
                        "Install it with: brew install tesseract")
    return _available


def read(png_path, psm=6, timeout=DEFAULT_TIMEOUT):
    """Return the text in `png_path`, or "" when OCR is unavailable or fails.

    Never raises: callers treat "" as "no OCR text" and fall back to the DOM.
    """
    if not available():
        return ""
    if not os.path.exists(png_path):
        log.warning("OCR skipped: %s does not exist", png_path)
        return ""
    try:
        r = subprocess.run(["tesseract", png_path, "-", "--psm", str(psm)],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log.warning("OCR timed out after %ss on %s", timeout, png_path)
        return ""
    except Exception as e:
        log.error("OCR failed on %s: %s: %s", png_path, e.__class__.__name__, e)
        return ""
    if r.returncode != 0:
        log.warning("OCR exited %s on %s: %s", r.returncode, png_path, (r.stderr or "").strip()[:200])
        return ""
    return r.stdout or ""
