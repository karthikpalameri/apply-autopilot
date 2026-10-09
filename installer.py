#!/usr/bin/env python3
"""installer.py — interactive cross-platform dependency installer for Apply Autopilot.

Detects the OS + package manager, checks every missing dependency, SHOWS the exact
commands it will run, asks the user to confirm, then installs everything:
  - system tools (node, git, tesseract, docker optional) via brew / apt / winget
  - Python venv + requirements.txt
  - npm MCP servers (@devinwangd/cloak-browser-mcp)
  - pi coding agent (@earendil-works/pi-coding-agent) + its packages
  - pi MCP + web-search config files

Run directly:   python3 installer.py
Or via hub:     python3 hub.py install
"""
import json
import os
import shutil
import subprocess
import sys

HUB = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def which(name):
    return shutil.which(name)


def pkg_manager():
    if IS_MAC:
        return "brew" if which("brew") else None
    if IS_LINUX:
        for p in ("apt-get", "dnf", "pacman", "zypper"):
            if which(p):
                return p
        return None
    if IS_WINDOWS:
        for p in ("winget", "choco", "scoop"):
            if which(p):
                return p
        return None
    return None


def sudo_prefix():
    """sudo for system package managers on Linux (unless already root)."""
    if IS_LINUX and os.geteuid() != 0:
        return ["sudo"]
    return []


