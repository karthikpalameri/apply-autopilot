#!/usr/bin/env python3
"""core/ats_boards.py — ONE owner for ATS board URLs, discovery and scanning.

Before this module the board matrix was written three times (find/ats_resolve.py
BOARDS, find/listed_sweep.py GH/LEV/ASH, find/prod_sweep.py) and each of them
resolved slugs a different way: ats_resolve guessed a slug from the company NAME
only, which missed every company whose slug is not its name (BrowserStack is
`browserstack` on Greenhouse but `Browserstack` in the list, Cred is `cred`,
Postman is `postman`...). Result: 47/500 boards sweepable, 453 invisible.

Discovery order here is cheapest-signal-first:
  1. known   — slug already stored on the company record
  2. careers — fetch the company's OWN careers page and read the embed
               (gh_jid= / jobs.lever.co/<slug> / jobs.ashbyhq.com/<slug>).
               This is the authoritative signal and needs no guessing.
  3. guess   — name variants, as a last resort (legacy ats_resolve behaviour).

Two identity gates apply to EVERY candidate before a slug is stored:
  EXISTS   the board API returns at least one job
  INDIA    at least one of those jobs is in India (proves it is the Indian
           entity, not a same-named foreign company — see ats_resolve's note
           about greenhouse/slice returning 22 Macedonian jobs).
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from core.fetch import fetch_many, get_json, post_json

WORKABLE_BODY = {"query": "", "location": [], "department": [], "worktype": [],
                 "remote": [], "page": 1}

BOARDS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
    # workday: slug is "tenant/wdN/site", e.g. browserstack/wd3/External
    "workday": "https://{slug}/wday/cxs/{slug}/jobs",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{slug}",
    "recruitee": "https://{slug}.recruitee.com/api/offers/",
}

# Providers whose JSON shape is flat-enough to scan the same way.
SCANNABLE = ("greenhouse", "lever", "ashby", "smartrecruiters", "workable", "keka", "recruitee")

# workable's widget endpoint is a POST, so it needs its own fetch.
WORKABLE_POST = "https://apply.workable.com/api/v3/accounts/{slug}/jobs"

INDIA = re.compile(
    r"ind(ia|ian)\b|bengaluru|bangalore|hyderabad|chennai|pune|mumbai|gurgaon|gurugram|"
    r"noida|delhi|kolkata|ahmedabad|jaipur|kochi|trivandrum|indore|coimbatore|chandigarh|"
    r"remote[\s\-(]*india", re.I)

# Probe only these. Measured over the 500-list: /careers carries the embed at almost
# every company that has one, and racing 8 paths cost 8x the requests for the same
# result. Two paths, not eight.
CAREER_PATHS = ("/careers", "/jobs")

# plain-substring prefilter per provider: if absent, skip the regex entirely.
# A regex search over a 1MB page is not free (PhonePe's took 8.5s); `in` is O(n)
# and rejects the ~90% of career pages that embed no ATS at all.
ATS_PREFILTER = {
    "greenhouse": ".greenhouse.io/",
    "lever": ".lever.co/",
    "ashby": ".ashbyhq.com/",
    "workable": ".workable.com/",
    "smartrecruiters": ".smartrecruiters.com/",
    "workday": ".myworkdayjobs.com/",
    "keka": ".keka.com/careers",
    "recruitee": ".recruitee.com",
}

EMBED = (
    ("greenhouse", re.compile(r"(?:boards|job-boards)\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_-]+)", re.I)),
    ("lever", re.compile(r"jobs\.(?:eu\.)?lever\.co/([a-z0-9_-]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([a-z0-9_.-]+)", re.I)),
    ("workable", re.compile(r"apply\.workable\.com/([a-z0-9_-]+)", re.I)),
    ("smartrecruiters", re.compile(r"jobs\.smartrecruiters\.com/([a-z0-9_-]+)", re.I)),
    # workday tenant is in the host: <tenant>.wdN.myworkdayjobs.com/<site>
    ("workday", re.compile(r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)", re.I)),
    # keka (very common in India): <tenant>.keka.com/careers
    ("keka", re.compile(r"([a-z0-9-]+)\.keka\.com/careers", re.I)),
    ("recruitee", re.compile(r"([a-z0-9-]+)\.recruitee\.com", re.I)),
)


def _norm(name):
    base = re.sub(r"[^A-Za-z0-9 ]+", " ", name or "").strip().lower()
    return base.split()


def name_variants(name):
    """Slugs worth trying straight from the name."""
    words = _norm(name)
    if not words:
        return []
    out = {"".join(words), "-".join(words), words[0]}
    if len(words) > 1:
        out.add("".join(words[:2]))
        out.add("-".join(words[:2]))
    return sorted(s for s in out if s and len(s) > 1)


def host_slug(website):
    """'https://www.browserstack.com/' -> 'browserstack' (brand token from the domain)."""
    if not website:
        return []
    m = re.search(r"https?://([^/]+)", website)
    if not m:
        return []
    host = m.group(1).lower()
    host = re.sub(r"^(www|careers|jobs|apply|about|in|en)\.", "", host)
    label = host.split(".")[0]
    if label in ("", "www", "app", "go"):
        return []
    # browserstack from browserstack.com ; slice from slice.bank.in
    return [label, label.replace("-", "")]


def board(provider, slug, timeout=5):
    """Return the board's job list, or None when the slug does not exist."""
    if provider == "keka":
        return keka_jobs(slug, timeout)
    if provider == "workable":
        data = post_json(WORKABLE_POST.format(slug=slug), WORKABLE_BODY, timeout)
        return (data or {}).get("results") if isinstance(data, dict) else None
    url = BOARDS[provider].format(slug=slug)
    data = get_json(url, timeout=timeout)
    if provider == "lever":
        return data if isinstance(data, list) else None
    if provider == "smartrecruiters":
        return (data or {}).get("content") if isinstance(data, dict) else None
    if provider == "recruitee":
        return (data or {}).get("offers") if isinstance(data, dict) else None
    if isinstance(data, dict) and isinstance(data.get("jobs"), list):
        return data["jobs"]
    return None


