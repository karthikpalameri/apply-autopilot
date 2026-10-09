#!/usr/bin/env python3
"""find/product_lookup.py — query the 500-product-company list.

Usage:
  .venv/bin/python find/product_lookup.py                # count + sectors
  .venv/bin/python find/product_lookup.py fintech       # companies in that sector (substring)
  .venv/bin/python find/product_lookup.py --website zapier  # find by company-name substring
  .venv/bin/python find/product_lookup.py --linkedin zapier # find LinkedIn URL by name
"""
import json, os, sys

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HUB, "config", "data", "product_companies.json")


def load():
    return json.load(open(PATH))


def main():
    cs = load()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    web = "--website" in sys.argv
    li = "--linkedin" in sys.argv

    if web or li:
        q = args[0].lower() if args else ""
        hits = [c for c in cs if q in c["company"].lower() or q in c.get("website", "").lower()]
        for c in hits[:40]:
            if li:
                print(f"{c['company']}\t{c['linkedin']}")
            else:
                print(f"{c['company']}\t{c['website']}\t{c['sector']}")
        print(f"({len(hits)} hit(s))")
        return

    if args:
        q = args[0].lower()
        hits = [c for c in cs if q in (c.get("sector") or "").lower() or q in c["company"].lower()]
        print(f"sector/name '{q}': {len(hits)} companies")
        for c in hits[:50]:
            print(f"  {c['company']:34s} {c.get('website',''):38s} {c.get('sector','')}")
        return

    sectors = {}
    for c in cs:
        sectors.setdefault(c["sector"], 0)
        sectors[c["sector"]] += 1
    print(f"total product companies: {len(cs)}")
    for s in sorted(sectors, key=lambda x: -sectors[x]):
        print(f"  {s:34s} {sectors[s]}")


if __name__ == "__main__":
    main()
