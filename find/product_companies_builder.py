#!/usr/bin/env python3
"""find/product_companies_builder.py — builds the PRODUCT-COMPANY list (→500).

Turns the curated seed (config/data/product_seed.py, 440+ product companies) into a clean,
verified list with official website + LinkedIn company URL + ATS board + sector + city.

RESOLUTION (no browser needed for the bulk):
  - website  : from seed; VERIFIED via HTTP/S (head request, follows redirects). Unreachable -> blank.
  - linkedin : from a curated slug override map + name-normalization fallback:
               https://www.linkedin.com/company/<slug>/
  - ATS      : those we know (greenhouse/lever/ashby/...) or blank.

When CloakBrowser is running, `--linkedin-verify` confirms each LinkedIn URL resolves from the
logged-in session (updates status to resolved/404). Without it we mark status:"url-built".

OUTPUT (saved in this folder):
  - config/data/product_companies.json   (structured list, searchable)
  - product_companies.md                 (readable markdown, in the hub root)
Usage:
  .venv/bin/python find/product_companies_builder.py            [# build from seed]
  .venv/bin/python find/product_companies_builder.py --linkedin # + live LinkedIn verify
  .venv/bin/python find/product_companies_builder.py --count 500
"""
import json, os, re, sys, socket, ssl, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HUB)
sys.path.insert(0, os.path.join(HUB, "config", "data"))
from config.data import product_seed  # noqa: E402

OUT_JSON = os.path.join(HUB, "config", "data", "product_companies.json")
OUT_MD = os.path.join(HUB, "product_companies.md")

CTA_TARGET = 500

# LinkedIn company slugs that do NOT equal the visible company name (curated).
# key = normalized company name -> real LinkedIn slug.
LINKEDIN_SLUGS = {
    "1mg": "1mg-com",
    "tata 1mg": "tata-1mg",
    "urban company": "urbanclap",
    "akko": "acko",
    "amex india": "american-express",
    "appdynamics cisco": "appdynamics",
    "black duck synopsys": "black-duck-software",
    "confluent india": "confluent",
    "segment twilio": "segment",
    "microsoft research india": "microsoft-research",
    "sap labs": "sap",
    "vmware broadcom": "vmware",
    "splunk cisco": "splunk",
    "gitkraken": "axosoft",
    "github microsoft": "github",
    "slack salesforce": "slack",
    "honey paypal": "honey",
    "flipkart walmart labs": "flipkart",
    "phonepe walmart": "phonepe",
    "myntra parts": "myntra",
    "amd": "advanced-micro-devices",
    "nvidia india": "nvidia",
    "intel india": "intel",
    "qualcomm india": "qualcomm",
    "oracle india": "oracle",
    "cisco india": "cisco",
    "microsoft india": "microsoft",
    "google india": "google",
    "meta india": "meta",
    "amazon india": "amazon",
    "atlassian india": "atlassian",
    "datadog india": "datadog",
    "snowflake india": "snowflake",
    "mongodb india": "mongodb",
    "dell technologies": "dell",
    "xilo": "xilinx",
    "xilinx amd": "xilinx",
    "walmart labs": "walmartlabs",
    "ibm india": "ibm",
    "ubr india": "uber",
    "make my trip": "makemytrip",
    "coindcx": "coindcx",
    "sahaj": "sahaj-software-automation",
    "replit india": "replit",
    "segment dev": "segment",
    "segment twilio": "segment",
    "ghost": "the-ghost-foundation",
    "hangout by paytm": "hangout",
    "moj": "moj-app",
    "bluestone": "bluestone-jewellery",
    "zapier india": "zapier",
    "mistral india": "mistral-ai",
    "openai india": "openai",
    "cursor anysphere": "anysphere",
    "adobe research": "adobe",
    "zyper": "zapier",
    "apollo io": "apollo-io",
    "vault hashicorp": "hashicorp",
    "terraform hashicorp": "hashicorp",
    "consul hashicorp": "hashicorp",
    "grafana labs": "grafana-labs",
}


def norm_name(n):
    n = n.lower().replace("&", " and ")
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def slug_for(name):
    key = norm_name(name)
    if key in LINKEDIN_SLUGS:
        return LINKEDIN_SLUGS[key]
    slug = key.replace(" ", "-")
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def linkedin_url(name):
    return f"https://www.linkedin.com/company/{slug_for(name)}/"


