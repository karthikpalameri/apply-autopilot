#!/usr/bin/env python3
"""listed_sweep.py — QA openings at PUBLICLY LISTED product companies (NASDAQ/NYSE/NSE, revenue-backed).
Concurrent ATS API checks + fast timeouts. Usage: .venv/bin/python find/listed_sweep.py"""
import json, urllib.request, re, sys
from concurrent.futures import ThreadPoolExecutor


def _ctx():
    try:
        import certifi, ssl
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def get(url, t=3):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(req, timeout=t, context=_ctx()).read())
    except Exception:
        return None

QA = re.compile(r"\b(qa|sdet|quality|test|automation)\b", re.I)
NON = re.compile(r"\b(recruiter|trainer|sales|marketing|data scientist|scientist|security engineer|hr|talent|firmware|hardware|electrical|manufacturing|soc|silicon|verification|analyst - |tax|audit|credit)\b", re.I)
LOC = re.compile(r"bangal|bengaluru|india", re.I)

# Listed product cos (ticker) -> ATS board
GH = ["freshworks","snowflakecomputing","crowdstrike","twilio","uber","datadoghq","cloudflare","zscaler",
      "n-able","gitlab","servicenow","netskope","cohesity","yugabyte","oracle","adobe","atlassian","instructure"]
LEV = ["swiggy","zomato","delhivery","makemytrip","netapp","cisco","microsoft","sap","adobe","service-now"]
ASH = ["paloaltonetworks","zscaler","crowdstrike","servicenow","datadog","vercel"]

found = []

def gh_check(b):
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs")
    out = []
    if d and "jobs" in d:
        for j in d["jobs"]:
            t = j.get("title", ""); loc = (j.get("location") or {}).get("name", "")
            if QA.search(t) and not NON.search(t) and LOC.search(loc):
                out.append(("GH", b, j.get("id"), t[:42], loc[:22], j.get("absolute_url","")[:66]))
    return out

def lev_check(b):
    d = get(f"https://api.lever.co/v0/postings/{b}?mode=json")
    out = []
    if isinstance(d, list):
        for j in d:
            t = j.get("text", ""); loc = j.get("categories", {}).get("location", "")
            if QA.search(t) and not NON.search(t) and LOC.search(loc):
                out.append(("LEV", b, j.get("id","")[:10], t[:42], loc[:22], j.get("hostedUrl","")[:66]))
    return out

def ash_check(b):
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{b}")
    out = []
    if d and "jobs" in d:
        for j in d["jobs"]:
            t = j.get("title",""); loc = j.get("location") or ""
            if QA.search(t) and not NON.search(t) and LOC.search(loc):
                out.append(("ASH", b, "", t[:42], loc[:22], j.get("jobUrl","")[:66]))
    return out

with ThreadPoolExecutor(max_workers=12) as ex:
    for fn, boards in ((gh_check, GH), (lev_check, LEV), (ash_check, ASH)):
        for res in ex.map(fn, boards):
            found.extend(res)

print(f"QA OPENINGS @ LISTED PRODUCT COS: {len(found)}")
for f in found:
    print(f"{f[0]:4s} {f[1][:16]:16s} {f[3]:42s} | {f[4]:20s} | {f[5][-44:]}")