def keka_jobs(tenant, timeout=8):
    """Keka renders its job board client-side from a JS template, so the jobslist
    endpoint returns NO job data over HTTP. We therefore cannot enumerate a Keka
    board statically. Return None ("not scannable") instead of inventing titles —
    scanning these needs a browser, and that is the caller's decision to make."""
    return None


def job_location(provider, job):
    if provider == "lever":
        return (job.get("categories") or {}).get("location") or ""
    if provider == "ashby":
        loc = job.get("location") or job.get("secondaryLocations") or ""
        return " ".join(str(x) for x in loc) if isinstance(loc, list) else str(loc)
    if provider == "smartrecruiters":
        loc = job.get("location") or {}
        return " ".join(str(loc.get(k) or "") for k in ("city", "region", "country"))
    if provider == "workable":
        return ", ".join(str(x) for x in (job.get("city"), job.get("country")) if x)
    if provider == "recruitee":
        return job.get("location") or ""
    if provider == "keka":
        return job.get("location") or "India"
    return (job.get("location") or {}).get("name") or ""


def job_title(job):
    return job.get("text") or job.get("title") or job.get("name") or ""


def job_url(provider, job, slug=""):
    """Public apply URL for one posting. `slug` is needed by providers whose URL
    carries the company name; omitting it produced slug-less links that looked like
    different jobs and could not be opened."""
    if provider == "lever":
        return job.get("hostedUrl") or ""
    if provider == "ashby":
        return job.get("jobUrl") or ""
    if provider == "smartrecruiters":
        jid = job.get("id", "")
        return f"https://jobs.smartrecruiters.com/{slug}/{jid}" if slug else \
               f"https://jobs.smartrecruiters.com/{jid}"
    if provider == "workable":
        return job.get("url") or job.get("shortlink") or ""
    if provider == "recruitee":
        return job.get("careers_url") or ""
    if provider == "keka":
        return job.get("jobUrl") or ""
    return job.get("absolute_url") or ""


def verify(provider, slug):
    """(ok, n_jobs, reason) — board must exist AND have an India posting."""
    jobs = board(provider, slug)
    if not jobs:
        return False, 0, "no such board"
    locs = [job_location(provider, j) for j in jobs]
    locs = [l for l in locs if l]
    india = [l for l in locs if INDIA.search(l)]
    if not india:
        return False, len(jobs), f"exists ({len(jobs)} jobs) but no India location: {locs[:2]}"
    return True, len(jobs), f"{len(india)}/{len(jobs)} India (e.g. {india[0][:34]})"


