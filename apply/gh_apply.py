#!/usr/bin/env python3
"""apply/gh_apply.py — GENERIC Greenhouse apply, driven by a freehire-routed URL.

The apply half of the freehire integration: find/freehire_sweep.py routes
`source=greenhouse` jobs here. Unlike fill_gh_fast.py (a hardcoded one-off), this
fetches the form's questions from Greenhouse's public boards API and maps the
standard fields to config/answers.py (DRY), so ANY Greenhouse board works.

SAFE BY DEFAULT — dry-run only. It fetches the live form + prints exactly what it
would fill/upload. It touches the browser and submits ONLY with an explicit
--submit flag (a real application is irreversible).

Usage:
    .venv/bin/python apply/gh_apply.py <greenhouse-url>            # dry-run (plan)
    .venv/bin/python apply/gh_apply.py <greenhouse-url> --submit   # fill + upload + submit
"""
import json, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import log, timeit, say
from core.ui import check, fill, select, upload, until
from config.answers import A, RESUME


# ---------------------------------------------------------------------------
# Greenhouse public boards API — the form schema (no auth)
# ---------------------------------------------------------------------------
_URL_RE = re.compile(r"job-boards\.greenhouse\.io/([^/]+)/jobs/(\d+)")


def parse_url(url):
    m = _URL_RE.search(url)
    if not m:
        raise SystemExit(f"not a greenhouse job-boards URL: {url}")
    return m.group(1), m.group(2)  # board token, job id


@timeit
def fetch_questions(board, jobid):
    import urllib.request, ssl
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl._create_unverified_context()
    u = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jobid}?questions=true"
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Answer mapping — standard Greenhouse labels -> config/answers.py (DRY)
# ---------------------------------------------------------------------------
def map_answer(question):
    """Return (kind, value) or None if we can't auto-answer."""
    label = (question.get("label") or "").strip().lower()
    fields = question.get("fields") or []

    if any(f.get("type") == "input_file" for f in fields):
        if re.search(r"resume|\bcv\b|curriculum", label) and not re.search(r"cover", label):
            return ("resume", RESUME)
        return (None, None)  # cover letter / other uploads: never auto-attach
    if re.search(r"\bfirst\b.*\bname\b|\bfirst name\b", label):
        return ("text", A["first"])
    if re.search(r"\blast\b.*\bname\b|\blast name\b", label):
        return ("text", A["last"])
    if re.search(r"\bemail\b", label):
        return ("text", A["email"])
    if re.search(r"\bphone\b", label):
        return ("text", A["phone"])
    if re.search(r"\blinkedin\b", label):
        return ("text", A["linkedin"])
    if re.search(r"\bgithub\b", label):
        return ("text", A["github"] or None)
    if re.search(r"\bwebsite\b|\bportfolio\b", label):
        return ("text", A["github"] or None)
    if re.search(r"\bcurrent location\b|\byour location\b|\bcity\b|\bwhere are you\b", label):
        return ("text", A["location"])
    if re.search(r"\bwilling\b|\bare you\b|\blegally authorized\b|\bwork authorization\b", label):
        # yes/no or multi_value single select -> "Yes" (candidate is authorized in India)
        return ("select", "Yes")
    return (None, None)


# ---------------------------------------------------------------------------
# Browser bridge (:9000 ctl) — same primitives as fill_gh_fast.py
# ---------------------------------------------------------------------------
from core.ctl import call as _ctl  # single owner (:9000 socket) — DRY


def _ev(js):
    return (_ctl({"op": "eval", "js": js}) or {}).get("result")


def _fill_text(fid, v):
    return fill(f"#{fid}", v)


