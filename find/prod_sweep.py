#!/usr/bin/env python3
"""prod_sweep.py — Bangalore product companies -> ATS API check for QA/SDET openings (fast, batch)."""
import json, urllib.request, re, sys


def _ctx():
    try:
        import certifi, ssl
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def get(url, t=5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(req, timeout=t, context=_ctx()).read())
    except Exception:
        return None

QA = re.compile(r"\b(qa|sdet|quality|test|automation)\b", re.I)
NON = re.compile(r"\b(recruiter|trainer|sales|marketing|frontend|backend|data scientist|scientist|security engineer|hr|talent|firmware|hardware|electrical|manufacturing|soc|silicon|verification)\b", re.I)

# Bangalore product companies + their ATS board slugs (Greenhouse/Lever/Ashby)
GH = ["freshworks","chargebee","postman","dream11","zoho","zepto","groww","jupiter","meesho","swiggy",
      "moengage","hasura","cred","practo","docusign","mckesson","illumina","halliburton","circana",
      "lightandwonder","n-able","hackerrank","yugabyte","parspec","druva","browserstack","unbxd","clevertap",
      "wingify","contentstack","zoho","razorpay","phonepe","flipkart","myntra","netapp","amd","nvidia","oracle","sap"]
LEV = ["freshworks","chargebee","postman","dream11","zoho","zepto","groww","jupiter","meesho","swiggy",
       "moengage","hasura","cred","practo","chargebee","khatabook","medibuddy","razorpay"]
ASH = ["postman","chargebee","freshworks","dream11","groww","zepto","jupiter","meesho","swiggy",
       "instawork","khatabook","medibuddy","zluri","sprinto","highlevel","kapiva"]

found = []
for b in GH:
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs")
    if d and "jobs" in d:
        for j in d["jobs"]:
            t = j.get("title", ""); loc = (j.get("location") or {}).get("name", "")
            if QA.search(t) and not NON.search(t) and re.search(r"bangal|india|bengaluru", loc, re.I):
                found.append(("GH", b, j.get("id"), t[:44], loc[:20], j.get("absolute_url","")[:70]))
for b in LEV:
    d = get(f"https://api.lever.co/v0/postings/{b}?mode=json")
    if isinstance(d, list):
        for j in d:
            t = j.get("text", ""); loc = j.get("categories", {}).get("location", "")
            if QA.search(t) and not NON.search(t) and re.search(r"bangal|india|bengaluru", loc, re.I):
                found.append(("LEV", b, j.get("id","")[:10], t[:44], loc[:20], j.get("hostedUrl","")[:70]))
for b in ASH:
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{b}")
    if d and "jobs" in d:
        for j in d["jobs"]:
            t = j.get("title",""); loc = j.get("location") or ""
            if QA.search(t) and not NON.search(t) and re.search(r"bangal|india|bengaluru", loc, re.I):
                found.append(("ASH", b, "", t[:44], loc[:20], j.get("jobUrl","")[:70]))
print(f"QA OPENINGS at Bangalore product companies: {len(found)}")
for f in found:
    print(f"{f[0]:4s} {f[1][:14]:14s} {f[3]:44s} | {f[4]:18s} | {f[5][-45:]}")
