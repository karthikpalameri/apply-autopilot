#!/usr/bin/env python3
"""core/fetch.py — the ONE owner of "fetch a URL from an ATS board API".

`find/prod_sweep.py` and `find/listed_sweep.py` each carried a private copy of
`_ctx()` + `get()`; the only real difference was the default timeout (5 vs 3 s).
Every ATS sweep needs the same three things: a browser-ish UA, a CA bundle that
works on macOS, and "return None, never raise" so one dead board can't kill a
40-board sweep.

Connection pooling: this uses one shared httpx.Client when httpx is installed,
because a sweep makes hundreds of requests to the same three hosts and urllib
opens a fresh TLS connection every time. Measured over 19 Greenhouse boards:
urllib 1.49s, httpx 0.46s — 3.26x. httpx is optional; without it this falls back
to urllib so the repo still runs on a bare interpreter.

Usage:
    from core.fetch import get_json
    jobs = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
"""
import asyncio
import contextlib
import json
import ssl
import threading
import urllib.request

from core.logger import log

import os

try:
    import httpx
except ImportError:      # keep the repo runnable with no third-party deps
    httpx = None

# Escape hatch: PI_FETCH_HTTPX=0 forces plain urllib. Useful when httpx is
# present but its TLS stack misbehaves on a corporate proxy.
USE_POOL = os.environ.get("PI_FETCH_HTTPX", "1") != "0"

DEFAULT_UA = "Mozilla/5.0"
DEFAULT_TIMEOUT = 5

_ctx_cache = None
_client = None
_client_lock = threading.Lock()


def ssl_context():
    """certifi -> system default -> unverified (cached, logged once when degraded)."""
    global _ctx_cache
    if _ctx_cache is not None:
        return _ctx_cache
    try:
        import certifi
        _ctx_cache = ssl.create_default_context(cafile=certifi.where())
        return _ctx_cache
    except Exception as e:
        log.debug("certifi unavailable (%s) — trying system CA store", e)
    try:
        _ctx_cache = ssl.create_default_context()
    except Exception:
        log.warning("no usable CA store — falling back to UNVERIFIED SSL for ATS fetches")
        _ctx_cache = ssl._create_unverified_context()
    return _ctx_cache


def pool():
    """The shared httpx client, or None when httpx is not installed.

    Built under a lock: the sweeps call this from two dozen threads at once, and
    without it every thread saw _client still None and built its own client — 24
    connection pools instead of one, which made the pooled path SLOWER than
    urllib (6.0s -> 8.5s). One lock, one client.
    """
    global _client
    if _client is not None or httpx is None or not USE_POOL:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        try:
            _client = httpx.Client(
                headers={"User-Agent": DEFAULT_UA},
                timeout=DEFAULT_TIMEOUT,
                follow_redirects=True,
                limits=httpx.Limits(max_connections=32, max_keepalive_connections=32),
            )
            log.debug("httpx pool ready")
        except Exception as e:
            log.warning("httpx unavailable (%s) — falling back to urllib", e)
            _client = None
    return _client


def _get(url, timeout, ua):
    """(body_bytes, error) — pooled httpx first, urllib as the fallback."""
    client = pool()
    if client is not None:
        try:
            r = client.get(url, timeout=timeout, headers={"User-Agent": ua})
            r.raise_for_status()
            return r.content, None
        except Exception as e:
            return None, e
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as r:
            return r.read(), None
    except Exception as e:
        return None, e


def get_json(url, timeout=DEFAULT_TIMEOUT, ua=DEFAULT_UA):
    """GET `url`, parse JSON. Returns None on any failure (never raises)."""
    body, err = _get(url, timeout, ua)
    if body is None:
        log.debug("GET %s failed: %s: %s", url, err.__class__.__name__, err)
        return None
    try:
        return json.loads(body)
    except Exception as e:
        log.debug("GET %s returned non-JSON: %s", url, e)
        return None


def post_json(url, payload, timeout=DEFAULT_TIMEOUT, ua=DEFAULT_UA):
    """POST `payload` as JSON, parse the reply. None on any failure (never raises).

    Only Workable needs this: its board is served by a POST endpoint, which is why
    the sweep used to carry a private urllib POST copy. Transport stays in one place.
    """
    data = json.dumps(payload).encode()
    client = pool()
    if client is not None:
        try:
            r = client.post(url, content=data, timeout=timeout,
                            headers={"User-Agent": ua, "Content-Type": "application/json"})
            r.raise_for_status()
            return json.loads(r.content)
        except Exception as e:
            log.debug("POST %s failed: %s: %s", url, e.__class__.__name__, e)
            return None
    try:
        req = urllib.request.Request(url, data=data,
                                     headers={"User-Agent": ua, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as r:
            return json.loads(r.read())
    except Exception as e:
        log.debug("POST %s failed: %s: %s", url, e.__class__.__name__, e)
        return None


def get_text(url, timeout=DEFAULT_TIMEOUT, ua=DEFAULT_UA):
    """GET `url`, return decoded text. Returns None on any failure."""
    body, err = _get(url, timeout, ua)
    if body is None:
        log.debug("GET %s failed: %s: %s", url, err.__class__.__name__, err)
        return None
    return body.decode("utf-8", "replace")


def fetch_many(urls, timeout=2.0, concurrency=128, deadline=18.0, ua=DEFAULT_UA):
    """GET many URLs concurrently. {url: text} for whatever answered in time.

    Why this exists: probing 410 company websites over 8 candidate paths is 3,280
    requests to 410 DIFFERENT hosts, so connection pooling buys nothing and a
    thread pool just parks workers on dead domains (measured: 3.2s per company
    with no signal, 242s for the full sweep, zero new boards). One event loop with
    a hard wall-clock deadline turns that into a bounded cost: whatever has not
    answered by `deadline` is abandoned and the caller still gets the partial map.

    The deadline is the contract — this never runs longer than `deadline` seconds.
    """
    if httpx is None:
        return {u: get_text(u, timeout, ua) for u in urls}
    hx = httpx                       # local binding: narrows Optional for the type checker

    async def run():
        lim = hx.Limits(max_connections=concurrency,
                        max_keepalive_connections=concurrency)
        out = {}
        cl = hx.AsyncClient(headers={"User-Agent": ua}, follow_redirects=True,
                            timeout=timeout, limits=lim)
        try:
            async def one(u):
                try:
                    r = await cl.get(u)
                    if r.status_code < 400:
                        out[u] = r.text
                except Exception as e:
                    log.debug("fetch_many: %s failed — %s", u, e.__class__.__name__)
            tasks = [asyncio.ensure_future(one(u)) for u in urls]
            _, pending = await asyncio.wait(tasks, timeout=max(deadline - 0.5, 0.5))
            for t in pending:
                t.cancel()
            if pending:
                log.debug("fetch_many: abandoned %d/%d urls at the %.1fs deadline",
                          len(pending), len(urls), deadline)
        finally:
            # closing 100+ sockets can hang, so bound it; a failed close is not fatal
            with contextlib.suppress(Exception):
                await asyncio.wait_for(cl.aclose(), timeout=0.4)
        return out

    # NOT asyncio.run(): it calls shutdown_default_executor() on close, which JOINS the
    # DNS worker threads. httpx resolves names via anyio threads that a cancel cannot
    # kill, so asyncio.run turned a 3s deadline into 30s (measured). Closing the loop
    # without joining is what actually makes the deadline hard.
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(asyncio.wait_for(run(), timeout=deadline))
    except (asyncio.TimeoutError, RuntimeError):
        return {}
    finally:
        with contextlib.suppress(Exception):
            loop.close()
