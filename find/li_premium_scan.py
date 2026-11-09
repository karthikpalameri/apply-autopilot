#!/usr/bin/env python3
"""li_premium_scan.py v3 — LIVE LinkedIn session scan for QA/SDET at PUBLIC product cos.
Sectors: banking/fintech + distribution/supply-chain. Logged-in browser (:9000).
Company-scoped via f_C=<id>&geoId=102713980 (Bengaluru). Usage: .venv/bin/python find/li_premium_scan.py
"""
import json
import re

from core.ctl import call_wait

GEO_BLR = "102713980"


def ctl(cmd, wait=0.0):
    """Thin local shim over the ONE socket owner (core.ctl).

    This file used to carry its own 9-line socket.create_connection loop, which is
    exactly the duplication skills/REFERENCE.md#single-source-invariant forbids:
    "Socket call has ONE owner: core.ctl.call / call_wait". The local name is kept
    so the ~20 `ctl(...)` call sites below stay readable; the wire logic does not
    live here any more.
    """
    return call_wait(cmd, wait=wait)

def company_id(slug):
    ctl({"op": "navigate", "url": f"https://www.linkedin.com/company/{slug}/"}, 3.2)
    r = ctl({"op": "eval", "js": "(() => { const m=document.documentElement.outerHTML.match(/\"(?:urn:li:company|fs_company):([0-9]+)\"/); return m? m[1] : null })()"}, 0.3)
    return r.get("result")

def scan_company(name, cid):
    url = (f"https://www.linkedin.com/jobs/search/?keywords=SDET&location=Bengaluru"
           f"&f_C={cid}&geoId={GEO_BLR}&f_TPR=r2592000")
    ctl({"op": "navigate", "url": url}, 5.5)
    r = ctl({"op": "eval", "js": """(() => {
      const cards=[...document.querySelectorAll(".job-card-container--clickable")];
      const detail=document.querySelector(".jobs-details__main-content, .jobs-search__job-details--container");
      const dt=detail?detail.innerText:"";
      const out=cards.map(c=>{
        const lines=c.innerText.split("\\n").filter(Boolean).map(x=>x.trim()).filter(Boolean);
        const title=lines.find(l=>!/with verification$/.test(l) && !/^(Job Title|Company Name)$/.test(l))||lines[0]||"";
        const ci=lines.indexOf("Company Name");
        const company=ci>=0? lines[ci+1] : (lines.find(l=>/\\S/.test(l)&&!l.includes("verification")&&!l.includes("(")&&l.length>2&&l.length<40&&l!==title)||"");
        const loc=lines.find(l=>l.includes("India")||l.includes("Bengaluru")||l.includes("Bangalore")||l.includes("Hyderabad")||l.includes("Pune")||l.includes("Chennai")||l.includes("Remote"))||"";
        const badges=lines.filter(l=>/applicant|reviewing|Promoted|Viewed|alum/i.test(l));
        return {title, company, loc, badges};
      });
      const ta=/top applicant|matches the required/i.test(dt) ? "TOP-APPLICANT" : "";
      return {n: cards.length, topApplicant: ta, cards: out};
    })()"""}, 0.3)
    res = r.get("result") or {}
    owned = [c for c in res.get("cards", []) if name.lower().split()[0] in (c.get("company") or "").lower()]
    qa = [c for c in owned if re.search(r"\b(qa|sdet|test|quality|automation)\b", c.get("title",""), re.I)]
    return res, owned, qa

TARGETS = [
    ("Intuit", "intuit"), ("PayPal", "paypal"), ("Visa", "visa"), ("Mastercard", "mastercard"),
    ("FIS", "fis"), ("Fiserv", "fiserv"), ("Temenos", "temenos"), ("SBI Cards", "sbi-card"),
    ("Paytm", "paytm"), ("Manhattan Associates", "manhattan-associates"),
    ("Walmart Global Tech", "walmart-global-tech"), ("Amazon", "amazon"), ("Zomato", "zomato"),
    ("Delhivery", "delhivery"), ("Blue Dart", "blue-dart-express"), ("SAP", "sap"), ("Oracle", "oracle"),
]

def main():
    out = []
    for name, slug in TARGETS:
        try:
            cid = company_id(slug)
            if not cid:
                print(f"✗ {name}: no id", flush=True); out.append({"company": name, "error": "no-id"}); continue
            res, owned, qa = scan_company(name, cid)
            entry = {"company": name, "id": cid, "cards_total": res.get("n", 0),
                     "owned_cards": len(owned), "qa_owned": [c for c in qa],
                     "top_applicant_panel": res.get("topApplicant", "")}
            out.append(entry)
            print(f"{'✓' if qa else '·'} {name} id={cid} total={res.get('n',0)} owned={len(owned)} QA={len(qa)} {res.get('topApplicant','')}", flush=True)
            for c in qa[:6]:
                print(f"      {c['title'][:46]} | {c['company'][:18]} | {str(c['loc'])[:26]} | {c['badges'][:1]}", flush=True)
        except Exception as e:
            print(f"✗ {name}: {e}", flush=True); out.append({"company": name, "error": str(e)})
    json.dump(out, open("config/li_premium_scan.json", "w"), indent=1)
    print("\nSaved -> config/li_premium_scan.json")

if __name__ == "__main__":
    main()
