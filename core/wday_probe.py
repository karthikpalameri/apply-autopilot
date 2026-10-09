#!/usr/bin/env python3
"""wday_probe.py — Workday availability probe (global outages happen; check BEFORE applying).
Usage: .venv/bin/python core/wday_probe.py [domain tenant site]  (default: walmart/mckesson/visa)"""
import json, sys, urllib.request

def probe(domain, tenant, site, search="QA"):
    try:
        import certifi, ssl
        _ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        _ctx = None
    url = f"https://{domain}/wday/cxs/{tenant}/{site}/jobs"
    body = json.dumps({"appliedFacets": {}, "limit": 1, "searchText": search}).encode()
    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=10, context=_ctx))
        return f"UP ({len(d.get('jobPostings', []))} jobs)"
    except Exception as e:
        return f"DOWN ({str(e)[:40]})"

DEFAULTS = [
    ("walmart", "walmart.wd5.myworkdayjobs.com", "Walmart", "WalmartExternal"),
    ("mckesson", "mckesson.wd5.myworkdayjobs.com", "McKesson", "McKessonExternal"),
    ("visa", "visa.wd5.myworkdayjobs.com", "Visa", "Visa"),
    ("acme-twenty-four", "acme-twenty-four.wd5.myworkdayjobs.com", "acme-twenty-four", "global"),
]

if __name__ == "__main__":
    if len(sys.argv) == 4:
        print(probe(sys.argv[1], sys.argv[2], sys.argv[3]))
    else:
        for name, d, t, s in DEFAULTS:
            print(f"{name}: {probe(d, t, s)}")
