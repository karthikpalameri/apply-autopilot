#!/usr/bin/env python3
"""Full AcmeEmployer Workday application driver (single-process: server + drive)."""
import json, socket, subprocess, sys, time, os
# Legacy example — run from the repo root, or set APPLY_HUB to your checkout path.
HUB = os.environ.get("APPLY_HUB", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(HUB)
CTL=9000; PY=os.path.join(HUB,".venv","bin","python")
RESUME=os.path.join(HUB,"config","your_resume.pdf")  # point at your own resume (see setup.py)

def ctl(cmd, timeout=120):
    s=socket.create_connection(("127.0.0.1",CTL),timeout=timeout)
    try:
        s.sendall((json.dumps(cmd)+"\n").encode()); b=b""
        while not b.endswith(b"\n"):
            c=s.recv(65536)
            if not c: break
            b+=c
    finally: s.close()
    try: return json.loads(b.decode() or "{}")
    except: return {"raw":b.decode()[:300]}

def up():
    try: return "url" in ctl({"op":"status"})
    except Exception: return False

def ensure():
    if not up():
        subprocess.run(["pkill","-9","-f","runtime/server.py"],capture_output=True)
        os.system("ps aux | grep 'mcp-session' | grep -viE 'grep' | grep -iE 'chrom|node' | awk '{print $2}' | xargs -r kill -9 2>/dev/null")
        time.sleep(4)
        subprocess.Popen([PY,"runtime/server.py"],stdout=open("logs/server.out","a"),stderr=subprocess.STDOUT,start_new_session=True)
        for _ in range(50):
            time.sleep(2)
            if up(): return True
    return up()

def body():
    return ctl({"op":"bodytext","max":1200}).get("text","")

def pierce():
    J='''()=>{const out=[];const walk=r=>{r.querySelectorAll('input,select,textarea,button').forEach(e=>{const b=e.getBoundingClientRect();out.push({t:e.tagName,aid:e.getAttribute('data-automation-id')||'',type:e.type||e.getAttribute('type')||'',vis:!!e.offsetParent,val:(e.value||'').slice(0,20),txt:(e.textContent||'').trim().slice(0,25)});});r.querySelectorAll('*').forEach(e=>{if(e.shadowRoot)walk(e.shadowRoot);});};walk(document);return out;}'''
    return ctl({"op":"eval","js":J}).get("result") or []

def fill(aid, value, verify=False):
    r = ctl({"op":"fill","by":"selector","key":f'[data-automation-id="{aid}"]',"value":value})
    if verify:
        for _ in range(4):
            el=[e for e in pierce() if e.get('aid')==aid]
            if el and el[0].get('val','')==value:
                return r
            # retype via selector fill again
            time.sleep(1)
            ctl({"op":"fill","by":"selector","key":f'[data-automation-id="{aid}"]',"value":value})
            time.sleep(1)
    return r

def val_of(aid):
    el=[e for e in pierce() if e.get('aid')==aid]
    return el[0].get('val','') if el else None

def click(aid):
    return ctl({"op":"click","by":"selector","key":f'[data-automation-id="{aid}"]'})

def click_txt(txt):
    return ctl({"op":"click","by":"selector","key":f'button:has-text("{txt}")'})

def start():
    if not ensure():
        print("FATAL_SERVER"); return False
    ctl({"op":"navigate","url":"https://<tenant>.myworkdayjobs.com/en-US/Careers/job/Bengaluru%2C-India/QA-Automation-Engineer_R015451/apply/applyManually"})
    time.sleep(5)
    print("STEP start:", ctl({"op":"status"}).get("url"))
    return True

def create_account():
    # wait for email field to render
    for _ in range(15):
        if val_of('email') is not None:
            break
        time.sleep(2)
    fill("email","jane.doe@example.com", verify=True); time.sleep(1)
    pw = os.environ.get("APPLY_PASSWORD", "ChangeMe_Strong!123")
    fill("password", pw, verify=True); time.sleep(1)
    fill("verifyPassword", pw, verify=True); time.sleep(1)
    click("createAccountCheckbox"); time.sleep(1)
    print("AFTER_CREATE_FILL:", [e for e in pierce() if e.get('aid') in ('email','password','verifyPassword','createAccountCheckbox')])
    click("createAccountSubmitButton"); time.sleep(6)
    print("POST_CREATE:", body()[:400].replace("\n"," "))
    print("POST_URL:", ctl({"op":"status"}).get("url"))
    return True

if __name__=="__main__":
    if not start(): sys.exit(1)
    create_account()
    # keep server alive a bit for inspection then terminate
    time.sleep(2)
    subprocess.run(["pkill","-9","-f","runtime/server.py"],capture_output=True)
