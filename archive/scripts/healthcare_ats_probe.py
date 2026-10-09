#!/usr/bin/env python3
"""Probe Workday shadow-DOM inputs using deep pierce traversal via page.evaluate."""
import json, socket, subprocess, sys, time, os
BASE = os.environ.get("APPLY_HUB", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))); os.chdir(BASE)
CTL_PORT = 9000; PY = os.path.join(BASE, ".venv", "bin", "python")

def ctl(cmd, timeout=90):
    s = socket.create_connection(("127.0.0.1", CTL_PORT), timeout=timeout)
    try:
        s.sendall((json.dumps(cmd) + "\n").encode()); b=b""
        while not b.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            b+=c
    finally: s.close()
    try: return json.loads(b.decode() or "{}")
    except: return {"raw": b.decode()[:200]}

def ev(js, arg=None):
    c={"op":"eval","js":js}
    if arg is not None: c["arg"]=arg
    return ctl(c).get("result")

def up():
    try:
        return "url" in ctl({"op":"status"})
    except Exception: return False

PIERCE = r"""() => {
  const out=[];
  const walk=(root)=>{
    root.querySelectorAll('input,select,textarea,button').forEach(el=>{
      const r=el.getBoundingClientRect();
      out.push({t:el.tagName, id:el.id, name:el.name||'', aid:el.getAttribute('data-automation-id')||'', type:el.type||el.getAttribute('type')||'', vis:!!el.offsetParent, x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), ph:(el.placeholder||'').slice(0,30)});
    });
    root.querySelectorAll('*').forEach(e=>{ if(e.shadowRoot) walk(e.shadowRoot); });
  };
  walk(document);
  return out;
}"""

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

def main():
    if not ensure():
        print("FATAL server not up"); return
    print("URL:", ctl({"op":"status"}).get("url"))
    print("BODY:", ctl({"op":"bodytext","max":300}).get("text","")[:200].replace("\n"," "))
    print("ELTS:", json.dumps(ev(PIERCE), default=str)[:2500])

if __name__=="__main__":
    main()
