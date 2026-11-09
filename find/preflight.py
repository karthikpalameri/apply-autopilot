#!/usr/bin/env python3
"""find/preflight.py — ONE command that does the whole FRESH-START gate (steps 1-5).

Replaces ~10 manual round-trips at session start:
  guard -> sweep -> LinkedIn harvest -> ledger rows per candidate -> classify

Usage:
  .venv/bin/python find/preflight.py                 # full: guard + sweep + harvest
  .venv/bin/python find/preflight.py --no-sweep      # skip freehire (fast, harvest only)
  .venv/bin/python find/preflight.py --pages 3       # harvest depth (default 2 => ~40 cards)

Output: a single READY table sorted by (age asc, company). Nothing else.
"""
import sys, os, json, re, ssl, time, subprocess, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config.dedupe import ROLE_QA, ROLE_STACK_REJECT, TERMINAL_STATUSES  # noqa: E402
from core.logger import log  # noqa: E402
from core.applied_ledger import co_key, company_matches, role_key, roles_match  # noqa: E402

LEDGER = os.path.join(ROOT, "data", "applied_ledger.jsonl")
SCRATCH = os.path.join(ROOT, "scratch", "preflight")


def _rx1(pattern: str, text: str, default: str = "", flags: int = 0) -> str:
    """First capture group of `pattern` in `text`, else `default`.

    Replaces the `(re.search(p, t) or [None, d])[1]` idiom that appeared six
    times in one function. That form reads as an index trick and types as
    `Match | list`, so a type checker cannot prove the result is a `str` — it
    reported five errors here. One helper, one behaviour, str out.
    """
    m = re.search(pattern, text, flags)
    return m.group(1) if m else default

# ---- gates -----------------------------------------------------------------
SERVICES = {
    "accenture", "infosys", "tcs", "cognizant", "wipro", "capgemini", "hcl",
    "tech mahindra", "mphasis", "ntt data", "cgi", "pwc", "deloitte", "kpmg",
    "ey", "ibm", "ust", "itc infotech", "innova", "arohana", "hcltech",
    "happiest minds", "beyondsoft", "applicantz", "acura", "eurofins",
    "getixhealth", "equiniti", "qualitest", "ness digital", "persistent",
    "birlasoft", "coforge", "hexaware", "virtusa", "zensar", "ltimindtree",
    "source-right", "qaagility", "recro", "accelon", "dymon asia", "dxc",
}
STACK_REJECT = ROLE_STACK_REJECT  # single owner: config/dedupe.py
ROLE_OK = ROLE_QA  # single owner: config/dedupe.py
ROLE_BAD = re.compile(r"developer|engineer\s*[-–]\s*(?!test)|architect|manager|lead\s+product|salesforce|frontend|backend|data scien", re.I)
DONE_STATUS = TERMINAL_STATUSES  # single owner: config/dedupe.py (was a private copy)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
CTX = ssl._create_unverified_context()


def load_ledger():
    rows = []
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    log.debug("skipping corrupt ledger line: %s", e)
    return rows


def ledger_index(rows):
    """company(lower) -> list of (role_KEY, status, date)

    Store role_key(role), not the raw title: roles_match() compares keys, so a raw
    title here made every comparison key-vs-raw and quietly returned False unless
    the posting's title already happened to equal its own key. Company identity was
    keyed via co_key() at compare time but the role side never was — the same
    private-divergence-from-the-canonical-matcher pattern as before.
    """
    idx = {}
    for r in rows:
        c = str(r.get("company", "")).strip().lower()
        idx.setdefault(c, []).append(
            (role_key(str(r.get("role", ""))), str(r.get("status", "")), str(r.get("date", "")))
        )
    return idx


# Identity + role matching are OWNED by core.applied_ledger (co_key/company_matches/
# roles_match). Do not reimplement them here: a private copy had already drifted
# (it disagreed with co_key on "Ping Identity", "AI Squared", "Sony India Software
# Centre") and used a looser 0.4 role overlap than ROLE_OVERLAP_MIN. That divergence
# is the exact bug class that destroyed ~111 companies on 2026-11-04.


