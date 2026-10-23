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
from config.freehire import (
    QA, NON, ROUTING, UNKNOWN_ROUTE,
    GATE_COMPANY_TYPES, FRESH_CLASSES,
    build_search_params,
)


# ---------------------------------------------------------------------------
# Dedupe — same rule as skills/find/SKILL.md (company + role already applied)
# ---------------------------------------------------------------------------
def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load_applied():
    """Return (applied_pairs, applied_companies) from the repo's dedupe sources."""
    pairs, companies = set(), set()
    base = os.path.dirname(os.path.abspath(__file__))

    pj = os.path.join(base, "..", "config", "progress.json")
    if os.path.exists(pj):
        try:
            d = json.load(open(pj))
            for v in d.get("verified_applications", []):
                c, r = _norm(v.get("company")), _norm(v.get("role"))
                if c:
                    companies.add(c)
                    if r:
                        pairs.add((c, r))
        except Exception as e:
            log.warning("freehire_sweep: progress.json unreadable: %s", e)

    am = os.path.join(base, "..", "scratch", "APPLIED.md")
    if os.path.exists(am):
        try:
            for line in open(am):
                if not line.startswith("- [x]"):
                    continue
                body = re.sub(r"\s*\[[^\]]*\]\s*$", "", line).strip("- [x] ")
                body = body.split("(")[0]
                if "—" in body:
                    company, role = body.split("—", 1)
                    c = _norm(company)
                    companies.add(c)
                    pairs.add((c, _norm(role)))
        except Exception as e:
            log.warning("freehire_sweep: APPLIED.md unreadable: %s", e)
    return pairs, companies


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
@timeit
def discover(location, show_all=False, strict=False):
    client = FreehireClient()
    pairs, companies = load_applied()

    merged, seen = [], set()
    for label, params in build_search_params(location):
        try:
            jobs = client.search(params)
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

    results = []
    for j in merged:
        title = j.get("title", "")
        company = j.get("company", "")
        ctype = (j.get("enrichment") or {}).get("company_type", "?")
        reality = (j.get("reality") or {}).get("class", "?")
        age = (j.get("reality") or {}).get("age_days", "?")
        c, r = _norm(company), _norm(title)

        if (c, r) in pairs:
            log.info("DUPLICATE %s @ %s", title, company)
            results.append({"verdict": "duplicate", "job": j})
            continue

        ok, why = passes_gate(j, strict=strict)
        company_seen = c in companies
        if not show_all and not ok:
            log.debug("skip (%s) %s @ %s [%s %s %sd]", why, title, company, ctype, reality, age)
            continue

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
    from core.console import enable_utf8
    enable_utf8()

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
