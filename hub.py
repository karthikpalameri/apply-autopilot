#!/usr/bin/env python3
"""hub.py — cross-platform command center for Apply Autopilot (macOS / Linux / Windows).

Usage:
    python3 hub.py setup      # interactive personalization wizard (writes config/user.json)
    python3 hub.py install    # create .venv + install Python/npm/pi dependencies + pi MCP config
    python3 hub.py start      # start the browser stack (server.py :9000 + cloakbrowser-mcp :3000)
    python3 hub.py stop       # stop the browser stack
    python3 hub.py restart    # stop + start
    python3 hub.py health     # run the 6-test health check
    python3 hub.py track      # applied vs not-applied report (config/progress.json)
    python3 hub.py doctor     # diagnose environment (python/node/pi/ports/config)
    python3 hub.py mcp-config # (re)generate ~/.pi/agent/mcp-adapter.json + web-search.json

This is the recommended entry point on ALL platforms. The run.sh / run_li.sh / track.sh
scripts are thin POSIX wrappers; run.bat / run_li.bat / track.bat are the Windows equivalents.
"""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time

HUB = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = os.name == "nt"
PY = sys.executable

RUN_DIR = os.path.join(HUB, "runtime")
LOG_DIR = os.path.join(HUB, "logs")
PID_DIR = os.path.join(RUN_DIR, "pids")

CTL_PORT = 9000
MCP_PORT = 3000
CLOAKBROWSER_MCP_VERSION = os.environ.get("CLOAKBROWSER_MCP_VERSION", "latest")
CLOAK_VIEWPORT = os.environ.get("CLOAK_VIEWPORT", "1280x800")


def log(msg):
    print(f"[hub] {msg}", flush=True)


def run(cmd, cwd=None, env=None, capture=True, check=False):
    """Run a command; return CompletedProcess. stdout/stderr captured as text by default."""
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(cmd, cwd=cwd or HUB, env=e, capture_output=capture, text=True, check=check)


def venv_python():
    if IS_WINDOWS:
        p = os.path.join(HUB, ".venv", "Scripts", "python.exe")
    else:
        p = os.path.join(HUB, ".venv", "bin", "python")
    return p if os.path.exists(p) else sys.executable


def npx_cmd():
    return "npx.cmd" if IS_WINDOWS else "npx"


def node_cmd():
    return "node.exe" if IS_WINDOWS else "node"


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def write_pid(name, pid):
    os.makedirs(PID_DIR, exist_ok=True)
    with open(os.path.join(PID_DIR, name + ".pid"), "w") as f:
        f.write(str(pid))


def read_pid(name):
    p = os.path.join(PID_DIR, name + ".pid")
    if os.path.exists(p):
        try:
            return int(open(p).read().strip())
        except Exception:
            return None
    return None


def kill_pid(name):
    pid = read_pid(name)
    if not pid:
        return False
    try:
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, text=True)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception:
        pass
    try:
        os.remove(os.path.join(PID_DIR, name + ".pid"))
    except OSError:
        pass
    return True