def role_known(idx, company, role):
    """None = new company. False = company seen, role is new. Tuple = duplicate."""
    cands = []
    for c, items in idx.items():
        if company_matches(co_key(c), co_key(company)):
            cands.extend(items)
    if not cands:
        return None
    # roles_match() takes KEYS (the ledger stores role_key(role)). Passing the raw
    # title compared "QA Engineer" against "qa engineer" and got False, so role
    # dedupe only ever fired when the posting's title already happened to be its
    # own key. Key the incoming title too.
    rk = role_key(role)
    for r_role, status, dt in cands:
        if status in DONE_STATUS and roles_match(rk, r_role):
            return (r_role, status, dt)
    return False


def _guest_page(url):
    """One LinkedIn guest-search page, or "" on failure (logged, not swallowed)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        return urllib.request.urlopen(req, context=CTX, timeout=15).read().decode("utf8", "ignore")
    except Exception as e:
        log.debug("guest search failed: %s: %s", e.__class__.__name__, e)
        return ""


def harvest(keywords, pages):
    """Fetch every guest-search page at once, then parse.

    Serially this slept 1.2s after each page and another 1.5s on every failure, so
    3 keywords x 2 pages cost ~15s whether or not LinkedIn answered. One pause for
    the whole batch keeps the request rate polite without paying it six times.
    """
    os.makedirs(SCRATCH, exist_ok=True)
    urls = ["https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={urllib.parse.quote(kw)}"
            "&location=Bengaluru%2C%20Karnataka%2C%20India"
            f"&f_TPR=r172800&start={p * 25}"
            for kw in keywords for p in range(pages)]

    time.sleep(1.2)   # one politeness pause for the batch, not one per page
    with ThreadPoolExecutor(max_workers=len(urls)) as ex:
        htmls = list(ex.map(_guest_page, urls))

    seen = {}
    for html in htmls:
        for it in html.split("<li>")[1:]:
            jid = _rx1(r"urn:li:jobPosting:(\d+)", it, default="")
            if not jid or jid in seen:
                continue
            title = _rx1(r'base-search-card__title">\s*(.*?)\s*</h3>', it, flags=re.S)
            cra = _rx1(r'base-search-card__subtitle">\s*(.*?)\s*</h4>', it, flags=re.S)
            comp = _rx1(r">\s*([^<>]+?)\s*</a>", cra, default=cra)
            loc = _rx1(r'job-search-card__location">\s*(.*?)\s*</span>', it, flags=re.S)
            dt = _rx1(r'<time[^>]*datetime="([^"]+)"', it)
            seen[jid] = {
                "id": jid,
                "company": re.sub(r"\s+", " ", comp).strip(),
                "title": re.sub(r"\s+", " ", title).strip(),
                "location": re.sub(r"\s+", " ", loc).strip(),
                "posted": dt[:10],
            }

    return list(seen.values())


ATS_LIVE = {
    # slug -> (api url builder, parser). Both return "<title> | <location>" lines
    # for live/listed postings only. Measured 2026-11-06: one HTTP call each.
    "ashby": lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}",
    "greenhouse": lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs",
}


def resolve_ats(company, title):
    """Find the ATS posting for (company, title) without spending a browser tab.

    Both employers applied on 2026-11-06 had NO LinkedIn Easy Apply, so the two
    hops (LinkedIn job view -> /safety/go/?url=<encoded> -> ATS) cost 3 navigations
    per application. Slug guesses over the public board APIs answer the same
    question in one call and also prove the requisition is live (isListed), which
    is what the blank-Ashby-tab confusion needed.
    """
    from core.fetch import get_json
    words = re.findall(r"[a-z0-9]+", company.lower())
    slugs = {"".join(words), "-".join(words), words[0] if words else ""}
    want = re.findall(r"[a-z0-9]+", title.lower())
    for ats, url_for in ATS_LIVE.items():
        for slug in filter(None, slugs):
            data = get_json(url_for(slug))
            if not data:
                continue
            jobs = data.get("jobs") or []
            for j in jobs:
                if ats == "ashby" and not j.get("isListed", True):
                    continue
                jt = re.findall(r"[a-z0-9]+", (j.get("title") or "").lower())
                overlap = len(set(want) & set(jt)) / max(1, len(set(want) | set(jt)))
                if overlap >= 0.4:
                    jid = j.get("id") or j.get("id_string") or j.get("absolute_url", "")
                    base = ("https://jobs.ashbyhq.com/" + slug) if ats == "ashby" \
                        else ("https://job-boards.greenhouse.io/" + slug)
                    return {"ats": ats, "slug": slug, "job_id": jid,
                            "url": j.get("absolute_url") or f"{base}/{jid}",
                            "title": j.get("title"), "location": _flatten_loc(j.get("location"))}
    return None


def _flatten_loc(loc):
    """Greenhouse returns {name:...}, Ashby may return a list of {location:...}.

    Both used to reach the display f-string raw and die with
    `TypeError: unsupported format string passed to list.__format__`,
    which killed preflight *after* the READY table had already printed.
    """
    if not loc:
        return ""
    if isinstance(loc, str):
        return loc
    if isinstance(loc, dict):
        return str(loc.get("name") or loc.get("location") or "")
    if isinstance(loc, (list, tuple)):
        return ", ".join(x for x in (_flatten_loc(i) for i in loc) if x)
    return str(loc)


def toolchain_health():
    """One line covering the two things that silently sink a session.

    1. ctl bridge (:9000) — if down, every core/ui + core/ctl fast-path call
       burns its timeout and reads as "the UI is slow".
    2. profile-dir collision — two servers sharing runtime/mcp-session makes
       the loser die with "Browser is already in use" while still charging
       5000 ms per rejected call.  Pi's MCP owns runtime/mcp-session;
       Python scripts own runtime/py-session.
    """
    import socket
    parts = []
    up = False
    try:
        with socket.create_connection(("127.0.0.1", 9000), timeout=0.4):
            up = True
    except OSError:
        pass
    parts.append("ctl:9000=" + ("up" if up else "DOWN"))

    holders = {}
    try:
        out = subprocess.run(["pgrep", "-fl", "server.py|cloak-browser-mcp"],
                             capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines():
            m = re.search(r"--profile-dir\s+(\S+)", line)
            if m:
                holders.setdefault(m.group(1), 0)
                holders[m.group(1)] += 1
    except Exception as e:
        # Profile detection is best-effort: a missing ps/lsof or an odd process
        # table must not fail preflight. Log it so a silent None is never the
        # only evidence when "profiles=ok" is wrong.
        log.debug("profile scan skipped: %s", e)
    clash = [p for p, n in holders.items() if n > 1]
    parts.append("profiles=" + ("CLASH:" + clash[0] if clash else "ok"))
    return "  ".join(parts)


def main():
    args = sys.argv[1:]
    pages = 2
    if "--pages" in args:
        pages = int(args[args.index("--pages") + 1])
    do_sweep = "--no-sweep" not in args

    t0 = time.time()
    print("=" * 78)
    print("PREFLIGHT  " + date.today().isoformat())
    print("=" * 78)

    # 0. toolchain health — cheap, catches the two failures that silently cost the session
    #    (browser server down; profile dir shared with another running server)
    _health = toolchain_health()
    print(f"[0] toolchain: {_health}")

    # 1. guard
    g = subprocess.run([sys.executable, os.path.join(ROOT, "find", "ledger_guard.py")],
                       capture_output=True, text=True)
    ok = g.returncode == 0
    print(f"[1] ledger_guard: {'PASS' if ok else 'FAIL'}  {g.stdout.strip().splitlines()[-1] if g.stdout.strip() else ''}")
    if not ok:
        print(g.stdout, g.stderr)
        print("\nSTOP: ledger not intact. Do not apply.")
        return 2

    rows = load_ledger()
    idx = ledger_index(rows)
    print(f"[2] ledger rows={len(rows)}  companies={len(idx)}")

    # 2. freehire sweep (optional)
    if do_sweep:
        out = os.path.join(SCRATCH, "sweep.json")
        os.makedirs(SCRATCH, exist_ok=True)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "find", "freehire_sweep.py"),
                            "--strict", "--json"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith("["):
            open(out, "w").write(r.stdout)
            try:
                sw = json.loads(r.stdout)
                fresh = [x for x in sw if x.get("verdict") != "duplicate"]
                print(f"[3] freehire_sweep: {len(sw)} results, {len(fresh)} non-dupe")
                for x in fresh:
                    print(f"      + {x.get('company')} | {x.get('title','')[:46]} | {x.get('source')}")
            except Exception as e:
                print(f"[3] freehire_sweep: parse error {e}")
        else:
            print(f"[3] freehire_sweep: skipped/failed rc={r.returncode}")
    else:
        print("[3] freehire_sweep: skipped (--no-sweep)")

    # 3. harvest
    jobs = harvest(["SDET", "QA Automation Engineer", "Test Automation Engineer"], pages)
    print(f"[4] linkedin harvest: {len(jobs)} unique cards")

    # 4. classify
    today = date.today()
    ready, blocked, dupes = [], [], []
    for j in jobs:
        age = 99
        try:
            age = (today - datetime.strptime(j["posted"], "%Y-%m-%d").date()).days
        except Exception as e:
            log.debug("no posted date for %s (%s) — treating as oldest", j.get("company"), e)
        company = j["company"]
        title = j["title"]
        cl = company.lower()

        if any(s == cl or s in cl for s in SERVICES):
            blocked.append((company, title, "services/staffing", age, j["id"]))
            continue
        if STACK_REJECT.search(title):
            blocked.append((company, title, "stack(C#/.NET)", age, j["id"]))
            continue
        if not ROLE_OK.search(title):
            blocked.append((company, title, "wrong-role", age, j["id"]))
            continue
        if ROLE_BAD.search(title) and not re.search(r"test", title, re.I):
            blocked.append((company, title, "wrong-seniority-title", age, j["id"]))
            continue

        hit = role_known(idx, company, title)
        if hit:
            dupes.append((company, title, f"{hit[1]} {hit[2]}", age, j["id"]))
            continue
        ready.append({"company": company, "title": title, "age": age,
                      "id": j["id"], "posted": j["posted"],
                      "new_company": hit is None})

    ready.sort(key=lambda x: (x["age"], x["company"]))

    print(f"[5] CLASSIFY: {len(ready)} READY | {len(dupes)} duplicate | {len(blocked)} rejected")
    print("-" * 78)
    if not ready:
        print("No READY candidates. Widen: --pages 4, or drop f_TPR to r604800.")
    for r in ready:
        tag = "NEW-CO" if r["new_company"] else "new-role"
        print(f"  READY {r['age']:>2}d [{tag:8}] {r['company'][:34]:34} | {r['title'][:46]:46} | {r['id']}")

    # 5b. resolve the ATS for the top candidates *before* a browser is opened.
    #     Kills the 3-navigation hop (LinkedIn -> /safety/go/ -> ATS) and proves
    #     the requisition is live. --resolve N (0 disables), default 3.
    limit = int(args[args.index("--resolve") + 1]) if "--resolve" in args else 3
    for r in ready[:limit]:
        hit = resolve_ats(r["company"], r["title"])
        if hit:
            r.update(hit)
            print(f"  ATS   {r['company'][:24]:24} -> {hit['ats']}:{hit['slug']} "
                  f"[{str(hit['job_id'])[:12]}] {hit['title'][:34]} | {hit['location'][:16]}")
        else:
            print(f"  ATS   {r['company'][:24]:24} -> not on ashby/greenhouse "
                  "(expect LinkedIn /safety/go/ hop)")

    print("-" * 78)
    print("NEXT: open the ATS url above; No Easy-Apply => never use the LinkedIn list pane")
    print(f"elapsed {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
