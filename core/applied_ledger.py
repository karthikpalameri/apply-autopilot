#!/usr/bin/env python3
"""core/applied_ledger.py — append-only STORE for application attempts.

SINGLE RESPONSIBILITY: read and append the JSONL log. No vocabulary (config/dedupe.py),
no CLI (find/ledger_*.py), no foreign file parsing (find/ledger_backfill_git.py).

WHY APPEND-ONLY
---------------
`progress.json` was a mutable document whose shape changed under us. On 2026-11-04 a
schema rewrite (150 keys -> 5) silently destroyed ~111 companies of application history
(`instahyre[55]`, `linkedin[27]`, `blocked[17]`, `amazon[7]`, + 64 URL-keyed records).
`HighLevel / QA Automation Engineer` lived only in `instahyre`; it vanished, so a later
sweep saw "no record" and we re-filled and re-submitted. Verified three ways: key counts,
company-identity set diff, and raw-regex forensics over `git show d391782:config/progress.json`.

An append-only log can gain a false line, but it **cannot lose a true one**.

USAGE
    from core.applied_ledger import record, is_applied, pairs, companies, stats
"""
import json, os, re
from datetime import datetime, timezone

from config.dedupe import COMPANY_ALIASES, ROLE_OVERLAP_MIN, ROLE_SYNONYMS, SUFFIX_WORDS

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(BASE, "data", "applied_ledger.jsonl")


# ---------------------------------------------------------------------------
# Identity — pure functions, driven by config/dedupe.py
# ---------------------------------------------------------------------------
def co_key(s):
    """Company identity. Split on non-alphanumerics FIRST, then drop suffix *words*.

    A plain substring substitution strips the letters "inc" out of ordinary names.
    Short-name aliases ("hpe") resolve AFTER the suffix strip, so the canonical key
    is reached the same way whichever spelling the board used.
    """
    key = " ".join(w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
                   if w not in SUFFIX_WORDS).strip()
    return COMPANY_ALIASES.get(key, key)


def role_key(s):
    """Role identity with SDET/QE spelling variants collapsed."""
    n = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (s or "").lower())).strip()
    for pat, rep in ROLE_SYNONYMS:
        n = pat.sub(rep, n)
    return re.sub(r"\s+", " ", n).strip()


def company_matches(a, b):
    """True if two company keys refer to the same employer.

    Two rules only, both measured against the real 632-company ledger:
      1. equal after removing spaces  — "ai squared" == "aisquared" (LinkedIn spelling)
      2. one key's tokens are a SUBSET of the other's — "pure storage" inside
         "everpure formerly pure storage", "amazon" inside "amazon web services"

    Deliberately NOT substring containment and NOT any-token overlap. Both were tried
    and both lied: any-overlap made Qualys ≡ RSA Security (word "security") and
    dextr ai ≡ zilo ai (word "ai"); 6-char containment made elastic ≡ elasticrun and
    dextr ai ≡ dextra; 3-char containment made abb ≡ snabbit. Across 632 companies that
    produced 360 false pairs, each a live role silently skipped as "duplicate".
    A rename that shares no full token belongs in COMPANY_ALIASES, not here.
    """
    if not a or not b:
        return False
    if a == b or a.replace(" ", "") == b.replace(" ", ""):
        return True
    ta, tb = set(a.split()), set(b.split())
    return bool(ta and tb) and (ta <= tb or tb <= ta)


def roles_match(a, b):
    """True if two role keys are the same requisition."""
    if not a or not b:
        return not a and not b
    if a == b or a.startswith(b) or b.startswith(a):
        return True
    ta, tb = set(a.split()), set(b.split())
    return bool(ta and tb) and len(ta & tb) / max(len(ta), 1) >= ROLE_OVERLAP_MIN


# ---------------------------------------------------------------------------
# Store — the only I/O in this module
# ---------------------------------------------------------------------------
def _path():
    return LEDGER


_cache = {"key": None, "rows": None}


