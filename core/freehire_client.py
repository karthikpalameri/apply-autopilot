#!/usr/bin/env python3
"""core/freehire_client.py — HTTP transport for the freehire public API (SRP).

Single responsibility: talk JSON over HTTPS, parse the `{data, meta}` / `{error}`
envelope, handle SSL + timeouts, and log every call. NO business rules (gates,
routing, dedupe) live here — those are in config/freehire.py and find/freehire_sweep.py.

Keyless: the catalogue endpoints need no auth. Works with stdlib only (no requests
required); prefers certifi when present, and degrades to unverified TLS if the
system CA bundle is missing (common on fresh machines).

Usage:
    from core.freehire_client import FreehireClient
    c = FreehireClient()
    jobs = c.search({"category": "qa", "cities": "bangalore", "sort": "posted_at"})
    one  = c.job("senior-qa-engineer-example-abc123")
"""
import json, ssl, urllib.error, urllib.parse, urllib.request
from core.logger import log, timeit


class FreehireError(RuntimeError):
    """Raised on transport / envelope / HTTP-level failures. Callers decide policy."""


class FreehireClient:
    def __init__(self, base="https://freehire.me/api/v1", timeout=15):
        self.base = base.rstrip("/")
        self.timeout = timeout

    # -- transport ----------------------------------------------------------
    def _ctx(self, unverified=False):
        if unverified:
            return ssl._create_unverified_context()
        try:
            import certifi
            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            pass
        try:
            return ssl.create_default_context()
        except Exception:
            log.warning("freehire_client: no SSL context available, using unverified TLS")
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

        def _open(ctx):
            return urllib.request.urlopen(req, timeout=self.timeout, context=ctx)

        try:
            with _open(self._ctx()) as r:
                body = json.loads(r.read().decode("utf-8"))
        except (ssl.SSLError, urllib.error.URLError) as e:
            if "certificate verify failed" in str(e) or "CERTIFICATE_VERIFY_FAILED" in str(e):
                log.warning("freehire_client: cert verify failed, retrying unverified TLS")
                try:
                    with _open(ssl._create_unverified_context()) as r:
                        body = json.loads(r.read().decode("utf-8"))
                except urllib.error.HTTPError as he:
                    raise FreehireError(f"HTTP {he.code} — {url}")
                except Exception as e2:
                    raise FreehireError(f"{e2.__class__.__name__}: {e2} — {url}")
            else:
                raise FreehireError(f"{e.__class__.__name__}: {e} — {url}")
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read().decode("utf-8")).get("error", "")
            except Exception:
                pass
            raise FreehireError(f"HTTP {e.code} {detail or e.reason} — {url}")
        except Exception as e:
            raise FreehireError(f"{e.__class__.__name__}: {e} — {url}")

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

    def job(self, slug):
        return self._get(f"/jobs/{slug}").get("data")

    def company(self, slug):
        return self._get(f"/companies/{slug}").get("data")

    def facets(self, params=None):
        return self._get("/jobs/facets", params).get("data")
