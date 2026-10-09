#!/usr/bin/env python3
"""generic_form_fill.py <job_url> — Greenhouse driver, LABEL-driven (any job).
Finds fields by question label, not ID. Portal-safe react-selects, real typing, consents."""
import json, socket, sys, time, re, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.answers import A, RESUME
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK

def ctl(cmd, timeout=60):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    return json.loads(buf.decode())

def ev(js): return ctl({"op": "eval", "js": js}).get("result") or ""

def typ(text):
    for chunk in [text[i:i+30] for i in range(0, len(text), 30)]:
        ctl({"op": "htype", "value": chunk}); time.sleep(0.35)

def find_control(label_re):
    """Find a visible form control whose question label matches. Returns input id."""
    r = ev(f"""() => {{
      const re = new RegExp({json.dumps(label_re)}, 'i');
      for (const f of document.querySelectorAll('.field, .select__container, [class*=question]')) {{
        const t = (f.innerText||'').replace(/\\s+/g,' ').trim();
        if (re.test(t)) {{
          const inp = f.querySelector('input:not([type=hidden]):not([type=file]), select, textarea');
          if (inp && inp.offsetParent) return inp.id || inp.name;
        }}
      }}
      return '';
    }}""")
    return r

def sel_pick(label_re, match):
    qid = find_control(label_re)
    if not qid:
        print(f"  ⚠️ select '{label_re}' NOT FOUND"); return False
    ev(f"""() => {{ const i=document.getElementById('{qid}'); i.focus(); i.value=''; const c=i.closest('.select__container')||i.parentElement; c.click(); }}""")
    time.sleep(0.9)
    r = ev(f"""() => {{
      const o=[...document.querySelectorAll('[id^="react-select-{qid}-option"]')].find(x=>x.offsetParent && {json.dumps(match)}.test((x.innerText||'').trim()));
      if (o) {{ o.click(); return 'clicked'; }} return 'no-match';
    }}""")
    time.sleep(0.5)
    print(f"  ✓ {label_re} -> {r}")
    return True

def text_fill(label_re, text):
    qid = find_control(label_re)
    if not qid:
        print(f"  ⚠️ text '{label_re}' NOT FOUND"); return False
    ev(f"() => {{ const i=document.getElementById('{qid}'); i.focus(); i.value=''; }}")
    typ(text)
    print(f"  ✓ {label_re} -> {text[:25]}")
    return True

def main(url):
    RESUME_PICK()
    ctl({"op": "navigate", "url": url}); time.sleep(3)
    ev("() => { const a=[...document.querySelectorAll('a,button')].find(x=>x.offsetParent&&/apply/i.test((x.innerText||'').trim())); if(a)a.click(); return 1; }")
    time.sleep(2)
    ctl({"op": "upload_cdp", "path": BEFORE_UPLOAD()}); time.sleep(1); RESUME_POST()
    text_fill("first name", A["first"]); text_fill("last name", A["last"])
    text_fill("^email", A["email"]); text_fill("^phone", A["phone"].replace("+91 ","").replace(" ",""))
    text_fill("linkedin profile", "https://" + A["linkedin"])
    text_fill("^website|github", "https://" + A["github"])
    sel_pick("country", "^India")
    sel_pick("legal right", "^Yes")
    sel_pick("work permit", "^No")
    sel_pick("How did you learn", "LinkedIn")
    sel_pick("previously worked for this employer", "never worked")
    sel_pick("procurement|government employee", "^No$")
    text_fill("Current Company", "<current employer>")
    text_fill("Current Title", "Senior QA Engineer")
    text_fill("Home Address|address", "Bengaluru, Karnataka <postcode>, India")
    # consents: any unchecked checkbox near "I Agree" / gdpr
    ev("""() => {
      for (const c of document.querySelectorAll('input[type=checkbox]')) {
        const lbl = (c.labels?.[0]?.innerText || c.closest('.field')?.innerText || '');
        if (c.offsetParent && !c.checked && (/I Agree|consent/i.test(lbl) || /gdpr/.test(c.id))) c.click();
      }
      return 1;
    }""")
    sel_pick("sex|wish to answer|gender", "don't wish")
    time.sleep(1)
    ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/submit application/i.test(x.innerText)); if(b)b.click(); return 1; }")
    time.sleep(6)
    r = ev("""() => {
      const errs=[...document.querySelectorAll('[class*=error]')].filter(x=>x.offsetParent&&/required/i.test(x.innerText||'')).map(e=>e.id);
      const ok=document.body.innerText.match(/(Application received|Thanks for applying|Your application has been submitted)/i);
      return JSON.stringify({errs, ok: ok?ok[0]:null});
    }""")
    print("RESULT:", r)

if __name__ == "__main__":
    main(sys.argv[1])