def run(cmd, show=True):
    """Run a command list. Return (ok, output_tail)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0:
            if show:
                print(f"    ✅ {cmd[0]} {' '.join(cmd[1:3])}")
            return True, out[-300:]
        if show:
            print(f"    ❌ failed: {' '.join(cmd)}")
            print(f"       {out[-400:]}")
        return False, out[-400:]
    except Exception as e:
        if show:
            print(f"    ❌ error running {' '.join(cmd)}: {e}")
        return False, str(e)


# ---------------------------------------------------------------- tool checks + install commands
def _python_ok():
    try:
        v = sys.version_info
        return (v.major, v.minor) >= (3, 10), f"Python {v.major}.{v.minor}.{v.micro}"
    except Exception:
        return False, "?"


def _check(name):
    if name == "python":
        ok, detail = _python_ok()
        return ok, detail
    if name in ("node", "npm", "npx"):
        n = which("node")
        return bool(n), (n or "missing")
    if name == "tesseract":
        t = which("tesseract")
        return bool(t), (t or "missing")
    if name == "git":
        g = which("git")
        return bool(g), (g or "missing")
    if name == "docker":
        d = which("docker")
        return bool(d), (d or "missing (optional)")
    if name == "pi":
        p = which("pi")
        return bool(p), (p or "missing")
    return False, "unknown"


def install_commands(name):
    """Return the shell command(s) for a missing system tool, per OS + pkg manager."""
    pm = pkg_manager()
    if name == "node":
        if IS_MAC:
            return [["brew", "install", "node"]]
        if IS_LINUX and pm == "apt-get":
            return [sudo_prefix() + ["apt-get", "install", "-y", "nodejs", "npm"]]
        if IS_LINUX and pm == "dnf":
            return [sudo_prefix() + ["dnf", "install", "-y", "nodejs", "npm"]]
        if IS_WINDOWS and pm == "winget":
            return [["winget", "install", "-e", "--id", "OpenJS.NodeJS.LTS"]]
        return None
    if name == "tesseract":
        if IS_MAC:
            return [["brew", "install", "tesseract"]]
        if IS_LINUX and pm == "apt-get":
            return [sudo_prefix() + ["apt-get", "install", "-y", "tesseract-ocr"]]
        if IS_WINDOWS and pm == "winget":
            return [["winget", "install", "-e", "--id", "UB-Mannheim.TesseractOCR"]]
        return None
    if name == "git":
        if IS_MAC:
            return [["brew", "install", "git"]]
        if IS_LINUX and pm == "apt-get":
            return [sudo_prefix() + ["apt-get", "install", "-y", "git"]]
        if IS_WINDOWS and pm == "winget":
            return [["winget", "install", "-e", "--id", "Git.Git"]]
        return None
    if name == "docker":
        if IS_MAC:
            return [["brew", "install", "--cask", "docker"]]
        if IS_LINUX and pm == "apt-get":
            return [sudo_prefix() + ["apt-get", "install", "-y", "docker.io", "docker-compose-v2"]]
        if IS_WINDOWS and pm == "winget":
            return [["winget", "install", "-e", "--id", "Docker.DockerDesktop"]]
        return None
    if name == "pi":
        return [["npm", "install", "-g", "@earendil-works/pi-coding-agent"]]
    return None


def venv_python():
    if IS_WINDOWS:
        p = os.path.join(HUB, ".venv", "Scripts", "python.exe")
    else:
        p = os.path.join(HUB, ".venv", "bin", "python")
    return p if os.path.exists(p) else sys.executable


# ---------------------------------------------------------------- main installer
def install_system_tools(interactive=True):
    """Check system tools, show missing + commands, ask, then install."""
    print("\n[1/5] System tools (node, git, tesseract, docker optional)")
    pm = pkg_manager()
    print(f"  OS: {sys.platform} · package manager: {pm or '⚠️ none detected'}")

    required = ["node", "git", "tesseract"]
    optional = ["docker"]
    missing = []
    for name in required + optional:
        ok, detail = _check(name)
        if not ok:
            cmds = install_commands(name)
            missing.append((name, cmds, name in optional))

    if not missing:
        print("  ✅ all system tools present")
        return True

    print("\n  These are MISSING — here is exactly what I'll run to install them:")
    for name, cmds, opt in missing:
        tag = " (optional)" if opt else ""
        if cmds:
            print(f"    • {name}{tag}:")
            for c in cmds:
                print(f"        $ {' '.join(c)}")
        else:
            print(f"    • {name}{tag}: no automatic installer for your OS — see docs/INSTALL.md")

    if interactive:
        ans = input("\n  Proceed with these installs now? [y]es / [n]o: ").strip().lower()
        if ans not in ("y", "yes", ""):
            print("  ⏭️  Skipping system installs.")
            return False
    print("  Installing…")
    for name, cmds, opt in missing:
        if name in ("docker",) and opt and interactive:
            if input(f"  Install optional {name} too? [y/N]: ").strip().lower() not in ("y", "yes"):
                continue
        if cmds:
            for c in cmds:
                run(c)
        else:
            print(f"    ⚠️  {name} must be installed manually")
    return True


def install_python_env():
    print("\n[2/5] Python virtualenv + requirements")
    if not os.path.exists(os.path.join(HUB, ".venv")):
        run([sys.executable, "-m", "venv", ".venv"])
    vp = venv_python()
    run([vp, "-m", "pip", "install", "--upgrade", "pip"], show=False)
    run([vp, "-m", "pip", "install", "-r", os.path.join(HUB, "requirements.txt")])


def install_npm():
    print("\n[3/5] npm MCP servers")
    if not which("node"):
        print("  ⚠️  node missing — install it first, then re-run")
        return
    run(["npm", "install", "-g", "@devinwangd/cloak-browser-mcp"])


def install_pi():
    print("\n[4/5] pi coding agent + packages")
    if not which("pi"):
        run(["npm", "install", "-g", "@earendil-works/pi-coding-agent"])
    if which("pi"):
        for pkg in ("npm:pi-mcp-adapter", "npm:pi-web-access", "npm:context-mode"):
            run(["pi", "install", pkg])
    else:
        print("  ⚠️  pi not available — skipped pi packages")


def configure_pi():
    """Write ~/.pi/agent/mcp-adapter.json + ~/.pi/web-search.json (absolute paths)."""
    print("\n[5/5] pi MCP + web-search config")
    agent_dir = os.path.expanduser("~/.pi/agent")
    os.makedirs(agent_dir, exist_ok=True)
    profile_dir = os.path.join(HUB, "runtime", "mcp-session")
    download_dir = os.path.join(HUB, "temp")
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs(download_dir, exist_ok=True)

    mcp_cfg = {"mcpServers": {"cloak-browser": {
        "command": "cloak-browser-mcp",
        "args": ["--caps", "all", "--headed", "--viewport", "1280x800", "--enable-unsafe-eval",
                 "--profile-dir", profile_dir, "--upload-allow-dir", HUB,
                 "--download-dir", download_dir, "--max-pages", "20"],
    }}}
    with open(os.path.join(agent_dir, "mcp-adapter.json"), "w") as f:
        json.dump(mcp_cfg, f, indent=2)
    print(f"  ✅ wrote ~/.pi/agent/mcp-adapter.json")

    ws = {"provider": "all", "searxngBaseUrl": "http://127.0.0.1:8080"}
    with open(os.path.expanduser("~/.pi/web-search.json"), "w") as f:
        json.dump(ws, f, indent=2)
    print("  ✅ wrote ~/.pi/web-search.json")
    print("  (restart pi after this)")


def run_all(interactive=True):
    print("=" * 68)
    print("  INSTALL — Apply Autopilot (interactive, cross-platform)")
    print("=" * 68)
    install_system_tools(interactive)
    install_python_env()
    install_npm()
    install_pi()
    configure_pi()
    print("\n" + "=" * 68)
    print("  ✅ Install finished.")
    print("  Next:  python3 hub.py onboard  →  python3 hub.py start  →  python3 hub.py eval")
    print("  (Windows: open a NEW terminal so PATH picks up fresh installs)")
    print("=" * 68)


if __name__ == "__main__":
    try:
        run_all(interactive=True)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
