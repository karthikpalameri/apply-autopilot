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

from core.logger import log, timeit
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
def _ctl(cmd, timeout=60):
    import socket
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c:
            break
        buf += c
    s.close()
    return json.loads(buf.decode())


def _ev(js):
    return (_ctl({"op": "eval", "js": js}) or {}).get("result")


def _fill_text(fid, v):
    return _ctl({"op": "hfill", "by": "selector", "key": f"#{fid}", "value": v}).get("ok")


# ---------------------------------------------------------------------------
# Plan (dry-run) vs apply (--submit)
# ---------------------------------------------------------------------------
def plan(board, jobid, url):
    d = fetch_questions(board, jobid)
    print(f"GREENHOUSE APPLY — dry-run plan (nothing submitted)")
    print(f"  job:    {d.get('title')} @ {d.get('company_name') or board}")
    print(f"  loc:    {(d.get('location') or {}).get('name')}")
    print(f"  url:    {url}\n")

    plan_ = {"fields": [], "resume": None, "unknown_required": []}
    for q in d.get("questions", []):
        label = q.get("label") or "(unlabeled)"
        required = bool(q.get("required"))
        kind, val = map_answer(q)
        if kind == "resume":
            plan_["resume"] = val
            print(f"  📎 resume   -> {os.path.basename(val)}")
        elif kind:
            if kind == "text" and not val:
                continue  # empty optional (e.g. no github set)
            plan_["fields"].append((label, kind, val, required))
            flag = "REQUIRED" if required else "optional"
            print(f"  ✍️  {label[:44]:46s} -> {kind}:{val}  [{flag}]")
        elif required:
            plan_["unknown_required"].append(label)
            print(f"  ⚠️  {label[:44]:46s} -> UNKNOWN (must answer manually)  [REQUIRED]")
        else:
            print(f"  –   {label[:44]:46s} -> skip (optional, no mapping)")
    return plan_


def apply(board, jobid, url):
    from core.resume_secure import PICK, BEFORE_UPLOAD, POST

    PICK()  # resume MD5 gate (before opening the form)
    print(f"🚀 {url}")
    _ctl({"op": "navigate", "url": url})
    time.sleep(4)

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
            print(f"✍️  {label} = {val}")
        elif kind == "select":
            _ev(f"() => {{ const b=[...document.querySelectorAll('select, input[type=radio]')]"
                f".filter(x=>x.offsetParent); const opt=[...document.querySelectorAll('option')]"
                f".find(o=>o.textContent.trim().toLowerCase().includes('{str(val).lower()}'))"
                f"|| [...document.querySelectorAll('input[type=radio]')].find(r=>r.value.toLowerCase()==='{str(val).lower()}');"
                f" if(opt){{opt.selected=true; opt.dispatchEvent(new Event('change',{{bubbles:true}})); return 'ok';}} return 'none'; }}")
            print(f"🔘 {label} = {val}")
        time.sleep(0.2)

    # resume upload through the MD5 gate
    path = BEFORE_UPLOAD()
    _ctl({"op": "upload_cdp", "path": path})
    print("📎 resume uploaded (md5 gate ✓)")
    POST()
    time.sleep(2)

    # required-empty check
    errs = _ev("() => [...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent&&/this field is required/i.test((e.innerText||''))).length")
    print("required-empty:", errs)
    if int(errs or 0) > 0:
        print("STILL MISSING REQUIRED — manual fix needed")
        sys.exit(2)

    _ev("() => { const b=[...document.querySelectorAll('button, input[type=submit]')].find(x=>x.offsetParent&&/submit/i.test((x.innerText||x.value||'').trim())); if(b){ b.click(); return 'clicked'; } return 'no'; }")
    time.sleep(8)
    st = _ev("() => { const f=document.getElementById('application-form'); const t=document.body.innerText.replace(/\\s+/g,' '); return JSON.stringify({formGone:!f, thanks:/thank you for your application|application has been submitted|your application was/i.test(t)}); }")
    print("AFTER SUBMIT:", st)


def main():
    from core.console import enable_utf8
    enable_utf8()

    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    url = args[0]
    board, jobid = parse_url(url)
    if "--submit" in args:
        apply(board, jobid, url)
    else:
        plan(board, jobid, url)
        print("\nTo actually submit: start the stack (`./run.sh`), then re-run with --submit.")


if __name__ == "__main__":
    main()