def _spawn(name, cmd, env=None):
    """Start a detached background process and record its PID."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logf = open(os.path.join(LOG_DIR, name + ".out"), "ab")
    errf = open(os.path.join(LOG_DIR, name + ".err"), "ab")
    e = dict(os.environ)
    if env:
        e.update(env)
    if IS_WINDOWS:
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        proc = subprocess.Popen(cmd, cwd=HUB, env=e, stdout=logf, stderr=errf, creationflags=flags)
    else:
        proc = subprocess.Popen(cmd, cwd=HUB, env=e, stdout=logf, stderr=errf,
                                start_new_session=True)
    write_pid(name, proc.pid)
    logf.close()
    errf.close()
    return proc.pid


# ---------------------------------------------------------------- commands
def cmd_setup():
    r = run([sys.executable, "setup.py"], capture=False)
    return r.returncode


def cmd_install():
    print("=" * 64)
    print("INSTALL — Apply Autopilot dependencies (cross-platform)")
    print("=" * 64)

    # 1. Python venv
    print("\n[1/6] Python virtualenv")
    if not os.path.exists(os.path.join(HUB, ".venv")):
        r = run([sys.executable, "-m", "venv", ".venv"], capture=False)
        if r.returncode != 0:
            print("❌ could not create .venv"); return 1
    else:
        print("  .venv already exists")
    vp = venv_python()
    run([vp, "-m", "pip", "install", "--upgrade", "pip"], capture=False)
    run([vp, "-m", "pip", "install", "-r", "requirements.txt"], capture=False)

    # 2. Node + npm
    print("\n[2/6] Node.js + npm")
    node = shutil.which(node_cmd())
    if not node:
        print("  ⚠️  node not found — install from https://nodejs.org (LTS) then re-run install")
    else:
        r = run([node, "--version"], capture=True)
        print(f"  node {r.stdout.strip()}")

    # 3. Global npm MCP servers
    print("\n[3/6] npm MCP servers")
    if node:
        run([npx_cmd(), "--version"], capture=False)
        print("  installing @devinwangd/cloak-browser-mcp (Pi stdio browser)…")
        run(["npm", "install", "-g", "@devinwangd/cloak-browser-mcp"], capture=False)
        print(f"  cloakbrowser-mcp@{CLOAKBROWSER_MCP_VERSION} is launched on demand by hub.py start")
    else:
        print("  skipped (node missing)")

    # 4. pi coding agent + packages
    print("\n[4/6] pi coding agent packages")
    pi = shutil.which("pi")
    if pi:
        for pkg in ("npm:pi-mcp-adapter", "npm:pi-web-access", "npm:context-mode"):
            print(f"  pi install {pkg}")
            run([pi, "install", pkg], capture=False)
    else:
        print("  ⚠️  pi not found — install it first (see docs/INSTALL.md), then re-run install")

    # 5. pi MCP + web-search config (absolute paths for this checkout)
    print("\n[5/6] pi MCP + web-search config")
    cmd_mcp_config()

    # 6. System tools (informational)
    print("\n[6/6] System tools (manual — follow OS-specific guidance)")
    print("  tesseract (OCR):  brew install tesseract  |  apt install tesseract-ocr  |  winget install tesseract")
    print("  docker (SearXNG): optional — see infra/searxng/README.md")

    print("\n✅ install finished. Next:  python3 hub.py setup && python3 hub.py start")
    return 0


def cmd_mcp_config():
    """Write ~/.pi/agent/mcp-adapter.json + ~/.pi/web-search.json with absolute paths."""
    pi_home = os.path.expanduser("~/.pi")
    agent_dir = os.path.join(pi_home, "agent")
    os.makedirs(agent_dir, exist_ok=True)

    profile_dir = os.path.join(HUB, "runtime", "mcp-session")
    upload_dir = HUB
    download_dir = os.path.join(HUB, "temp")
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs(download_dir, exist_ok=True)

    mcp_cfg = {
        "mcpServers": {
            "cloak-browser": {
                "command": "cloak-browser-mcp",
                "args": [
                    "--caps", "all",
                    "--headed",
                    "--viewport", CLOAK_VIEWPORT,
                    "--enable-unsafe-eval",
                    "--profile-dir", profile_dir,
                    "--upload-allow-dir", upload_dir,
                    "--download-dir", download_dir,
                    "--max-pages", "20",
                ],
            }
        }
    }
    target = os.path.join(agent_dir, "mcp-adapter.json")
    with open(target, "w") as f:
        json.dump(mcp_cfg, f, indent=2)
    print(f"  wrote {target}")

    ws_cfg = {"provider": "all", "searxngBaseUrl": "http://127.0.0.1:8080"}
    target2 = os.path.expanduser("~/.pi/web-search.json")
    with open(target2, "w") as f:
        json.dump(ws_cfg, f, indent=2)
    print(f"  wrote {target2}")
    print("  (restart pi after writing these)")
    return 0


def cmd_start():
    if not os.path.exists(os.path.join(HUB, ".venv")):
        print("❌ .venv missing — run: python3 hub.py install")
        return 1
    vp = venv_python()

    # 1. ctl bridge :9000
    if port_in_use(CTL_PORT):
        log(f"port {CTL_PORT} already in use (server.py likely running)")
    else:
        _spawn("server", [vp, os.path.join("runtime", "server.py")])
        log(f"started runtime/server.py (:{CTL_PORT})")

    # 2. cloakbrowser-mcp :3000
    if port_in_use(MCP_PORT):
        log(f"port {MCP_PORT} already in use (cloakbrowser-mcp likely running)")
    else:
        lock = os.path.join(RUN_DIR, "mcp-session", ".cloakbrowser-mcp-profile.lock")
        if os.path.exists(lock):
            try:
                os.remove(lock)
            except OSError:
                pass
        env = {
            "PLAYWRIGHT_MCP_HEADLESS": "false",
            "PLAYWRIGHT_MCP_USER_DATA_DIR": os.path.join(RUN_DIR, "mcp-session"),
            "PLAYWRIGHT_MCP_SNAPSHOT_BOXES": "false",
            "CLOAK_PLAYWRIGHT_MCP_CONSOLE_FALLBACK": "false",
            "CLOAK_VIEWPORT": CLOAK_VIEWPORT,
        }
        _spawn("mcp", [npx_cmd(), "-y", f"cloakbrowser-mcp@{CLOAKBROWSER_MCP_VERSION}",
                       "--transport", "streamable-http", "--http-port", str(MCP_PORT)],
               env=env)
        log(f"started cloakbrowser-mcp (:{MCP_PORT})")

    log("waiting for services to come up…")
    time.sleep(8)
    cmd_health()
    return 0


def cmd_stop():
    killed = False
    for name in ("mcp", "server"):
        if kill_pid(name):
            log(f"stopped {name}")
            killed = True
    # best-effort: also try to free the ports by killing listeners
    if not killed:
        log("no pid files found — trying port-based cleanup is OS-specific; run `hub.py doctor`")
    time.sleep(1)
    return 0


def cmd_restart():
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def cmd_health():
    vp = venv_python()
    r = run([vp, os.path.join("core", "test_hub.py")], capture=False)
    return r.returncode


def cmd_track():
    vp = venv_python()
    args = sys.argv[2:]
    r = run([vp, os.path.join("find", "tracker_reconcile.py")] + args, capture=False)
    return r.returncode


def cmd_doctor():
    print("=" * 64)
    print("DOCTOR — environment diagnosis")
    print("=" * 64)

    def ok(name, cond, extra=""):
        print(f"  {'✅' if cond else '❌'} {name}{(' — ' + extra) if extra else ''}")

    ok("python3", shutil.which("python3") or shutil.which("python"))
    try:
        v = run([sys.executable, "--version"], capture=True).stdout.strip()
        ok("python version", True, v)
    except Exception:
        ok("python version", False)
    node = shutil.which(node_cmd())
    ok("node", bool(node))
    if node:
        ok("node version", True, run([node, "--version"], capture=True).stdout.strip())
    ok("npx", bool(shutil.which(npx_cmd())))
    ok("pi", bool(shutil.which("pi")))
    ok("tesseract", bool(shutil.which("tesseract")), "OCR")
    ok("docker", bool(shutil.which("docker")), "SearXNG (optional)")
    ok(".venv", os.path.exists(os.path.join(HUB, ".venv")))
    ok("config/user.json", os.path.exists(os.path.join(HUB, "config", "user.json")),
       "run: python3 hub.py setup")
    ok("config/resume.md5", os.path.exists(os.path.join(HUB, "config", "resume.md5")))
    ok(f"port {CTL_PORT} (ctl)", not port_in_use(CTL_PORT), "free" if not port_in_use(CTL_PORT) else "in use")
    ok(f"port {MCP_PORT} (mcp)", not port_in_use(MCP_PORT), "free" if not port_in_use(MCP_PORT) else "in use")

    # pi packages
    if shutil.which("pi"):
        r = run([shutil.which("pi"), "install", "--list"], capture=True)
        if r.returncode == 0:
            out = r.stdout + r.stderr
            for pkg in ("pi-mcp-adapter", "pi-web-access", "context-mode"):
                ok(f"pi package {pkg}", pkg in out)
    print("\nHUB:", HUB)
    return 0


def main():
    cmds = {
        "setup": cmd_setup,
        "install": cmd_install,
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "health": cmd_health,
        "track": cmd_track,
        "doctor": cmd_doctor,
        "mcp-config": cmd_mcp_config,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        return 1
    try:
        return cmds[sys.argv[1]]() or 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
