import sys
sys.path.insert(0, 'config')
from config.answers import A
#!/usr/bin/env python3
"""workable_apply.py <job_url> — generic Workable apply: click Apply, fill std+custom fields,
keyword-based custom questions, radios, resume (filechooser), submit. Same-eval fills to avoid re-render wipes."""
import json, socket, sys, time, re

def ctl(cmd, timeout=30):
    s = socket.create_connection(("127.0.0.1", 9000), timeout=timeout)
    s.sendall((json.dumps(cmd) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(65536)
        if not c: break
        buf += c
    s.close()
    return json.loads(buf.decode())

def ev(js):
    return (ctl({"op": "eval", "js": js}) or {}).get("result") or ""

def main():
    url = sys.argv[1]
    ctl({"op": "navigate", "url": url})
    time.sleep(8)
    # open apply form
    r = ev("() => { const b=[...document.querySelectorAll('button,a')].find(x=>x.offsetParent&&/^Apply for this job$/.test((x.innerText||'').trim())); if(b){ b.click(); return 'clicked'; } return /firstname/i.test(document.body.innerText)?'on-form':'no'; }")
    print("apply:", r, flush=True)
    time.sleep(6)
    # 1) upload resume FIRST (triggers the re-render, then we fill)
    ev("() => { const f=document.querySelector('input[type=file]'); if(f) f.click(); return 1; }")
    time.sleep(8)
    print("resume:", ev("() => { const f=document.querySelector('input[type=file]'); return f?f.files.length:0; }"), flush=True)
    # 2) same-eval: fill standard + keyword custom fields + radios + submit
    r = ev("""() => {
      const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
      const tset=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
      const fillI=(n,v)=>{ const el=document.querySelector('[name="'+n+'"]'); if(el&&el.type!=='radio'&&el.type!=='checkbox'&&!el.value){ set.call(el,v); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); el.dispatchEvent(new Event('blur',{bubbles:true})); } };
      fillI('firstname', A['first']); fillI('lastname', A['last']); fillI('email', A['email']); fillI('phone', A['phone'].replace('+91 ','').replace(' ',''))
      fillI('city','Bengaluru'); fillI('postcode','<postcode>'); fillI('country','India');
      // keyword custom fields (only if empty)
      const kwMap = [
        [/preferred name/i, A["first"]], [/mailing address|address/i, A["address"]],
        [/linkedin/i, A["linkedin"]], [/salary/i, str(A["expected_ctc_lpa"])],
        [/work auth/i, 'Yes'], [/start date/i, 'Immediate'], [/hear about/i, 'Job Board'],
        [/how did you hear/i, 'Job Board'], [/current employer/i, '<current employer>'],
        [/experience years|years of experience/i, '8']
      ];
      const out=[];
      for(const el of document.querySelectorAll('input[type=text], input[type=number], input[type=tel], input[type=email], textarea')){
        if(!el.offsetParent||el.value) continue;
        let q=''; let n=el.parentElement;
        for(let i=0;i<6&&n;i++){ const t=(n.innerText||'').replace(/\\s+/g,' ').trim(); if(t.length>4&&t.length<90){ q=t; break; } n=n.parentElement; }
        const m=kwMap.find(k=>k[0].test(q));
        if(m){ const s=el.tagName==='TEXTAREA'?tset:set; s.call(el,m[1]); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); el.dispatchEvent(new Event('blur',{bubbles:true})); out.push(el.name+'='+m[1]); }
      }
      // radios: yes/no by question
      const rds=[...document.querySelectorAll('input[type=radio]')].filter(r=>r.offsetParent);
      let n=0;
      for(const rd of rds){
        const par=rd.parentElement; const lt=par?(par.innerText||'').trim():'';
        const row=rd.closest('fieldset')||rd.closest('[class*=field]')||document.body;
        const q=(row.innerText||'').replace(/\\s+/g,' ').trim();
        let want=null;
        if(/sponsorship/i.test(q)) want='No';
        else if(/1<years> years|authorized to work/i.test(q)) want='Yes';
        else if(/worked for|ever been employed|related to/i.test(q)) want='No';
        else if(/confirm|consent|agree/i.test(q)) want='Yes';
        if(want&&lt===want&&!rd.checked){ rd.click(); n++; }
      }
      return JSON.stringify({custom:out, radios:n});
    }""")
    print("fill:", r, flush=True)
    time.sleep(1)
    r = ev("() => { const b=[...document.querySelectorAll('button')].find(x=>x.offsetParent&&/^Submit application$/.test((x.innerText||'').trim())); if(!b) return 'no'; b.click(); return 'clicked'; }")
    print("submit:", r, flush=True)
    time.sleep(14)
    st = ev("() => { const t=document.body.innerText.replace(/\\s+/g,' '); const done=/Thank you|submitted successfully/i.test(t); const errs=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.offsetParent&&/required|this field/i.test(e.innerText||'')&&e.innerText.length<60).map(e=>e.innerText.trim().slice(0,40)); return JSON.stringify({done, errs:[...new Set(errs)].slice(0,3)}); }")
    print("AFTER:", st, flush=True)

main()
