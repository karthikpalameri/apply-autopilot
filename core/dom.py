#!/usr/bin/env python3
"""core/dom.py — shared accessibility-snapshot + DOM-dump helpers.

Single owner for two helpers that had been copy-pasted across the ATS drivers:

    ref_of()    was defined 3× (core/login_naukri.py, core/login_linkedin.py,
                apply/li_listed_apply.py) with the same regex and different
                parameter names.
    dom_dump()  was defined 2× (core/login_naukri.py, core/login_linkedin.py)
                with different selector, slice limit and output filename.

Both were identical in intent, so a fix in one never reached the others.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "logs")


def ref_of(snapshot, pattern):
    """Return the accessibility ref (e.g. 'e12') of the first role matching `pattern`.

    `snapshot` is the text of browser_snapshot(); `pattern` is the leading part of
    the role line, e.g. r'button "Easy Apply"'. Returns None when absent.
    """
    if not snapshot:
        return None
    m = re.search(rf'({pattern})[^\[]*\[ref=(\w+)\]', snapshot)
    return m.group(2) if m else None


def dump_dom(browser, name, selector="'form'", limit=2500, fallback="document.body"):
    """Dump page innerHTML to logs/<name>.txt and return the text.

    For failure forensics: when a ref lookup misses, this shows the real structure
    instead of guessing. `browser` is an McpBrowser (anything with _call).
    """
    expr = (
        "() => { const f=document.querySelector(%s)||%s; "
        "return f.innerHTML.replace(/</g,'\\n<').slice(0,%d); }"
        % (selector, fallback, limit)
    )
    r = browser._call("browser_evaluate", {"expression": expr})
    content = (r.get("result") or {}).get("content") or []
    txt = "".join(c.get("text", "") for c in content if isinstance(c, dict))
    os.makedirs(LOGS, exist_ok=True)
    path = os.path.join(LOGS, f"{name}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"📄 DOM dumped -> {os.path.relpath(path, ROOT)}")
    return txt


def checked_radio_labels(browser_ev):
    """(label, id) of every checked radio — assert the resume pick before clicking Next.

    Proven 2026-11-05: LinkedIn renders ~22 radios for ~21 duplicate resume entries
    and only one is checked. Reading the label list instead of the checked state is
    how a wrong resume gets submitted.
    """
    expr = (
        "() => JSON.stringify([...document.querySelectorAll('input[type=radio]:checked')]"
        ".map(r => [ (r.getAttribute('aria-label') || (r.closest('label')||{}).innerText || '').trim(), r.id ]))"
    )
    import json
    return json.loads(browser_ev(expr) or "[]")