def iter_rows():
    """Yield every row. A corrupt line is skipped, never fatal.

    Cached on (mtime, size). find/freehire_sweep.py calls pairs() AND
    is_applied() inside its per-result loop, and each call re-read and re-parsed
    the whole ledger — O(results x rows) for no reason, and worse every month as
    the ledger grows. The ledger is append-only, so an append changes size and
    mtime and the cache drops by itself.
    """
    p = _path()
    if not os.path.exists(p):
        return
    try:
        st = os.stat(p)
    except OSError:
        return
    key = (st.st_mtime_ns, st.st_size)
    if _cache["key"] == key:
        # `rows` is None until the first successful parse; `or []` keeps the
        # generator from raising TypeError on that edge instead of yielding nothing.
        yield from (_cache["rows"] or [])
        return

    parsed = []
    with open(p, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                parsed.append(json.loads(line))
            except Exception:
                import sys
                print(f"⚠️  applied_ledger: skipping corrupt line {lineno}", file=sys.stderr)
    _cache["key"], _cache["rows"] = key, parsed
    yield from parsed


def rows():
    return list(iter_rows())


def _row(company, role, status, url, job_id, date, proof, source):
    """Build one ledger row. Shared by record() and amend() so the schema stays
    in one place."""
    if not (company or "").strip():
        raise ValueError("company is required")
    return {
        "company": company, "role": role or "", "status": status or "",
        "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "url": url or "", "job_id": str(job_id or ""),
        "proof": proof or "", "source": source or "",
        "c": co_key(company), "r": role_key(role),
    }


def _append(row):
    os.makedirs(os.path.dirname(_path()), exist_ok=True)
    with open(_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def record(company, role, status, url="", job_id="", date="", proof="", source=""):
    """Append one attempt. Idempotent on (company-key, role-key, url).

    Returns the row written, or None if it was already present.
    """
    row = _row(company, role, status, url, job_id, date, proof, source)
    for e in iter_rows():
        if (e.get("c"), e.get("r"), e.get("url")) == (row["c"], row["r"], row["url"]):
            return None
    return _append(row)


def amend(company, role, status, url="", job_id="", date="", proof="", source=""):
    """Append a superseding attempt for the same (company-key, role-key, url).

    record() refuses an existing key, which is right for duplicates but wrong when
    an earlier row was a blocker that later resolved (blocked -> submitted). The
    earlier row stays in the file; readers take the LAST row per key, so history
    is preserved and the current state is honest.
    """
    return _append(_row(company, role, status, url, job_id, date, proof, source))


# ---------------------------------------------------------------------------
# Queries — no I/O beyond reading the store
# ---------------------------------------------------------------------------
def is_applied(company, role=None):
    """True if ANY prior attempt exists at this company (optionally matching role)."""
    ck = co_key(company)
    if not ck:
        return False
    rk = role_key(role) if role else None
    for e in iter_rows():
        if not company_matches(ck, e.get("c") or ""):
            continue
        if rk is None or roles_match(rk, e.get("r") or ""):
            return True
    return False


def job_ids():
    """{job_id} for every recorded attempt that captured one.

    Single owner for the "has this ATS/LinkedIn job id been attempted?" question.
    apply/li_drive.py and apply/li_listed_apply.py used to grep APPLIED.md and
    progress.json with hand-rolled needles (f"_{jid}_"); that missed rows and
    disagreed with the ledger.
    """
    return {str(e["job_id"]) for e in iter_rows() if e.get("job_id")}


def has_job_id(job_id):
    """True if this exact job id was already attempted."""
    return bool(job_id) and str(job_id) in job_ids()



def pairs():
    """{(company_key, role_key)} for every recorded attempt."""
    return {(e.get("c"), e.get("r")) for e in iter_rows() if e.get("c")}


def companies():
    """{company_key} for every recorded attempt."""
    return {e["c"] for e in iter_rows() if e.get("c")}


def stats():
    r = rows()
    return {"rows": len(r),
            "companies": len({e.get("c") for e in r if e.get("c")}),
            "pairs": len({(e.get("c"), e.get("r")) for e in r if e.get("c")})}
