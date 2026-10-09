#!/usr/bin/env python3
"""verify.py — FAST combined DOM+OCR page verifier. Reads DOM (instant) + screenshot OCR, compares.
Usage: verify.py [tag] — prints structured state. ~2s.
"""
import json, socket, subprocess, sys

def ctl(cmd, timeout=15):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    b = b""
    while not b.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        b += c
    s.close()
    return json.loads(b.decode())

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
try:
    ocr = subprocess.run(["tesseract", p, "-", "--psm", "6"], capture_output=True, text=True, timeout=10).stdout
    ocr_snip = ocr.replace("\n", " | ")[:400]
except Exception:
    ocr_snip = "(ocr fail)"
print("STEP:", st.get("step"), "| DLG:", st.get("dlg"), "| ERRORS:", st.get("errs"))
print("URL:", st.get("url"))
print("BTNS:", st.get("btns"))
for v in st.get("vals", []):
    print(f"  {v['n']:26s} = {v['v']!r}")
print("OCR:", ocr_snip)
