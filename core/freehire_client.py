#!/usr/bin/env python3
"""core/freehire_client.py — HTTP transport for the freehire public API (SRP).

Single responsibility: talk JSON over HTTPS, parse the `{data, meta}` / `{error}`
envelope, handle SSL + timeouts, and log every call. NO business rules (gates,
routing, dedupe) live here — those are in config/freehire.py and find/freehire_sweep.py.

Keyless: the catalogue endpoints need no auth.

Usage:
    from core.freehire_client import FreehireClient
    c = FreehireClient()
    jobs = c.search({"category": "qa", "cities": "bangalore", "sort": "posted_at"})
    one  = c.job("senior-qa-engineer-ping-identity-angpbxf2")
"""
import asyncio
import json, ssl, urllib.error, urllib.parse, urllib.request
from core.logger import log, timeit

try:
    import httpx
except ImportError:
    httpx = None


class FreehireError(RuntimeError):
    """Raised on transport / envelope / HTTP-level failures. Callers decide policy."""


class FreehireClient:
    # Timeout: 10s = comfortable for a slow public API, still fails fast on a dead
    # endpoint (was 15s; a hung host burned a whole sweep's budget). Override per call.
    def __init__(self, base="https://freehire.me/api/v1", timeout=10):
        self.base = base.rstrip("/")
        self.timeout = timeout

    # -- transport ----------------------------------------------------------
    def _ctx(self):
        """SSL context: certifi → system default → unverified (best effort, logged)."""
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
            return ctx
        except Exception as e:
            # Not fatal — the system store is tried next — but never invisible.
            log.debug("freehire_client: certifi unusable (%s); trying system CA store", e)
        try:
            return ssl.create_default_context()
        except Exception:
            log.warning("freehire_client: using unverified SSL (no certifi, no system CAs)")
            return ssl._create_unverified_context()

    @timeit
    def _get(self, path, params=None):
        url = f"{self.base}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            url += "?" + urllib.parse.urlencode(clean)
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        )
        log.debug("freehire GET %s (timeout=%ss)", url, self.timeout)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx()) as r:
                body = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read().decode("utf-8")).get("error", "")
            except Exception as inner:
                log.debug("freehire_client: error body was not JSON (%s); using e.reason", inner)
            raise FreehireError(f"HTTP {e.code} {detail or e.reason} — {url}") from e
        except Exception as e:
            raise FreehireError(f"{e.__class__.__name__}: {e} — {url}") from e

        if "error" in body:
            raise FreehireError(f"{body['error']} — {url}")
        return body

    # -- catalogue endpoints (keyless) -------------------------------------
    def search(self, params, full_descriptions=True):
        """List jobs. `full_descriptions` uses /agent/jobs/search (markdown body)."""
        path = "/agent/jobs/search" if full_descriptions else "/jobs/search"
        body = self._get(path, params)
        data = body.get("data", [])
        log.info("freehire search -> %d jobs (total=%s)", len(data), body.get("meta", {}).get("total"))
        return data

    def search_paged(self, params, pages=12, page_size=100, concurrency=12,
                     deadline=20.0, full_descriptions=True):
        """Fetch `pages` pages of 100 CONCURRENTLY. Deduped by public_slug.

        The catalogue holds 5,378 India QA postings; `search()` returns one page of
        100 (the server caps `limit`), so the sweep was reading 2% of it and
        reporting "no new roles". `offset` is the only way past the cap.

        Sequential paging would be 12 x ~1s = 12s of wall clock; one event loop
        makes it ~1-2s. `deadline` is hard: unanswered pages are abandoned and the
        caller still gets the partial set, because a usable short list now beats a
        complete one after the user has given up waiting.
        """
        path = "/agent/jobs/search" if full_descriptions else "/jobs/search"
        base = {k: v for k, v in params.items() if v not in (None, "")}
        base.pop("offset", None)
        offsets = [i * page_size for i in range(pages)]

        def urls():
            out = []
            for off in offsets:
                q = dict(base, limit=page_size, offset=off)
                out.append(f"{self.base}{path}?{urllib.parse.urlencode(q)}")
            return out

        if httpx is None:                       # no httpx: one synchronous page
            return self.search(dict(base, limit=page_size), full_descriptions)
        hx = httpx

        async def run():
            lim = hx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
            got = []
            cl = hx.AsyncClient(headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                                timeout=self.timeout, limits=lim)
            try:
                async def one(u):
                    try:
                        r = await cl.get(u)
                        if r.status_code < 400:
                            got.append(r.json().get("data") or [])
                    except Exception as e:
                        log.debug("freehire page failed: %s", e.__class__.__name__)
                await asyncio.wait([asyncio.ensure_future(one(u)) for u in urls()],
                                   timeout=max(deadline - 0.5, 0.5))
            finally:
                import contextlib
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(cl.aclose(), timeout=0.4)
            return got

        loop = asyncio.new_event_loop()
        try:
            batches = loop.run_until_complete(asyncio.wait_for(run(), timeout=deadline))
        except (asyncio.TimeoutError, RuntimeError) as e:
            log.warning("freehire search_paged hit the %.1fs deadline: %s", deadline, e)
            batches = []
        finally:
            import contextlib
            with contextlib.suppress(Exception):
                loop.close()

        seen, merged = set(), []
        for batch in batches:
            for j in batch:
                slug = j.get("public_slug")
                if slug and slug not in seen:
                    seen.add(slug)
                    merged.append(j)
        log.info("freehire search_paged -> %d unique jobs from %d page(s)", len(merged), len(batches))
        return merged

    def job(self, slug):
        body = self._get(f"/jobs/{slug}")
        return body.get("data")

    def company(self, slug):
        body = self._get(f"/companies/{slug}")
        return body.get("data")

    def facets(self, params=None):
        body = self._get("/jobs/facets", params)
        return body.get("data")
