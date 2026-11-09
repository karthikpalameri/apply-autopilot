"""Guard: resume uploads must INJECT into input[type=file], never open a native picker.

Why this exists
---------------
A click on an Attach / Upload / Browse button opens the OS file dialog (macOS
NSSavePanel / Windows GetOpenFileName). That window is outside the browser, so no
automation API can dismiss it and the run stalls until timeout. Measured on this
build's Chromium (2026-11-05): `setInputFiles` on a `display:none` input landed a
615155-byte file in 40 ms and the `filechooser` event never fired; clicking the
button fired `filechooser`, i.e. the native picker. See skills/resume/SKILL.md#upload-method.

Allowed:   `setInputFiles(path)` / `set_input_files(path)` / `files = DataTransfer`
           / `chooser.setFiles(path)`  (chooser object is Playwright-side).
Flagged:   `.click()` on a control whose name is Attach / Upload / Browse / Choose file,
           and clicks on `input[type=file]` itself.

Usage:
    .venv/bin/python core/lint_upload.py          # live code only
    .venv/bin/python core/lint_upload.py --all    # include archive/ and scratch/
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent

SKIP_PARTS = {"third_party", ".venv", "node_modules", ".git", "logs", "data", "__pycache__"}
SKIP_WITHOUT_ALL = {"archive", "scratch", "runtime/extensions", "runtime/extensions/buster"}
SUFFIXES = {".py", ".js", ".mjs", ".sh"}

SAFE = (
    "setInputFiles",
    "set_input_files",
    "DataTransfer",
    "setFiles(",  # chooser.setFiles(...) — Playwright-side, no OS window
)

# A click call on this line.
CLICK = re.compile(r"(?i)(\.click\(|\.click\(\)|mouse_click|click_xy|\.hover\()")

# The click target names an upload control: Attach / Upload / Browse / Choose file.
UPLOAD_TARGET = re.compile(
    r"""(?ix)
    (?:getByRole|getByText|get_by_role|get_by_text|locator|querySelector|find|btn|button|label)
    [^\n]{0,120}?
    (?:name\s*:\s*['"][^'"]*(attach|upload|browse|choose|select[\s_-]?file|add[\s_-]?(cv|resume|file))[^'"]*['"]
      |['"][^'"]*(attach|upload|browse|choose[\s_-]?file|select[\s_-]?file)[^'"]*['"]
    )
    """
)

# Clicking a file input directly.
CLICK_FILE_INPUT = re.compile(r"(?i)(input\[type=['\"]?file)")

# A one-liner help string that merely prints a legend.
LEGEND = re.compile(r"(?i)^\s*(print|console\.log|#|\|)")


def _iter_files(include_all: bool):
    for p in HUB.rglob("*"):
        if not p.is_file() or p.suffix not in SUFFIXES:
            continue
        rel = p.relative_to(HUB)
        if set(rel.parts) & SKIP_PARTS:
            continue
        if not include_all and any(str(rel).startswith(s) for s in SKIP_WITHOUT_ALL):
            continue
        # Minified / bundled blobs: one huge line, vendored.
        try:
            st = p.stat()
            if st.st_size > 400_000 or max(len(x) for x in p.read_text(errors="ignore").splitlines()[:1] or [""]) > 5_000:
                continue
        except (OSError, ValueError):
            continue
        yield p, rel


def scan(path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
        s = line.strip()
        if LEGEND.match(s):
            continue
        # Any safe injection API on the line clears it — those are the correct path.
        if any(k in s for k in SAFE):
            continue
        if not CLICK.search(s):
            continue
        if CLICK_FILE_INPUT.search(s) or UPLOAD_TARGET.search(s):
            hits.append((i, s))
    return hits


def main() -> int:
    include_all = "--all" in sys.argv
    violations: list[tuple[Path, int, str]] = []
    for p, rel in _iter_files(include_all):
        for lineno, line in scan(p):
            violations.append((rel, lineno, line))

    if not violations:
        print("[lint_upload] OK — uploads use setInputFiles; no click-on-upload-control.")
        return 0

    print("[lint_upload] FAIL — these clicks can open a native file picker:")
    for rel, lineno, line in violations:
        print(f"  {rel}:{lineno}: {line[:150]}")
    print("\nFix: resolve `input[type=file]` (light DOM or shadow root) and call")
    print("     `setInputFiles(path)`. Procedure: skills/resume/SKILL.md#upload-method")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
