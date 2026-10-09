import os
#!/usr/bin/env python3
"""fill_gh.py <url> — generic Greenhouse filler: text + react-selects + resume + submit."""
import json, socket, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.answers import A, RESUME
from core.resume_secure import BEFORE_UPLOAD, POST as RESUME_POST, PICK as RESUME_PICK

def ctl(cmd, timeout=120):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    return json.loads(buf.decode())

FIELDS_JS = r"""() => {
    const out = [];
    for (const el of document.querySelectorAll("input:not([type=hidden]):not([type=file]), select, textarea")) {
        let label = '';
        if (el.labels && el.labels.length) label = el.labels[0].innerText;
        const rs = !!el.closest('[class*=select__input-container]');
        out.push({id: el.id, type: el.type, label: label.replace(/\s+/g,' ').trim().slice(0,80), rs, vis: !!el.offsetParent, req: el.required});
    }
    return out.filter(f => f.vis);
}"""

def rs_pick(qid, target, retries=3):
    ctl({"op": "eval", "js": f"() => {{ const i = document.getElementById('{qid}'); if (i) i.focus(); return 1; }}"})
    time.sleep(0.4)
    ctl({"op": "keys", "keys": "Meta+A"}); ctl({"op": "keys", "keys": "Backspace"})
    time.sleep(0.3)
    ctl({"op": "htype", "value": target[:6]})
    for _ in range(retries):
        time.sleep(2)
        r = ctl({"op": "eval", "js": f"() => {{ const menus = [...document.querySelectorAll('[class*=select__menu]')]; for (const m of menus) {{ const o = [...m.querySelectorAll('[class*=option]')]; const t = o.find(x => x.innerText.trim().toLowerCase() === '{target.lower()}') || o.find(x => x.innerText.includes('{target}')); if (t) {{ t.click(); return 'ok'; }} }} return 'none'; }}"})
        if r.get("result") == "ok":
            return True
    return False

def main():
    url = sys.argv[1]
    RESUME_PICK()
    print(f"🚀 {url}", flush=True)
    ctl({"op": "navigate", "url": url})
    time.sleep(4)
    fields = ctl({"op": "eval", "js": FIELDS_JS})["result"]
    print(f"   {len(fields)} visible fields", flush=True)
    std = {"first_name": A["full_name"].split()[0], "last_name": A["full_name"].split()[-1],
           "email": A["email"], "phone": A["phone"], "candidate-location": A["location"],
           "preferred_name": A["full_name"].split()[0]}
    # standard text fields + URLs
    extra = {"question": None}
    filled = 0
    for f in fields:
        fid, lbl = f["id"], f["label"].lower()
        if not fid: continue
        if f["rs"]:
            continue  # handled in pass 2
        val = None
        if fid in std: val = std[fid]
        elif "linkedin" in lbl: val = A["linkedin"]
        elif "website" in lbl and "github" not in lbl: val = A["github"]
        elif "how did you hear" in lbl: val = "LinkedIn"
        if val:
            r = ctl({"op": "hfill", "by": "selector", "key": f"#{fid}", "value": val})
            if r.get("ok"): filled += 1; print(f"  ✍️ {fid} ({lbl[:28]})", flush=True)
            time.sleep(random.uniform(0.8, 1.6))
    # react-selects: Yes/No + country + location + months
    for f in fields:
        if not f["rs"]: continue
        fid, lbl = f["id"], f["label"].lower()
        target = None
        if not lbl or len(lbl) < 3: continue
        if any(k in lbl for k in ["authorized", "visa", "sponsorship", "relocate", "in-person", "family", "business activity", "employed by", "ai tools", "cloud platform", "docker", "kubernetes", "proficiency", "performance testing", "<years> years", "experience with", "network protocol"]):
            target = "Yes" if not any(k in lbl for k in ["visa", "sponsorship", "family", "business activity", "employed by", "network protocol"]) else "No"
        elif "country" in lbl: target = "India +91"
        elif "location" in lbl: target = "Bengaluru"
        elif "month" in lbl:
            target = "August" if "start" in lbl else "May"
        elif "year" in lbl: continue
        elif "degree" in lbl: target = "Bachelor"
        elif "discipline" in lbl: target = "Computer Science"
        elif "school" in lbl:
            print(f"  ⚠️ school field — trying manual entry", flush=True)
        if target:
            ok = rs_pick(fid, target)
            print(f"  {'✅' if ok else '❌'} select {fid} ({lbl[:28]}) → {target}", flush=True)
            if ok: filled += 1
            time.sleep(random.uniform(0.6, 1.4))
    r = ctl({"op": "upload_cdp", "path": BEFORE_UPLOAD()})
    print(f"📎 resume: {'uploaded' if r.get('ok') else r.get('error')} | filled {filled}", flush=True)
    if r.get('ok'): RESUME_POST()

main()