# ---------------------------------------------------------------------------
# Plan (dry-run) vs apply (--submit)
# ---------------------------------------------------------------------------
def plan(board, jobid, url):
    d = fetch_questions(board, jobid)
    say("GREENHOUSE APPLY — dry-run plan (nothing submitted)")
    say(f"  job:    {d.get('title')} @ {d.get('company_name') or board}")
    say(f"  loc:    {(d.get('location') or {}).get('name')}")
    say(f"  url:    {url}\n")

    plan_ = {"fields": [], "resume": None, "unknown_required": []}
    for q in d.get("questions", []):
        label = q.get("label") or "(unlabeled)"
        required = bool(q.get("required"))
        kind, val = map_answer(q)
        if kind == "resume":
            plan_["resume"] = val
            say(f"  📎 resume   -> {os.path.basename(val)}")
        elif kind:
            if kind == "text" and not val:
                continue  # empty optional (e.g. no github set)
            plan_["fields"].append((label, kind, val, required))
            flag = "REQUIRED" if required else "optional"
            say(f"  ✍️  {label[:44]:46s} -> {kind}:{val}  [{flag}]")
        elif required:
            plan_["unknown_required"].append(label)
            say(f"  ⚠️  {label[:44]:46s} -> UNKNOWN (must answer manually)  [REQUIRED]")
        else:
            say(f"  –   {label[:44]:46s} -> skip (optional, no mapping)")
    return plan_


def apply(board, jobid, url):
    from core.resume_secure import PICK, BEFORE_UPLOAD, POST

    PICK()  # resume MD5 gate (before opening the form)
    say(f"🚀 {url}")
    _ctl({"op": "navigate", "url": url})
    # wait for the application form instead of a flat 4s
    until(lambda: _ev("() => !!document.getElementById('application-form')"),
          timeout=15, interval=0.4, what="greenhouse form")

    d = fetch_questions(board, jobid)
    for q in d.get("questions", []):
        label = q.get("label") or ""
        kind, val = map_answer(q)
        if not kind or kind == "resume":
            continue
        if kind == "text" and not val:
            continue
        # greenhouse standard input ids are first_name / last_name / email / phone …
        fid = re.sub(r"[^a-z0-9_]+", "_", label.strip().lower()).strip("_")
        if kind == "text":
            _fill_text(fid, val)
            say(f"✍️  {label} = {val}")
        elif kind == "select":
            # Was one JS string that searched every <option> on the page and, on the
            # radio fallback, set `opt.selected` — a property radios do not have, so
            # that branch could never have worked. Try the native select first, then
            # the radio, using the idempotent primitives.
            chosen = select(f"#{fid}", val)
            if chosen:
                say(f"🔘 {label} = {val}  -> {chosen}")
            elif check(f"#{fid}"):
                say(f"🔘 {label} = {val}  (radio)")
            else:
                log.warning("could not answer %r with %r (no #%s select or radio)",
                            label, val, fid)
        time.sleep(0.2)

    # resume upload through the MD5 gate
    path = BEFORE_UPLOAD()
    n = upload(None, path)          # no selector -> first file input, same as before
    say(f"📎 resume uploaded (md5 gate ✓, {n} file)")
    POST()
    until(lambda: _ev("() => !document.body.innerText.includes('Attach') ? true : "
                      "document.querySelectorAll('[class*=file]').length > 0"),
          timeout=10, interval=0.3, what="resume upload")

    # required-empty check
    errs = _ev("() => [...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent&&/this field is required/i.test((e.innerText||''))).length")
    say("required-empty:", errs)
    if int(errs or 0) > 0:
        say("STILL MISSING REQUIRED — manual fix needed")
        sys.exit(2)

    _ev("() => { const b=[...document.querySelectorAll('button, input[type=submit]')].find(x=>x.offsetParent&&/submit/i.test((x.innerText||x.value||'').trim())); if(b){ b.click(); return 'clicked'; } return 'no'; }")
    until(lambda: _ev("() => { const f=document.getElementById('application-form'); "
                      "const t=document.body.innerText; return !f || "
                      "/thank you for your application|application has been submitted|your application was/i.test(t); }"),
          timeout=20, interval=0.4, what="submit confirmation")
    st = _ev("() => { const f=document.getElementById('application-form'); const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({formGone:!f, thanks:/thank you for your application|application has been submitted|your application was/i.test(t)}); }")
    say("AFTER SUBMIT:", st)


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    url = args[0]
    board, jobid = parse_url(url)
    if "--submit" in args:
        apply(board, jobid, url)
    else:
        plan(board, jobid, url)
        say("\nTo actually submit: start the stack (`./run.sh`), then re-run with --submit.")


if __name__ == "__main__":
    main()
