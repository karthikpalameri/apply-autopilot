#!/usr/bin/env python3
"""find/ats_resolve.py — fill the `ats`/`ats_slug` fields in product_companies.json.

435 of the 500 companies had no board, so prod_sweep/listed_sweep could never see
them. Discovery and the two identity gates now live in **core/ats_boards.py**
(single owner); this file is only the CLI + writer that persists what it finds.

Why the careers page matters: guessing a slug from the company NAME missed every
company whose slug is not its name. Razorpay's Greenhouse slug is
`razorpaysoftwareprivatelimited`, BrowserStack is not on Greenhouse at all (Workday
`browserstack.wd3`). Reading the company's own careers page recovers both.

Usage:
  .venv/bin/python find/ats_resolve.py --report        # what is still missing
  .venv/bin/python find/ats_resolve.py --dry-run CRED Groww Slice
  .venv/bin/python find/ats_resolve.py --limit 50      # resolve 50, writing as it goes
  .venv/bin/python find/ats_resolve.py --all
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core.ats_boards import BOARDS, SCANNABLE, candidates, probe_websites, verify  # noqa: E402
from core.logger import log  # noqa: E402

DATA = os.path.join(ROOT, "config", "data", "product_companies.json")
COMPANY_WORKERS = 8
PROBE_DEADLINE = 15.0   # seconds for the whole careers-page batch, hard cap


def resolve(company, website="", known=None):
    """(provider, slug) when both gates pass, else None.

    `known` is the (provider, slug) pair already discovered from `website`'s careers
    page by probe_websites, so a batch pays for the HTML fetch once instead of once
    per company.
    """
    cands = (known or []) + candidates(company, "")
    scannable = [(p, s) for p, s in cands if p in SCANNABLE]
    seen, uniq = set(), []
    for pair in scannable:
        if pair not in seen:
            seen.add(pair)
            uniq.append(pair)
    with ThreadPoolExecutor(max_workers=min(16, max(1, len(uniq)))) as ex:
        futs = {ex.submit(verify, p, s): (p, s) for p, s in uniq}
        for fut in as_completed(futs):
            provider, slug = futs[fut]
            try:
                ok, _, reason = fut.result()
            except Exception as e:
                log.debug("%s: %s/%s failed — %s", company, provider, slug, e)
                continue
            if ok:
                log.info("%s -> %s/%s: %s", company, provider, slug, reason)
                return provider, slug
            log.debug("%s: %s/%s rejected — %s", company, provider, slug, reason)
    return None


def load():
    return json.load(open(DATA))


def save(companies):
    tmp = DATA + ".tmp"
    with open(tmp, "w") as f:
        json.dump(companies, f, indent=1)
    os.replace(tmp, DATA)   # atomic: an interrupt never leaves a half-written data file


def _parse_args(argv):
    """Split flags from company names. --limit takes a value, so it must not be
    mistaken for a company name (asking for `--limit 50` used to try to resolve a
    company literally called "50")."""
    opts = {"dry": "--dry-run" in argv, "all": "--all" in argv,
            "report": "--report" in argv, "limit": 50}
    names, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--limit":
            i += 1
            opts["limit"] = int(argv[i]) if i < len(argv) else 50
        elif not a.startswith("--"):
            names.append(a)
        i += 1
    return opts, names


def _targets(opts, names, companies, unresolved):
    """Pick which companies to work on: named, --all, or the first --limit."""
    if not names:
        return unresolved if opts["all"] else unresolved[:opts["limit"]]
    want = {n.lower() for n in names}
    for m in sorted(want - {c["company"].lower() for c in companies}):
        print(f"  not in product_companies.json: {m}")
    return [c for c in companies if c["company"].lower() in want]


def _resolve_batch(targets, companies, dry):
    """Probe careers pages once for the whole batch, then verify candidate boards."""
    hits, done, t0 = 0, 0, time.time()
    discovered = probe_websites([(c["company"], c.get("website", "")) for c in targets],
                                timeout=2.0, deadline=PROBE_DEADLINE)
    print(f"  careers probe: {len(discovered)}/{len(targets)} sites showed an ATS embed"
          f"  ({time.time() - t0:.1f}s)", flush=True)
    with ThreadPoolExecutor(max_workers=COMPANY_WORKERS) as ex:
        futures = {ex.submit(resolve, c["company"], c.get("website", ""),
                             discovered.get(c["company"])): c for c in targets}
        for fut in as_completed(futures):
            c = futures[fut]
            done += 1
            try:
                got = fut.result()
            except Exception as e:
                log.warning("%s: resolve failed — %s", c["company"], e)
                got = None
            if got:
                hits += 1
                c["ats"], c["ats_slug"] = got
                c["status"] = "ats-resolved"
                if not dry:
                    save(companies)
            if done % 25 == 0:
                print(f"  {done}/{len(targets)}  hits={hits}  "
                      f"{done / max(time.time() - t0, 0.001):.1f} co/s", flush=True)
    return hits, time.time() - t0


def main():
    opts, names = _parse_args(sys.argv[1:])
    dry = opts["dry"]
    companies = load()
    unresolved = [c for c in companies if not (c.get("ats") or "").strip()]
    if opts["report"]:
        print(f"{len(companies)} companies | {len(companies) - len(unresolved)} with slug "
              f"| {len(unresolved)} unsweepable")
        for c in unresolved[:30]:
            print(f"  {c['company']:32s} {c.get('website', '')}")
        if len(unresolved) > 30:
            print(f"  ... and {len(unresolved) - 30} more")
        return
    targets = _targets(opts, names, companies, unresolved)
    if not targets:
        print("nothing to resolve")
        return
    print(f"resolving {len(targets)} company(ies){' [DRY RUN — no writes]' if dry else ''}", flush=True)
    hits, elapsed = _resolve_batch(targets, companies, dry)
    print(f"resolved {hits}/{len(targets)} in {elapsed:.1f}s"
          f"{' [DRY RUN — nothing written]' if dry else ''}")
    if not dry and hits:
        total = len(companies)
        have = sum(1 for c in companies if (c.get("ats_slug") or "").strip())
        print(f"coverage now {have}/{total} ({have / total:.1%})  providers: "
              f"{ {p: sum(1 for c in companies if c.get('ats') == p) for p in BOARDS} }")


if __name__ == "__main__":
    main()
