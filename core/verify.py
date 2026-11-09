#!/usr/bin/env python3
"""verify.py — FAST combined DOM+OCR page verifier. Reads DOM (instant) + screenshot OCR, compares.
Usage: verify.py [tag] — prints structured state. ~2s.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ctl import call as ctl  # single owner (:9000 socket) — DRY
from core.ocr import available as ocr_available, read as ocr  # single owner (tesseract)
from core.hard_assert import POSITIVE  # single owner (proof patterns) — DRY
from core.decide import proof_status  # single owner (evidence -> ledger status)

def dom():
    """One DOM eval: step, visible text, field values, errors, buttons, url."""
    js = """() => {
      const t = document.body.innerText.replace(/\\s+/g,' ');
      const m = t.match(/(\\d+)\\/(\\d+)\\s*pages/);
      const art = [...document.querySelectorAll('article')].find(a=>/Apply to/.test(a.innerText)) || document.body;
      const vals = [...art.querySelectorAll('input:not([type=hidden]):not([type=file]), select, textarea')]
        .filter(e=>e.offsetParent).slice(0,18).map(e=>({n:(e.name||e.id||'').slice(0,24),v:(e.value||'').slice(0,16)}));
      const errs = [...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent&&/this field is required/i.test((e.innerText||''))).length;
      const btns = [...document.querySelectorAll('button')].filter(b=>b.offsetParent).map(b=>(b.innerText||'').trim().slice(0,16)).filter(x=>/next|review|submit|apply|back/i.test(x));
      return JSON.stringify({url: location.href.slice(0,70), step: m?m[1]+'/'+m[2]:'?', dlg:/Apply to/.test(t),
        errs, vals, btns:[...new Set(btns)].slice(0,6)});
    }"""
    return json.loads(ctl({"op": "eval", "js": js}).get("result") or "{}")

tag = sys.argv[1] if len(sys.argv) > 1 else "v"
st = dom()
ctl({"op": "snap", "name": f"v_{tag}", "full": False})
p = f"logs/v_{tag}.png"
ocr_text = ocr(p)
ocr_snip = ocr_text.replace("\n", " | ")[:400] if ocr_text else (
    "(OCR unavailable — install tesseract; DOM state above is still valid)"
    if not ocr_available() else "(no OCR text)")
print("STEP:", st.get("step"), "| DLG:", st.get("dlg"), "| ERRORS:", st.get("errs"))
print("URL:", st.get("url"))
print("BTNS:", st.get("btns"))
for v in st.get("vals", []):
    print(f"  {v['n']:26s} = {v['v']!r}")
print("OCR:", ocr_snip)

# Typed proof classification: hard_assert owns the POSITIVE patterns, decide owns
# the evidence -> status mapping. No positive message read = blocked (never infer).
found = ""
for pat in POSITIVE:
    m = re.search(pat, ocr_text, re.I)
    if m:
        found = m.group(0)
        break
print("STATUS:", proof_status(found))
