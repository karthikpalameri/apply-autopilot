#!/usr/bin/env python3
"""capsolver.py — CapSolver API wrapper: hCaptcha, reCAPTCHA v3, reCAPTCHA v2 Enterprise."""
import json, os, time, urllib.request
from pathlib import Path

def _load_env():
    envp = Path(__file__).resolve().parent / ".env"
    if envp.exists():
        for line in envp.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ.get("CAPSOLVER_API_KEY")

_load_env()

def _post(path, payload, timeout=90):
    def _ctx():
        try:
            import certifi, ssl
            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            return None
    req = urllib.request.Request(f"https://api.capsolver.com{path}",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout, context=_ctx()).read())

def get_balance(key=None):
    key = key or os.environ.get("CAPSOLVER_API_KEY")
    r = _post("/getBalance", {"clientKey": key})
    return r.get("balance")

def _poll(task_type, task, key, max_wait):
    r = _post("/createTask", {"clientKey": key, "task": task})
    tid = r.get("taskId")
    if not tid:
        return {"ok": False, "error": r}
    for _ in range(max_wait // 5):
        time.sleep(5)
        r = _post("/getTaskResult", {"clientKey": key, "taskId": tid})
        st = r.get("status")
        if st == "ready":
            return {"ok": True, "token": r["solution"]["gRecaptchaResponse"]}
        if st == "failed":
            return {"ok": False, "error": r}
    return {"ok": False, "error": "timeout"}

def solve_hcaptcha(sitekey, pageurl, key=None, max_wait=180, enterprise=False):
    key = key or os.environ.get("CAPSOLVER_API_KEY")
    task = {"type": "HCaptchaTaskProxyless", "websiteURL": pageurl, "websiteKey": sitekey}
    if enterprise:
        task["enterprisePayload"] = {"rqdata": ""}
    return _poll("hcaptcha", task, key, max_wait)

def solve_recaptcha_v3(sitekey, pageurl, score=0.9, key=None, max_wait=180):
    key = key or os.environ.get("CAPSOLVER_API_KEY")
    task = {"type": "ReCaptchaV3TaskProxyless",
            "websiteURL": pageurl, "websiteKey": sitekey, "minScore": score}
    return _poll("v3", task, key, max_wait)

def solve_recaptcha_v2_enterprise(sitekey, pageurl, key=None, max_wait=180):
    key = key or os.environ.get("CAPSOLVER_API_KEY")
    task = {"type": "ReCaptchaV2EnterpriseTaskProxyless",
            "websiteURL": pageurl, "websiteKey": sitekey, "isInvisible": True}
    return _poll("v2ent", task, key, max_wait)

def solve_recaptcha_v2(sitekey, pageurl, key=None, max_wait=180):
    key = key or os.environ.get("CAPSOLVER_API_KEY")
    task = {"type": "ReCaptchaV2TaskProxyless",
            "websiteURL": pageurl, "websiteKey": sitekey}
    return _poll("v2", task, key, max_wait)
