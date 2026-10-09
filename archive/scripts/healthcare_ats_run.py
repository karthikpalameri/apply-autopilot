#!/usr/bin/env python3
"""One-shot AcmeEmployer Workday application driver.
Launches server.py in background, then drives the whole flow via the ctl socket.
Everything in ONE process so the browser stays alive while we work.
"""
import json, re, socket, subprocess, sys, time, os

BASE = os.environ.get("APPLY_HUB", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(BASE)
CTL_PORT = 9000
PY = os.path.join(BASE, ".venv", "bin", "python")

def ctl(cmd, timeout=90):
    s = socket.create_connection(("127.0.0.1", CTL_PORT), timeout=timeout)
    try:
        s.sendall((json.dumps(cmd) + "\n").encode())
        b = b""
        while not b.endswith(b"\n"):
            c = s.recv(65536)
            if not c: break
            b += c
    finally:
        s.close()
    try:
        return json.loads(b.decode() or "{}")
    except Exception:
        return {"raw": b.decode()[:200]}

def ev(js):
    return ctl({"op": "eval", "js": js}).get("result")

def navigate(url):
    return ctl({"op": "navigate", "url": url})

def body():
    return ctl({"op": "bodytext", "max": 900}).get("text", "")

def main():
    # kill stragglers on our profile
    subprocess.run(["pkill", "-9", "-f", "runtime/server.py"], capture_output=True)
    os.system("ps aux | grep 'mcp-session' | grep -viE 'grep' | grep -iE 'chrom|node' | awk '{print $2}' | xargs -r kill -9 2>/dev/null")
    time.sleep(4)

    # launch server detached so it survives within this same process tree
    server = subprocess.Popen(
        [PY, "runtime/server.py"],
        stdout=open("logs/server.out", "a"), stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    # wait for listen
    up = False
    for _ in range(40):
        time.sleep(2)
        try:
            st = ctl({"op": "status"})
            if "url" in st:
                up = True
                break
        except Exception:
            pass
    if not up:
        print("FATAL server not up"); return

    # Go to Netflix... no, AcmeEmployer apply
    navigate("https://<tenant>.myworkdayjobs.com/Careers/job/Bengaluru-India/QA-Automation-Engineer_R015451")
    time.sleep(4)
    print("STEP0:", body()[:150].replace("\n", " "))

    # Open apply chooser -> apply manually
    navigate("https://<tenant>.myworkdayjobs.com/en-US/Careers/job/Bengaluru%2C-India/QA-Automation-Engineer_R015451/apply/applyManually")
    time.sleep(4)
    print("STEP1:", body()[:200].replace("\n", " "))

    # Fill create-account step
    fields = ctl({"op": "fields"}).get("fields", [])
    print("FIELDS:", json.dumps([{"n": f.get("name"), "q": f.get("q")} for f in fields], default=str)[:800])

    server.terminate()

if __name__ == "__main__":
    main()