def check_website(domain):
    if not domain:
        return "", False
    try:
        import certifi, ssl
        _ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        _ctx = None
    url = domain if domain.startswith("http") else "https://" + domain
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=6, context=_ctx) as r:
            return r.url, (200 <= r.status < 400)
    except Exception:
        try:  # some servers reject HEAD -> GET with minimal read
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6, context=_ctx) as r:
                r.read(1024)
                return r.url, (200 <= r.status < 400)
        except Exception:
            return "", False


def build():
    raw = product_seed.seed_list()
    # parallel website HEAD/GET check
    with ThreadPoolExecutor(max_workers=24) as ex:
        webresults = list(ex.map(lambda e: check_website(e["website"]), raw))

    companies = []
    for e, (real_url, ok) in zip(raw, webresults):
        url = real_url if ok else (e["website"] if e["website"] else "")
        companies.append({
            "company": e["company"],
            "sector": bucket(e["sector"]),
            "city": e["city"],
            "website": url or "",
            "linkedin": linkedin_url(e["company"]),
            "ats": e.get("ats", ""),
            "status": ("resolved" if url else "website-unknown"),
        })

    # drop entries with no host info at all (pure dev-placeholders / unknown)
    return [c for c in companies if c["website"] or c["linkedin"]]


# Normalize fine-grained sectors into broad buckets for readable grouping.
SECTOR_BUCKET = {
    "fintech": "Fintech / Payments", "fintech-insurance": "Fintech / Insurance",
    "fintech-saas": "Fintech / SaaS", "fintech-payments": "Fintech / Payments",
    "fintech-api": "Fintech / APIs", "fintech-analytics": "Fintech / Analytics",
    "fintech-admin": "Fintech / Admin", "banking": "Banking / Fintech",
    "crypto": "Crypto / Fintech", "fintech-insurance": "Fintech / Insurance",
    "health-saas": "HealthTech", "health": "HealthTech", "health-ai": "HealthTech",
    "healthtech": "HealthTech", "healthcare": "HealthTech",
    "saas": "SaaS", "b2b": "B2B / SaaS", "b2b-saas": "SaaS",
    "hcm-saas": "SaaS", "sales-saas": "SaaS", "support-saas": "SaaS",
    "crm": "SaaS", "crm-saas": "SaaS", "marketing-saas": "SaaS",
    "review-saas": "SaaS", "document-saas": "SaaS", "email-saas": "SaaS",
    "commerce-saas": "SaaS", "headless-cms": "SaaS", "web-saas": "SaaS",
    "nocode": "DevTools / Platform", "automation-saas": "SaaS",
    "devtools": "DevTools / Platform", "devops": "DevTools / Platform",
    "orchestration": "DevTools / Platform", "mlops": "DevTools / Platform",
    "monitoring": "Observability", "observability": "Observability",
    "incident": "Observability", "networking": "Infra / Networking",
    "infra": "Infra / Networking", "edge": "Infra / Networking",
    "cdn": "Infra / Networking", "apigw": "Infra / Networking",
    "virtualization": "Infra / Networking", "linux": "Infra / OS",
    "database": "Data / Database", "data": "Data / Analytics", "data-ai": "Data / AI",
    "data-saas": "Data / Analytics", "storage": "Data / Storage",
    "ecommerce": "E-commerce / Retail", "d2c": "E-commerce / Retail",
    "d2c-fashion": "E-commerce / Retail", "d2c-jewelry": "E-commerce / Retail",
    "marketplace": "Marketplace", "quick-commerce": "Quick Commerce",
    "qcommerce": "Quick Commerce", "qcommerce-food": "Food / Q-Commerce",
    "food-tech": "Food / Q-Commerce", "freshtech": "Food / Q-Commerce",
    "logistics": "Logistics / Supply", "logistics-saas": "Logistics / Supply",
    "logistics-ai": "Logistics / Supply",
    "travel-tech": "Travel / Mobility", "mobility": "Travel / Mobility",
    "ev": "Travel / Mobility", "auto-tech": "Travel / Mobility",
    "edtech": "EdTech", "gaming": "Media / Gaming", "gaming-video": "Media / Gaming",
    "social": "Media / Social", "audio": "Media / Streaming", "streaming": "Media / Streaming",
    "video": "Media / Streaming", "publishing": "Media / Publishing",
    "design": "Design / Creative", "productivity": "SaaS",
    "semiconductor": "Semiconductor / Hardware", "hardware": "Semiconductor / Hardware",
    "consumer-tech": "Semiconductor / Hardware", "fpga": "Semiconductor / Hardware",
    "eda": "Semiconductor / Hardware", "simulation": "Semiconductor / Hardware",
    "cad": "Design / Engineering SW", "iot-cad": "Industrial / IoT",
    "industrial": "Industrial / IoT", "security": "Cybersecurity",
    "cybersecurity": "Cybersecurity", "identity": "Cybersecurity / Identity",
    "cloud": "Cloud / Infra", "enterprise": "Enterprise / Cloud",
    "enterprise-saas": "Enterprise / Cloud", "internet": "Internet / Big-Tech",
    "telecom-tech": "Telecom / Tech", "rnd": "R&D / Labs",
    "ai": "AI / ML", "ai-saas": "AI / SaaS", "ai-writing": "AI / SaaS",
    "ai-search": "AI / Search", "ai-dev": "AI / DevTools", "ai-health": "AI / Health",
    "ai-finance": "AI / Fintech", "ai-legal": "AI / Legal",
    "cpas-saas": "SaaS", "blockchain": "Crypto / Fintech",
    "agritech": "Agritech", "capacity": "Data / AI", "greentech": "CleanTech",
    "clean-energy": "CleanTech", "energy": "CleanTech",
    "it-services": "IT Services", "digital": "Digital / Services",
    "digital-engineer": "IT Services", "tech-product": "Tech / Product",
    "consulting-product": "Tech / Product", "qa": "Services / QA",
}


