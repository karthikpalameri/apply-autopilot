---
name: resume-secure
description: RESUME node — the exact resume + MD5 integrity gates. Read before ANY apply or upload.
  Enforces pick/upload/post md5 == known-good. Trigger: "resume", "md5", "upload resume".
parent: skills/SKILL.md
version: 1.0.0
---

# RESUME (MD5-SECURE + PROFESSIONAL FILENAME)

## ⚠️ THE FILENAME RULE (recruiters reject "resume.pdf")
- The resume MUST be uploaded/attached with the **professional filename `Firstname_Lastname_Role.pdf`**.
- ❌ NEVER upload as `resume.pdf` (or `_patched.pdf`) — recruiters filter/judge candidates by it.
- The hub copy lives at `config/Firstname_Lastname_Role.pdf` and is what every apply uploads.

## THE EXACT RESUME
- **Canonical file:** `<HUB_ROOT>/config/Firstname_Lastname_Role.pdf`
- **Source of truth:** `config/user.json → resume_path` → `config/answers.py (RESUME / RESUME_NAME)` → `core/resume_secure.RESUME`
- **Known-good MD5:** `<GENERATED_ON_SETUP>` (persisted in `config/resume.md5`, format `HASH  PATH`)

## UPLOAD METHOD (user correction)
- Prefer direct HTML/Playwright/Selenium-style insertion into an existing `input[type=file]` via `setInputFiles(BEFORE_UPLOAD())`; on this MCP build use `browser_run_code_unsafe` with `const { page } = cloak;` rather than an `async (page) => {}` wrapper.
- If direct Playwright attachment is unavailable, use page-side `File`/`DataTransfer` assignment and dispatch `input`/`change`; never open a native file-picker popup or ask the user to select a file.
- After insertion, read back the ATS filename/attachment chip. If no usable file input exists, stop and record the exact blocker.

## THE 3 GATES (module: `core/resume_secure.py`)
```
PICK(status)          → BEFORE opening the apply form.          Verifies source exists + hashes to known-good.
BEFORE_UPLOAD()       → IMMEDIATELY before handing bytes to ATS. Returns the verified path to upload.
POST()                → right after submit.                      Re-verifies the local copy hasn't corrupted.
```
- `md5_of(path)`, `verify_md5(path, expected)`, `known_good()` for ad-hoc checks.
- `upload_target()` → the exact file to upload (returns `config/Firstname_Lastname_Role.pdf`, a verified byte-copy with the
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
# macOS/Linux
md5 config/Firstname_Lastname_Role.pdf
# Windows
certutil -hashfile config\Firstname_Lastname_Role.pdf MD5
# expect the hash stored in config/resume.md5
```
