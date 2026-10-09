import os
#!/usr/bin/env python3
"""ashby_apply.py <url> — Ashby form + CapSolver reCAPTCHA v3 token injection."""
import json, re, socket, sys, time, random, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.answers import A, RESUME
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK
from capsolver import solve_recaptcha_v3

def ctl(cmd, timeout=150):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    return json.loads(buf.decode())

def main():
    RESUME_PICK()
    url = sys.argv[1]
    print(f"🚀 {url}", flush=True)
    ctl({"op": "navigate", "url": url})
    time.sleep(4)
    # open the Application tab (Ashby)
    ctl({"op": "eval", "js": "() => { const el = document.querySelector('.ashby-job-posting-right-pane-application-tab'); if (el) el.click(); return 1; }"})
    time.sleep(4)

    # extract fields with labels
    r = ctl({"op": "eval", "js": "() => { const out = []; document.querySelectorAll('input[name], textarea[name], select[name]').forEach(e => { if (!e.offsetParent) return; let q=''; if (e.labels && e.labels.length) q = e.labels[0].innerText; else { let n=e; for(let i=0;i<5&&n;i++){ n=n.parentElement; if(!n) break; const p=n.previousElementSibling; if(p&&p.innerText){ const t=p.innerText.replace(/\\s+/g,' ').trim(); if(t&&t.length<220){q=t;break;} } } } out.push({name: e.name, tag: e.tagName, q: q.replace(/\\s+/g,' ').trim().slice(0,90)}); }); return JSON.stringify(out); }"})
    fields = json.loads(r.get("result"))
    print(f"   {len(fields)} fields", flush=True)

    # fill by label match
    def answer(q):
        ql = q.lower()
        if ql.startswith("name"): return A["full_name"]
        if "email" in ql: return A["email"]
        if "years of experience" in ql: return "8"
        if "hands-on experience" in ql: return "Yes - Selenium WebDriver, Appium (Android/iOS), RestAssured, TestNG, Cucumber, Java."
        if "cloud platforms" in ql: return "Yes - AWS (Lambda, DynamoDB, CloudWatch) and Kubernetes."
        if "telecommunications" in ql or "wireless" in ql: return "No"
        if "ai tools" in ql: return "Yes - I use AI-assisted testing (Appium AI Plugin, OpenCV) daily."
        if "located" in ql or "50-kilom" in ql: return "Yes - based in Bengaluru"
        if "notice period" in ql: return "Immediate (serving notice — last working day <your last working day>)"
        if "current ctc" in ql or "current compensation" in ql or "current salary" in ql: return A["ctc"]
        if "salary" in ql or "expected" in ql or "ctc" in ql: return "<expected CTC>"
        return None

    filled = 0
    for f in fields:
        ans = answer(f["q"])
        if ans and not f["name"].startswith("_systemfield"):
            r = ctl({"op": "hfill", "by": "name", "key": f["name"], "value": ans})
            if r.get("ok"):
                filled += 1
                print(f"  ✍️ [{f['q'][:44]}...] = {str(ans)[:25]}", flush=True)
            time.sleep(random.uniform(0.6, 1.4))
    # system fields (name/email have ids)
    for nm, val in [("_systemfield_name", A["full_name"]), ("_systemfield_email", A["email"])]:
        r = ctl({"op": "hfill", "by": "name", "key": nm, "value": val})
        if r.get("ok"): filled += 1; print(f"  ✍️ {nm}", flush=True)
        time.sleep(random.uniform(0.6, 1.2))

    r = ctl({"op": "upload_cdp", "path": BEFORE_UPLOAD()})
    print(f"📎 resume: {'uploaded' if r.get('ok') else r.get('error')} | filled {filled}", flush=True)
    if r.get('ok'): RESUME_POST()

    # --- CapSolver reCAPTCHA v3 ---
    r = ctl({"op": "eval", "js": "() => { const f = [...document.querySelectorAll('iframe')].find(x => x.src.includes('recaptcha')); const m = f ? f.src.match(/[?&]k=([^&]+)/) : null; const ta = document.querySelector('textarea[name=g-recaptcha-response]'); return JSON.stringify({sitekey: m ? m[1] : null, hasTextarea: !!ta}); }"})
    info = json.loads(r.get("result"))
    print("recaptcha:", info, flush=True)
    if info.get("sitekey"):
        tok, err = solve_recaptcha_v3(info["sitekey"], url, score=0.9)
        if tok:
            print(f"✅ token ({len(tok)} chars) — injecting", flush=True)
            ctl({"op": "eval", "js": f"() => {{ const ta = document.querySelector('textarea[name=g-recaptcha-response]'); if (!ta) return 'no-ta'; const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set; setter.call(ta, '{tok}'); ta.dispatchEvent(new Event('input', {{bubbles:true}})); ta.dispatchEvent(new Event('change', {{bubbles:true}})); return 'injected'; }}"})
            time.sleep(2)
        else:
            print(f"❌ capsolver: {err}", flush=True)
    # submit
    r = ctl({"op": "eval", "js": "() => { const b = [...document.querySelectorAll('button')].find(x => /submit application/i.test((x.innerText||'').trim())); if (!b) return 'no-btn'; b.scrollIntoView({block:'center'}); b.click(); return 'clicked'; }"})
    print("submit:", r.get("result"), flush=True)
    time.sleep(10)
    body = ctl({"op": "bodytext", "max": 500})
    txt = body.get("text") or ""
    print("RESULT:", "SUCCESS" if ("flagged" not in txt and "couldn't submit" not in txt and len(txt) > 50) else "CHECK:", txt[:200], flush=True)

main()
