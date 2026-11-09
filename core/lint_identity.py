"""Guard: config/user.json is the ONE source of candidate facts.

Why this exists
---------------
`config/user.json` is the authority. `config/resume_facts.json` is a *derived
cache* scraped out of the resume PDF by `find/resume_facts.py`, and a skill file
must never carry a copy of a personal value.

That invariant silently broke twice:
  - `find/resume_facts.py` built `merged` for its printout but wrote the raw
    scrape, so the cache held a differently-spaced phone number than user.json
    (and a LinkedIn URL that disagreed on a trailing slash).
  - DOB and phone had been copy-pasted into four skill files, so a correction in
    user.json would leave four stale copies behind.

This check is deliberately narrow and offline: it only compares the cache
against the source, and it only flags PII literals that appear in tracked
skill/doc files. It never prints a personal value.

Usage:
    .venv/bin/python core/lint_identity.py          # exit 1 on drift
    .venv/bin/python core/lint_identity.py -v       # name the offending keys
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = ROOT / "config" / "user.json"
FACTS = ROOT / "config" / "resume_facts.json"

# Keys the cache must agree with when both carry them. Identity fields only —
# the cache legitimately adds derived keys (work_history, degree, school).
SHARED_KEYS = (
    "full_name", "email", "phone", "phone_national", "phone_country_code",
    "linkedin_url", "github", "date_of_birth", "resume_path",
    "employer_current", "employer_current_start", "city", "country",
    "gender", "last_working_day", "expected_ctc_lpa", "current_ctc_lpa",
)

# Files where a personal literal must never be hardcoded. Values are read from
# user.json at runtime, so a literal here is by definition a duplicate source.
SCAN_GLOBS = ("skills/**/*.md", "docs/**/*.md", "README.md")

# The identity SSOT is the ONE place a personal value is allowed to be written
# down (it is the human-readable mirror of config/user.json). Everything else
# must reference it instead of copying it. The token opens an allowed BLOCK that
# lasts until a line containing only `<!-- /identity-ssot:allow -->`.
ALLOW_MARKER = "identity-ssot:allow"
ALLOW_END = "/identity-ssot:allow"

# Short numeric literals (phone tails) are too collision-prone to scan for.
MIN_LITERAL_LEN = 6


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def check_drift(user: dict, facts: dict) -> list[str]:
    """Keys where the derived cache disagrees with the source."""
    bad = []
    for k in SHARED_KEYS:
        uv, fv = user.get(k), facts.get(k)
        if uv in (None, "") or fv in (None, ""):
            continue
        if str(uv).strip() != str(fv).strip():
            bad.append(k)
    return bad


def _literals(user: dict) -> dict[str, str]:
    """Personal strings worth scanning for, mapped to the key they came from."""
    out = {}
    for k in ("email", "phone", "phone_national", "linkedin_url", "github",
              "date_of_birth", "full_name", "address_line1", "postal_code"):
        v = user.get(k)
        if isinstance(v, str) and len(v) >= MIN_LITERAL_LEN:
            out[v] = k
    return out


def check_literals(user: dict) -> list[tuple[str, int, str]]:
    """(path, lineno, key) for every hardcoded personal literal in a skill/doc."""
    lits = _literals(user)
    if not lits:
        return []
    hits = []
    for pattern in SCAN_GLOBS:
        for path in ROOT.glob(pattern):
            if not path.is_file():
                continue
            in_block = False
            for i, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
                if ALLOW_END in line:
                    in_block = False
                    continue
                if ALLOW_MARKER in line:
                    in_block = True
                    continue
                if in_block:
                    continue
                for lit, key in lits.items():
                    if lit in line:
                        hits.append((str(path.relative_to(ROOT)), i, key))
                        break
    return hits


def main() -> int:
    verbose = "-v" in sys.argv
    user, facts = _load(USER), _load(FACTS)

    if not user:
        # Generic clone: no identity has been created yet, so there is nothing to
        # leak or drift. The gate is green; run `python setup.py` to create the
        # identity and the next run will enforce the single-source invariant.
        print(f"[lint_identity] {USER.relative_to(ROOT)} missing — nothing to check "
              "(generic clone; run `python setup.py` first).")
        return 0

    drift = check_drift(user, facts)
    leaks = check_literals(user)

    if not drift and not leaks:
        print("[lint_identity] OK — user.json is the single source; cache agrees, "
              "no personal literals in skills/docs.")
        return 0

    if drift:
        print("[lint_identity] DRIFT — config/resume_facts.json disagrees with user.json.")
        if verbose:
            for k in drift:
                print(f"  key: {k}")
        print("  Fix: `.venv/bin/python find/resume_facts.py` (user.json wins conflicts).")
    if leaks:
        print("[lint_identity] LEAK — personal values hardcoded in skills/docs:")
        for path, lineno, key in leaks:
            print(f"  {path}:{lineno}  ({key})")
        print("  Fix: read the value at runtime from config/user.json; point to "
              "`skills/REFERENCE.md#identity` instead of copying it.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
