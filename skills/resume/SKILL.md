---
name: resume-secure
description: RESUME node — the exact resume + MD5 integrity gates. Read before ANY apply or upload. Enforces pick/upload/post md5 == known-good. Trigger — "resume", "md5", "upload resume".
parent: skills/SKILL.md
version: 1.0.0
---

# RESUME (MD5-SECURE + PROFESSIONAL FILENAME)

## ⚠️ THE FILENAME RULE (recruiters reject "resume.pdf")
- The resume MUST be uploaded/attached with the **professional filename `Your_Name_Resume.pdf`**.
- ❌ NEVER upload as `resume.pdf` (or `_patched.pdf`) — recruiters filter/judge candidates by it.
- The hub copy lives at `config/Your_Name_Resume.pdf` and is what every apply uploads.

## THE EXACT RESUME
- **Canonical file:** `config/Your_Name_Resume.pdf`
- **Source of truth:** `config/user.json → resume_path` → `config/answers.py → A['resume']` → `core/resume_secure.RESUME`
- **Known-good MD5:** `YOUR_RESUME_MD5` (persisted in `config/resume.md5`, format `HASH  PATH`)

## UPLOAD METHOD

<sub>single source — user correction 2026-11-05</sub>

**Never let a native file picker open.** A click on an Attach/Upload/Browse button opens the macOS/Windows OS dialog, which lives outside the browser and outside every automation API — the harness cannot dismiss it and the run stalls until timeout.

**Proof (measured on this build's Chromium, 2026-11-05):**
| Method | Files land | OS dialog |
|---|---|---|
| `locator.setInputFiles(path)` on a `display:none` input | ✓ 1 file, 615155 B, 40 ms | **none** (`filechooser` never fired) |
| page-side `File`/`DataTransfer` + `input`/`change` | ✓ 1 file | **none** |
| `.click()` on the Attach button | — | **`filechooser` fired = native picker** |

Playwright attaches files directly to the `<input type=file>` element instead of interacting with the OS native dialog, so the input can be `display:none`, `opacity:0`, or clipped — hiddenness is irrelevant. If a chooser does get opened, dismiss it programmatically with `chooser.setFiles([])`; never leave it for the user to close.

**Order of preference (stop at the first that works):**
1. `page.locator('input[type=file]').first().setInputFiles(BEFORE_UPLOAD())` — one call, no chooser. Use `browser_run_code_unsafe` with `const { page } = cloak;` (not an `async (page) => {}` wrapper).
2. Shadow-root / off-DOM input: resolve the handle first (`bframe.evaluateHandle(...)` → `asElement()` → `setInputFiles`), as in `recipes/smartrecruiters.md`.
3. No reachable input at all: page-side `DataTransfer` assignment + dispatch `input`/`change`.
4. Last resort only: `waitForEvent('filechooser')` + click + `chooser.setFiles(path)` — the chooser object is Playwright-side so no window survives, but the click may flash the OS dialog.

- **Never** `browser_file_upload` (chooser-based, 5 s timeout) and **never** ask the user to pick the file.
- After insertion, read back the ATS filename/attachment chip. If no usable file input exists, stop and record the exact blocker.

## THE 3 GATES (module: `core/resume_secure.py`)
```text
PICK(status)          → BEFORE opening the apply form.          Verifies source exists + hashes to known-good.
BEFORE_UPLOAD()       → IMMEDIATELY before handing bytes to ATS. Returns the verified path to upload.
POST()                → right after submit.                      Re-verifies the local copy hasn't corrupted.
```
- `md5_of(path)`, `verify_md5(path, expected)`, `known_good()` for ad-hoc checks.
- `upload_target()` → the exact file to upload (returns `config/Your_Name_Resume.pdf`, a verified byte-copy with the
  PROFESSIONAL filename — because macOS TCC can block the browser reading `~/Downloads`, and recruiters reject `resume.pdf`).
- **Auto-heal:** if the hub copy is missing/corrupted/mismatched the module re-copies from canonical and re-verifies.

## DO / DON'T
- ✅ Import from `core.resume_secure` in EVERY apply script:
  ```python
  from core.resume_secure import BEFORE_UPLOAD, POST, PICK
  PICK()                           # 1. before form
  ...                              # fill
  ctl({"op": "upload_cdp", "path": BEFORE_UPLOAD()})   # 2. before upload
  POST()                           # 3. after submit
  ```
- ✅ If MD5 mismatch raises `MD5MismatchError` → STOP, do not upload. Diagnose: is `resume_path`
  pointing at the canonical file? Is the file intact (re-download)?
- ❌ NEVER hardcode `config/resume.pdf` (or any path) in an apply script — always resolve via the module.
- ❌ NEVER setInputFiles a resume without `BEFORE_UPLOAD()` gating it.

## Dry-run / check
```bash
.venv/bin/python core/resume_secure.py   # prints md5 + runs pick→upload→post gates
```

## VERIFY the MD5 anytime
```bash
md5 config/Your_Name_Resume.pdf
# expect YOUR_RESUME_MD5
```
