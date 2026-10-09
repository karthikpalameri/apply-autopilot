#!/usr/bin/env python3
"""eval.py — readiness evaluation for Apply Autopilot.

Runs a set of test cases (profile, python env, node/MCP, pi, system tools, runtime)
and computes a weighted SUCCESS RATE (0–100%). Each failing case prints the exact
fix command.

Run:  python3 eval.py        (or:  python3 hub.py eval)
"""
import json
import os
import shutil
import socket
import subprocess
import sys

HUB = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = os.name == "nt"

CFG = os.path.join(HUB, "config", "user.json")
MD5 = os.path.join(HUB, "config", "resume.md5")


def which(name):
    return shutil.which(name)


def venv_python():
    if IS_WINDOWS:
        p = os.path.join(HUB, ".venv", "Scripts", "python.exe")
    else:
        p = os.path.join(HUB, ".venv", "bin", "python")
    return p if os.path.exists(p) else None


def port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.7)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _venv_import(mod):
    vp = venv_python()
    if not vp:
        return False, "no .venv"
    r = subprocess.run([vp, "-c", f"import {mod}"], capture_output=True, text=True)
    return r.returncode == 0, ("" if r.returncode == 0 else r.stderr.strip()[-120:])


def _pi_packages():
    pi = which("pi")
    if not pi:
        return [], False
    r = subprocess.run([pi, "list"], capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    found = [p for p in ("pi-mcp-adapter", "pi-web-access", "context-mode") if p in out]
    return found, True


def load_cfg():
    try:
        with open(CFG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def resume_ok():
    cfg = load_cfg()
    rp = cfg.get("resume_path", "")
    rp = os.path.expanduser(rp) if rp else ""
    return os.path.exists(rp), rp


# ---------------------------------------------------------------- test cases
# Each: (id, label, weight, fn -> (ok, detail), fix_hint)
def build_cases():
    cases = []

    # 1. Profile & identity — 25
    def c_user_json():
        ok = os.path.exists(CFG)
        return ok, (CFG if ok else "missing")
    cases.append(("profile.user_json", "config/user.json exists", 8, c_user_json,
                  "python3 hub.py onboard"))

    def c_user_valid():
        cfg = load_cfg()
        ok = bool(cfg.get("full_name") and cfg.get("email"))
        return ok, f"{cfg.get('full_name','')} <{cfg.get('email','')}>" if ok else "missing name/email"
    cases.append(("profile.identity", "name + email configured", 7, c_user_valid,
                  "python3 hub.py onboard"))

    def c_md5():
        ok = os.path.exists(MD5)
        return ok, (MD5 if ok else "missing")
    cases.append(("profile.md5", "resume.md5 present", 5, c_md5,
                  "python3 hub.py onboard"))

    def c_resume():
        ok, p = resume_ok()
        return ok, (p if ok else "resume file not found")
    cases.append(("profile.resume", "resume PDF exists", 5, c_resume,
                  "re-run onboarding with the correct resume path"))

    # 2. Python env — 20
    def c_venv():
        ok = venv_python() is not None
        return ok, (venv_python() or "missing")
    cases.append(("py.venv", ".venv created", 5, c_venv, "python3 hub.py install"))

    def c_cloakbrowser():
        ok, d = _venv_import("cloakbrowser")
        return ok, d
    cases.append(("py.cloakbrowser", "cloakbrowser importable", 6, c_cloakbrowser,
                  ".venv/bin/pip install cloakbrowser"))

    def c_pypdf():
        ok, d = _venv_import("pypdf")
        return ok, d
    cases.append(("py.pypdf", "pypdf importable", 4, c_pypdf, ".venv/bin/pip install pypdf"))

    def c_pil():
        ok, d = _venv_import("PIL")
        return ok, d
    cases.append(("py.pillow", "Pillow importable (OCR)", 5, c_pil, ".venv/bin/pip install Pillow"))

    # 3. Node & MCP — 15
    def c_node():
        return bool(which("node")), (which("node") or "missing")
    cases.append(("node.bin", "node installed", 5, c_node, "see docs/INSTALL.md"))

    def c_npx():
        return bool(which("npx")), (which("npx") or "missing")
    cases.append(("node.npx", "npx available", 5, c_npx, "bundled with Node.js"))

    def c_mcp_npm():
        ok = bool(which("cloak-browser-mcp"))
        return ok, (which("cloak-browser-mcp") or "missing")
    cases.append(("node.mcp", "@devinwangd/cloak-browser-mcp installed", 5, c_mcp_npm,
                  "npm install -g @devinwangd/cloak-browser-mcp"))

    # 4. pi + pi config — 20
    def c_pi():
        return bool(which("pi")), (which("pi") or "missing")
    cases.append(("pi.bin", "pi coding agent installed", 5, c_pi,
                  "npm install -g @earendil-works/pi-coding-agent"))

    def c_pi_pkgs():
        found, have_pi = _pi_packages()
        ok = have_pi and len(found) == 3
        return ok, (", ".join(found) if found else "none" + ("" if have_pi else " (pi missing)"))
    cases.append(("pi.packages", "pi packages (adapter/web-access/context-mode)", 10, c_pi_pkgs,
                  "pi install npm:pi-mcp-adapter && pi install npm:pi-web-access && pi install npm:context-mode"))

    def c_pi_mcp():
        ok = os.path.exists(os.path.expanduser("~/.pi/agent/mcp-adapter.json"))
        return ok, ("~/.pi/agent/mcp-adapter.json" if ok else "missing")
    cases.append(("pi.mcp_config", "pi MCP config (mcp-adapter.json)", 3, c_pi_mcp,
                  "python3 hub.py mcp-config"))

    def c_pi_ws():
        ok = os.path.exists(os.path.expanduser("~/.pi/web-search.json"))
        return ok, ("~/.pi/web-search.json" if ok else "missing")
    cases.append(("pi.websearch", "pi web-search config", 2, c_pi_ws,
                  "python3 hub.py mcp-config"))

    # 5. System tools — 10
    def c_tess():
        return bool(which("tesseract")), (which("tesseract") or "missing")
    cases.append(("sys.tesseract", "tesseract (OCR)", 6, c_tess,
                  "brew install tesseract | apt install tesseract-ocr | winget install UB-Mannheim.TesseractOCR"))

    def c_git():
        return bool(which("git")), (which("git") or "missing")
    cases.append(("sys.git", "git", 2, c_git, "see docs/INSTALL.md"))

    def c_docker():
        return bool(which("docker")), (which("docker") or "missing (optional)")
    cases.append(("sys.docker", "docker (SearXNG, optional)", 2, c_docker,
                  "install Docker Desktop (optional)"))

    # 6. Runtime — 10
    def c_ctl():
        ok = port_open(9000)
        return ok, ("reachable" if ok else "not running")
    cases.append(("run.ctl", "ctl bridge :9000 running", 5, c_ctl, "python3 hub.py start"))

    def c_mcp():
        ok = port_open(3000)
        return ok, ("reachable" if ok else "not running")
    cases.append(("run.mcp", "cloakbrowser-mcp :3000 running", 5, c_mcp, "python3 hub.py start"))

    return cases


# ---------------------------------------------------------------- report
def evaluate():
    cases = build_cases()
    total_weight = sum(c[2] for c in cases)
    earned = 0
    passed = failed = warn = 0

    print("=" * 72)
    print("  READINESS EVALUATION — Apply Autopilot")
    print("=" * 72)
    print(f"  {'CASE':<34} {'RESULT':<10} {'WEIGHT':>6}   DETAIL")
    print("-" * 72)

    failures = []
    for cid, label, weight, fn, fix in cases:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, str(e)[:100]
        if ok:
            passed += 1
            earned += weight
            mark = "✅ PASS"
        else:
            failed += 1
            mark = "❌ FAIL"
            failures.append((label, detail, fix))
        print(f"  {label:<34} {mark:<10} {weight:>5}%   {detail}")

    print("-" * 72)
    pct = round(100.0 * earned / total_weight) if total_weight else 0
    print(f"  PASSED {passed}/{passed + failed}   ·   SUCCESS RATE = {pct}%")

    if pct >= 90:
        grade = "🟢 EXCELLENT — ready to apply"
    elif pct >= 70:
        grade = "🟡 GOOD — a few gaps to close first"
    elif pct >= 50:
        grade = "🟠 PARTIAL — run the install + onboarding steps"
    else:
        grade = "🔴 NOT READY — run `python3 hub.py install` then `python3 hub.py onboard`"
    print(f"  GRADE: {grade}")

    if failures:
        print("\n  To fix the failing cases:")
        for label, detail, fix in failures:
            print(f"    • {label}: {detail}")
            print(f"        →  {fix}")
    print("=" * 72)
    return pct


if __name__ == "__main__":
    try:
        sys.exit(0 if evaluate() >= 70 else 1)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
