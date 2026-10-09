"""core/console.py — cross-platform UTF-8 console setup.

On Windows the default console codec is often `cp1252`, which raises
`UnicodeEncodeError` the moment a script prints an emoji or box-drawing glyph
(e.g. "✅", "⚠️", "→"). Call `enable_utf8()` once at the start of any entry point
that prints non-ASCII so the same code runs cleanly on macOS / Linux / Windows.
"""
import sys


def enable_utf8():
    """Reconfigure stdout/stderr to UTF-8 with replacement (never raises)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def propagate_utf8_env():
    """Export PYTHONUTF8=1 so child processes (subprocesses) also use UTF-8."""
    import os
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