def probe_websites(companies, timeout=2.0, deadline=18.0):
    """[(company, website)] -> {company: [(provider, slug), ...]}. ONE bounded batch.

    Every website is probed in a single event loop instead of spawning a thread pool
    per company, and the whole batch shares one wall-clock deadline. This is the
    difference between 242s (threads parked on dead domains, 0 boards found) and a
    few seconds: 410 companies x 2 paths = 820 GETs, all abandoned at `deadline`.
    """
    urls, owner = [], {}
    for company, website in companies:
        if not website:
            continue
        base = (website if website.startswith("http") else "https://" + website).rstrip("/")
        for path in CAREER_PATHS:
            urls.append(base + path)
            owner[base + path] = company

    pages = fetch_many(urls, timeout=timeout, deadline=deadline)

    out = {}
    for url, html in pages.items():
        found = _embeds(html)
        if found:
            company = owner[url]
            merged = out.setdefault(company, [])
            for pair in found:
                if pair not in merged:
                    merged.append(pair)
    return out


def _embeds(html):
    """[(provider, slug)] found in one page's markup. Substring prefilter first:
    a regex over a 1MB page is not free (PhonePe's took 8.5s), `in` is O(n) and
    rejects the pages that embed no ATS at all."""
    found = []
    low = html.lower()
    for prov, rx in EMBED:
        if ATS_PREFILTER[prov] not in low:
            continue
        m = rx.search(html)
        if not m:
            continue
        if prov == "workday":
            tenant, node, site = m.group(1).lower(), m.group(2).lower(), m.group(3)
            found.append((prov, f"{tenant}.{node}.myworkdayjobs.com/{site}"))
            continue
        slug = m.group(1).lower() if m.groups() else None
        if slug and slug not in ("embed", "job_board"):
            found.append((prov, slug))
    return found


def scrape_careers(website, timeout=2.0, deadline=6.0):
    """One company's careers page -> [(provider, slug), ...].

    Delegates to probe_websites so there is exactly one implementation. Kept for the
    single-company callers (`--dry-run SomeCompany`); batch callers should use
    probe_websites directly and share one deadline across every company.
    """
    got = probe_websites([("_", website)], timeout=timeout, deadline=deadline)
    return got.get("_", [])


def _dedupe(pairs):
    seen, out = set(), []
    for p in pairs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def candidates(company, website=""):
    """Every (provider, slug) worth asking about, cheapest signal first."""
    out = []
    for prov, slug in scrape_careers(website):
        if prov in BOARDS:
            out.append((prov, slug))
    for slug in host_slug(website) + name_variants(company):
        for prov in SCANNABLE:
            out.append((prov, slug))
    return _dedupe(out)


def scan(companies, role_rx, exclude_rx, loc_rx):
    """Concurrent board scan -> [(company, provider, title, location, url)]. One owner."""
    def one(c):
        prov, slug = c.get("ats"), c.get("ats_slug")
        if prov not in SCANNABLE or not slug:
            return []
        jobs = board(prov, slug, timeout=8) or []
        rows = []
        for j in jobs:
            title = job_title(j)
            loc = job_location(prov, j)
            if role_rx.search(title) and not exclude_rx.search(title) and loc_rx.search(loc or ""):
                rows.append((c["company"], prov, title[:52], (loc or "")[:24],
                             job_url(prov, j, slug)))
        return rows

    found = []
    with ThreadPoolExecutor(max_workers=32) as ex:
        for r in ex.map(one, companies):
            found.extend(r)
    return found


def scan_slugs(provider_slugs, role_rx, exclude_rx, loc_rx=INDIA):
    """{provider: [slug]} -> (n_boards, rows). The one entry point for slug-list sweeps.

    `find/deep_sweep.py` and `find/deep_sweep2.py` differ ONLY in their curated slug
    sets; their build-scan-print body was identical (jscpd flagged 3 clones). Keeping
    the shape here means a new provider or filter fix lands once.
    """
    boards = [{"company": s, "ats": p, "ats_slug": s}
              for p, slugs in provider_slugs.items() for s in dict.fromkeys(slugs)]
    return len(boards), scan(boards, role_rx, exclude_rx, loc_rx)


def format_found(found):
    """Shared one-line-per-role report for the slug-list sweeps."""
    return [f"{prov[:4]:4s} {company[:16]:16s} {title[:46]:46s} | {loc[:22]:22s} | {url[-52:]}"
            for company, prov, title, loc, url in sorted(found)]


if __name__ == "__main__":
    print(f"providers: {', '.join(BOARDS)}", file=sys.stderr)
