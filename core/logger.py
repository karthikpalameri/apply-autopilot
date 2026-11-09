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
    # console -> stderr (stdout stays clean for program data / --json output)
    c = logging.StreamHandler(sys.stderr)
    c.setFormatter(logging.Formatter(_FMT, datefmt="%H:%M:%S"))
    # file (rotating, 1MB x 3)
    f = RotatingFileHandler(os.path.join(LOGS, "app.log"), maxBytes=1_000_000, backupCount=3)
    f.setFormatter(logging.Formatter(_FMT))
    lg.addHandler(c); lg.addHandler(f)
    return lg

log = _setup()


def say(msg="", level=logging.INFO):
    """Console-facing status line that ALSO reaches logs/app.log.

    Scripts used bare print() for progress and results, so nothing they did ever
    landed in the log file — the only evidence of a real submission was a
    screenshot. say() keeps the exact stdout formatting (so CLI tables and dry-run
    plans look the same) while routing a timestamped copy to the rotating log.
    """
    print(msg)
    log.log(level, "%s", msg)


def warn(msg=""):
    say(msg, level=logging.WARNING)


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
