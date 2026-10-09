#!/usr/bin/env python3
"""core/logger.py — SINGLE logging module (DRY). stdout + file, timestamps, levels.
Usage: from core.logger import log; log.info("...")
"""
import logging, os, sys
from logging.handlers import RotatingFileHandler

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(BASE, "logs")
os.makedirs(LOGS, exist_ok=True)

_FMT = "%(asctime)s %(levelname)-7s [%(name)s] %(message)s"

def _setup(name="hub", level=logging.INFO):
    lg = logging.getLogger(name)
    if lg.handlers:
        return lg
    lg.setLevel(level)
    # console
    c = logging.StreamHandler(sys.stdout)
    c.setFormatter(logging.Formatter(_FMT, datefmt="%H:%M:%S"))
    # file (rotating, 1MB x 3)
    f = RotatingFileHandler(os.path.join(LOGS, "app.log"), maxBytes=1_000_000, backupCount=3)
    f.setFormatter(logging.Formatter(_FMT))
    lg.addHandler(c); lg.addHandler(f)
    return lg

log = _setup()

def timeit(fn):
    """Decorator: log elapsed time (speed visibility)."""
    import time, functools
    @functools.wraps(fn)
    def w(*a, **k):
        t0 = time.time()
        try:
            r = fn(*a, **k)
            log.debug("%s took %.2fs", fn.__name__, time.time() - t0)
            return r
        except Exception as e:
            log.warning("%s FAILED in %.2fs: %s", fn.__name__, time.time() - t0, e)
            raise
    return w
