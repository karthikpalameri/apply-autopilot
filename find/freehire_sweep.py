#!/usr/bin/env python3
"""find/freehire_sweep.py — discover QA/SDET roles via freehire (orchestration).

ADDITIVE source — sits alongside prod_sweep.py / listed_sweep.py / sweep.py.
Thin use-case layer over core/freehire_client.py (transport) and
config/freehire.py (filters/gates/routing). Logs to logs/app.log via core.logger.

Usage:
    .venv/bin/python find/freehire_sweep.py              # Bangalore QA/SDET, strict gate
    .venv/bin/python find/freehire_sweep.py india        # India-wide QA/SDET
    .venv/bin/python find/freehire_sweep.py --all        # full annotated pool
    .venv/bin/python find/freehire_sweep.py --strict     # product companies only
    .venv/bin/python find/freehire_sweep.py --json       # machine-readable (agents)
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import log, timeit
from core.freehire_client import FreehireClient, FreehireError
from core import applied_ledger as _ledger
from config.freehire import (
    QA, NON, ROUTING, UNKNOWN_ROUTE,
    GATE_COMPANY_TYPES, FRESH_CLASSES,
    build_search_params,
)


# ---------------------------------------------------------------------------
# Dedupe — DELEGATED to core/applied_ledger.py (single source, append-only).
# Matching rules (company suffixes, SDET synonyms, rename tolerance) live ONLY there;
# duplicating them here is how the two copies drift apart.
# ---------------------------------------------------------------------------
def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load_applied():
    """Return (applied_pairs, applied_companies) from core/applied_ledger (the authority).

    FAIL CLOSED: if the ledger is empty, stop and tell the operator to build it.
    A silent fallback to progress.json would reintroduce exactly the bug that lost
    ~111 companies (2026-11 schema rewrite) — never degrade to a weaker source.
    """
    from core.applied_ledger import pairs, companies, stats

    p, c = pairs(), companies()
    if not p:
        raise SystemExit(
            "❌ applied ledger is empty — refusing to sweep blind.\n"
            "   Build it:  .venv/bin/python find/ledger_backfill_git.py\n"
            "   Then:      .venv/bin/python find/ledger_backfill_git.py --current"
        )
    log.info("freehire_sweep: dedupe from ledger %s", stats())
    return p, c


# ---------------------------------------------------------------------------
# Gates — pure predicates (no I/O)
# ---------------------------------------------------------------------------
def passes_gate(job, strict=False):
    """Apply title, employer and staleness gates. Returns (ok, why)."""
    title = job.get("title", "")
    if not QA.search(title) or NON.search(title):
        return False, "title"

    ctype = (job.get("enrichment") or {}).get("company_type", "?")
    allowed = {"product"} if strict else GATE_COMPANY_TYPES
    if ctype not in allowed:
        return False, "company_type"

    reality = (job.get("reality") or {}).get("class", "?")
    if reality not in FRESH_CLASSES:
        return False, "stale"

    return True, "ok"


def route_for(source):
    return ROUTING.get((source or "").lower(), UNKNOWN_ROUTE)


# ---------------------------------------------------------------------------
# Discovery — orchestration (logs every decision)
# ---------------------------------------------------------------------------
PAGES = 12          # 12 x 100 = 1,200 postings; catalogue has ~5,400 India QA
PAGE_DEADLINE = 20.0
STALE_STREAK = 40   # sorted newest-first, so this many stale in a row means "we are past the fresh window"


@timeit
def discover(location, show_all=False, strict=False):
    client = FreehireClient()
    pairs, companies = load_applied()

    merged, seen = [], set()
    for label, params in build_search_params(location):
        try:
            jobs = client.search_paged(params, pages=PAGES, deadline=PAGE_DEADLINE)
        except FreehireError as e:
            log.error("freehire_sweep %s failed: %s", label, e)
            print(f"⚠️  {label} failed: {e}", file=sys.stderr)
            continue
        for j in jobs:
            slug = j.get("public_slug")
            if slug and slug not in seen:
                seen.add(slug)
                merged.append(j)

    merged.sort(key=lambda j: j.get("posted_at", ""), reverse=True)
    log.info("freehire_sweep %s: fetched %d unique postings", location, len(merged))

    results, stale_streak = [], 0
    for j in merged:
        title = j.get("title", "")
        company = j.get("company", "")
        ctype = (j.get("enrichment") or {}).get("company_type", "?")
        reality = (j.get("reality") or {}).get("class", "?")
        age = (j.get("reality") or {}).get("age_days", "?")
        c, r = _norm(company), _norm(title)

        # Delegate to the ledger — its matcher is the single source of truth
        # (company suffix tolerance, SDET synonyms, rename handling, 75% token overlap).
        dup = (c, r) in pairs or _ledger.is_applied(company, title)

        if dup:
            log.info("DUPLICATE %s @ %s", title, company)
            results.append({"verdict": "duplicate", "job": j})
            continue

        ok, why = passes_gate(j, strict=strict)
        company_seen = c in companies
        if not show_all and not ok:
            # Newest-first ordering makes staleness monotonic, so a long stale run
            # means the fresh window is over: stop instead of walking 1,200 rows.
            stale_streak = stale_streak + 1 if why == "stale" else 0
            if stale_streak >= STALE_STREAK:
                log.info("freehire_sweep: %d stale in a row — fresh window ended, stopping",
                         stale_streak)
                break
            log.debug("skip (%s) %s @ %s [%s %s %sd]", why, title, company, ctype, reality, age)
            continue
        stale_streak = 0

        results.append({
            "verdict": "pass" if ok else f"fail:{why}",
            "job": j,
            "company_seen": company_seen,
            "route": route_for(j.get("source")),
        })
    return results


def _render_human(results, scope, strict):
    print(f"FREEHIRE QA/SDET OPENINGS — {scope}  (additive source; does not replace prod_sweep.py)")
    print(f"{len(results)} shown. Gate: company_type={'product' if strict else 'product+inhouse'} "
          f"AND reality=fresh. --all to see everything; --strict for product-only.\n")
    n_pass = 0
    for r in results:
        j = r["job"]
        title, company = j.get("title", ""), j.get("company", "")
        src = (j.get("source") or "?").lower()
        ctype = (j.get("enrichment") or {}).get("company_type", "?")
        reality = (j.get("reality") or {}).get("class", "?")
        age = (j.get("reality") or {}).get("age_days", "?")
        auto = j.get("auto_apply_available", False)

        if r["verdict"] == "duplicate":
            print(f"  DUPLICATE (already applied): {title} @ {company}")
            continue
        if r["verdict"] == "pass":
            n_pass += 1
            tag = "✓"
        elif r["verdict"] == "fail:stale":
            tag = "◇ stale"
        else:
            tag = "◇ type"

        autoflag = " AUTO-APPLY" if auto else ""
        seenflag = " (company already in tracker)" if r.get("company_seen") else ""
        print(f"{tag} [{src:14s}] {title[:46]:46s} | {company[:22]:22s} | "
              f"{ctype:9s} {reality:5s} {age}d{autoflag}{seenflag}")
        print(f"      route: {r['route']}")
        print(f"      {j.get('url', '')}")
    print(f"\n{len(results)} shown, {n_pass} pass all gates.")
    print("Next: pick a ✓ → route via the ATS hint (existing scripts) or write a recipe "
          "for NO RECIPE YET boards (SuccessFactors dominates Bangalore QA).")


def main():
    args = [a for a in sys.argv[1:]]
    location = "india" if "india" in args else "bangalore"
    show_all = "--all" in args
    strict = "--strict" in args
    as_json = "--json" in args

    results = discover(location, show_all=show_all, strict=strict)

    if as_json:
        out = []
        for r in results:
            j = r["job"]
            out.append({
                "verdict": r["verdict"],
                "title": j.get("title"),
                "company": j.get("company"),
                "source": j.get("source"),
                "company_type": (j.get("enrichment") or {}).get("company_type"),
                "reality": (j.get("reality") or {}).get("class"),
                "age_days": (j.get("reality") or {}).get("age_days"),
                "auto_apply": j.get("auto_apply_available", False),
                "route": r.get("route"),
                "slug": j.get("public_slug"),
                "url": j.get("url"),
            })
        print(json.dumps(out, indent=1))
        return

    scope = "India" if location == "india" else "Bangalore"
    _render_human(results, scope, strict)


if __name__ == "__main__":
    main()
