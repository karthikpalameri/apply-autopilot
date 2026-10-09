#!/usr/bin/env python3
"""find/naukri_listed.py — search Naukri QA jobs at LISTED product companies (via MCP browser)."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import McpBrowser

b = McpBrowser()
b._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name":"naukri","version":"0.1"}})
def snap(): return b.snapshot().get("text","")

LISTED = re.compile(r"cisco|microsoft|adobe|sap|servicenow|netapp|nutanix|oracle|ibm|dell|honeywell|siemens|bosch|swiggy|zomato|delhivery|makemytrip|walmart|shopify|uber|twilio|datadog|crowdstrike|snowflake|zscaler|paypal|ebay|atlassian|vmware|qualcomm|amazon|flipkart|myntra|paytm|freshworks|philips|samsung|intel|hp\b", re.I)

urls = [
  "https://www.naukri.com/sdet-jobs-in-bangalore",
  "https://www.naukri.com/quality-assurance-jobs-in-bangalore",
]
for u in urls:
    b.navigate(u); time.sleep(5)
    t = snap()
    # extract job titles + companies from snapshot (Naukri lists: title, company, exp)
    jobs = re.findall(r'link "([^"]{5,70})"[^\[]*\[ref=(\w+)\]', t)
    print(f"\n=== {u.split('/')[-1]} — {len(jobs)} links ===")
    for title, ref in jobs[:40]:
        if LISTED.search(title):
            print(f"  [{ref}] {title[:60]}")