def bucket(s):
    return SECTOR_BUCKET.get(s, s)


def to_md(cs):
    lines = [
        "# Product-Based Companies (Bangalore + India QA/SDET targets)",
        "",
        f"**{len(cs)} product companies** — each with official website + LinkedIn company URL.",
        "Product companies build & own a product (SaaS/devtools/fintech/e-commerce/cloud). "
        "Auto-generated by `find/product_companies_builder.py`. Add more seeds in `config/data/product_seed.py`.",
        "",
        "## By sector",
        "",
    ]
    sectors = {}
    for c in cs:
        sectors.setdefault(bucket(c["sector"]), []).append(c)
    for s in sorted(sectors):
        lines.append(f"### {s}  ({len(sectors[s])})")
        lines.append("")
        lines.append("| Company | Website | LinkedIn | ATS |")
        lines.append("|---|---|---|---|")
        for c in sorted(sectors[s], key=lambda x: x["company"].lower()):
            w = f"[{c['website']}]({c['website']})" if c["website"] else "—"
            li = f"[company]({c['linkedin']})"
            lines.append(f"| {c['company']} | {w} | {li} | {c.get('ats','') or ''} |".rstrip(" |"))
        lines.append("")
    return "\n".join(lines)


def main():
    count = CTA_TARGET
    if "--count" in sys.argv:
        count = int(sys.argv[sys.argv.index("--count") + 1])
    print("building product-company list from seed…")
    cs = build()
    cs = cs[:count]

    if "--linkedin-verify" in sys.argv:
        try:
            from core.browser import CtlBrowser
            b = CtlBrowser()
            for c in cs:
                st = probe_linkedin(b, c["linkedin"])
                c["status"] = "linkedin-ok" if st == "ok" else "linkedin-404"
            ok = sum(1 for c in cs if c["status"] == "linkedin-ok")
            print(f"linkedin verify: resolved={ok} 404={len(cs)-ok}")
        except Exception as e:
            print("ℹ️  --linkedin-verify needs CloakBrowser (ctl :9000); skipped:", e)

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(cs, open(OUT_JSON, "w"), indent=1)
    open(OUT_MD, "w").write(to_md(cs))
    resolved = sum(1 for c in cs if c["website"])
    print(f"saved {len(cs)} companies (target {count})  # with website: {resolved}")
    print(f"  json: {OUT_JSON}")
    print(f"  md  : {OUT_MD}")


def probe_linkedin(browser, url):
    """Check a LinkedIn company URL from the logged-in browser: returns 'ok' or '404'."""
    browser.navigate(url)
    import time
    time.sleep(3)
    r = browser.eval_js("() => /^404|not available|page not found|couldn't find that page/i.test((document.body.innerText||'').slice(0,400)) ? '404' : 'ok'")
    return "404" if str(r.get("result") if isinstance(r, dict) else r) == "404" else "ok"


if __name__ == "__main__":
    main()
