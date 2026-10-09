#!/usr/bin/env python3
"""validate.py — repo self-test: verify every Python file compiles, every skill has
valid frontmatter, and every file path referenced from skills actually exists.

This exists so ANY model (even a low-IQ one) gets a clear PASS/FAIL signal before
it trusts the repo. Run:  python3 validate.py   (or:  python3 hub.py validate)
"""
import os
import py_compile
import re
import sys

HUB = os.path.dirname(os.path.abspath(__file__))

PATH_RE = re.compile(r"(?:`|^|\s)((?:skills|core|config|apply|find|docs|infra|runtime)/[A-Za-z0-9_./\-]+\.(?:py|md|json|sh|yml|yaml|example))\b", re.M)

# Files that legitimately don't exist until the user runs onboarding/setup (git-ignored).
RUNTIME_FILES = {
    "config/user.json", "config/profile.json", "config/profile.md",
    "config/progress.json", "config/applied_vs_not_applied.md",
    "config/product_companies_tracker.md", "config/mcp_session.json",
    "config/resume.md5", "config/targets.json",
}


def is_runtime_file(path):
    if path in RUNTIME_FILES:
        return True
    if path.startswith("config/li_") and path.endswith(".json"):
        return True
    return False


FAILS = []
PASSES = []


def note_ok(msg):
    PASSES.append(msg)
    print(f"  ✅ {msg}")


def note_fail(msg):
    FAILS.append(msg)
    print(f"  ❌ {msg}")


def check_py_files():
    print("\n[1/3] Python files compile")
    for root, dirs, files in os.walk(HUB):
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", "node_modules",
                                                "runtime/mcp-session", "runtime/session", "logs", "temp")]
        for f in files:
            if f.endswith(".py"):
                p = os.path.join(root, f)
                try:
                    py_compile.compile(p, doraise=True)
                except Exception as e:
                    note_fail(f"{os.path.relpath(p, HUB)}: {e}")
    if not any("compile" in x for x in FAILS):
        note_ok("all .py files compile")


def check_skill_frontmatter():
    print("\n[2/3] Skill frontmatter + links")
    for root, dirs, files in os.walk(os.path.join(HUB, "skills")):
        for f in files:
            if f != "SKILL.md":
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, HUB)
            txt = open(p, encoding="utf-8").read()
            if not txt.startswith("---"):
                note_fail(f"{rel}: missing frontmatter (---)")
                continue
            parts = txt.split("---", 2)
            fm = parts[1] if len(parts) >= 3 else ""
            for key in ("name:", "description:"):
                if key not in fm:
                    note_fail(f"{rel}: frontmatter missing '{key}'")
            # the master skill (skills/SKILL.md) is the graph root — no parent required
            if "parent:" not in fm and rel != "skills/SKILL.md":
                note_fail(f"{rel}: frontmatter missing 'parent:' (graph edge)")
            # check referenced paths exist (skip runtime-generated git-ignored files)
            for m in PATH_RE.finditer(txt):
                link = m.group(1)
                if is_runtime_file(link):
                    continue
                target = os.path.join(HUB, link)
                if not os.path.exists(target):
                    note_fail(f"{rel}: broken link -> {link}")
    if not any("SKILL.md" in x for x in FAILS):
        note_ok("all skill files have valid frontmatter + resolvable links")


def check_invariants():
    print("\n[3/3] Repo invariants")
    # .mcp.json must stay empty (pi MCP is user-level only)
    mcp = os.path.join(HUB, ".mcp.json")
    if os.path.exists(mcp):
        import json
        try:
            d = json.load(open(mcp))
            if d.get("mcpServers") == {}:
                note_ok(".mcp.json is empty (correct — pi MCP is user-level)")
            else:
                note_fail(".mcp.json must stay {'mcpServers': {}}")
        except Exception as e:
            note_fail(f".mcp.json invalid JSON: {e}")
    # key entry points exist
    for f in ("hub.py", "onboarding.py", "setup.py", "installer.py", "eval.py",
              "resume_parser.py", "AGENTS.md", "README.md", "requirements.txt",
              "config/answers.py", "runtime/server.py"):
        if not os.path.exists(os.path.join(HUB, f)):
            note_fail(f"missing entry point: {f}")
    if not any(x.startswith("missing entry point") for x in FAILS):
        note_ok("all key entry points present")


def main():
    print("=" * 68)
    print("  REPO SELF-TEST (validate) — Apply Autopilot")
    print("=" * 68)
    check_py_files()
    check_skill_frontmatter()
    check_invariants()
    print("-" * 68)
    print(f"  PASS: {len(PASSES)}   FAIL: {len(FAILS)}")
    if FAILS:
        for f in FAILS:
            print(f"    ❌ {f}")
        print("\n  RESULT: ❌ FAIL")
        return 1
    print("\n  RESULT: ✅ ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
