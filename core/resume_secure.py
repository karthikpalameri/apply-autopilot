#!/usr/bin/env python3
"""core/resume_secure.py — THE resume gate. Single source of truth for the resume file.

ENFORCES the exact resume + MD5 integrity at THREE points of every apply:
  1. PICK    (before we start)      — source file exists & matches the known-good MD5
  2. UPLOAD  (the exact bytes sent) — the file handed to the ATS matches the canonical copy
  3. POST    (after submit)         — uploaded copy still matches (no corruption / wrong file)

The canonical resume lives in config/user.json -> resume_path (exact absolute path),
NOT a generic "resume.pdf". MD5 is stored/validated against config/resume.md5.

USAGE (every apply script, DRY):
    from core.resume_secure import (
        PICK, UPLOAD, POST,           # gate enforcers (raise on mismatch)
        resolve, md5_of, verify_md5,  # helpers
        RESUME,                       # absolute path to the exact resume to upload
    )
    PICK()          # call once, before opening the form
    UPLOAD()        # call immediately before the upload step
    POST()          # call right after submit
"""
import hashlib, os, shutil, sys

# anchor: hub root = parent of core/
HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HUB)

try:
    from config.answers import RESUME as _RESUME_CFG, RESUME_NAME as _RESUME_NAME
    RESUME = os.path.abspath(os.path.expanduser(_RESUME_CFG or ""))
except Exception:
    RESUME = ""

MDPATH = os.path.join(HUB, "config", "resume.md5")
# The ATS/UPLOAD copy MUST keep the PROFESSIONAL filename (recruiters reject "resume.pdf").
# Browser can't always read ~/Downloads, so we copy the canonical into config with the
# EXACT intended filename (e.g. Firstname_Lastname_Role.pdf, from config/user.json) and
# update that if the source changes.

def _upload_name():
    name = (_RESUME_NAME or "").strip() or "Firstname_Lastname_Role.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name

UPLOAD_NAME = _upload_name()
HUB_COPY = os.path.join(HUB, "config", UPLOAD_NAME)


def md5_of(path, block=2**20):
    """Hex MD5 of a file. Fast, streaming. Returns None if unreadable."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for c in iter(lambda: f.read(block), b""):
                h.update(c)
        return h.hexdigest()
    except Exception:
        return None


def known_good():
    """The trusted MD5 hash + source path, from config/resume.md5 (format: HASH  PATH)."""
    try:
        with open(MDPATH) as f:
            line = f.read().strip()
        parts = line.split(None, 1)
        return parts[0], (parts[1].strip() if len(parts) > 1 else RESUME)
    except Exception:
        return None, None


def verify_md5(path, expected):
    """True if file at path hashes to expected. Used at pick/upload/post."""
    return md5_of(path) == (expected or "").lower()


def resolve():
    """Return the absolute path of the resume we must use, verified to exist."""
    if not RESUME or not os.path.exists(RESUME):
        raise FileNotFoundError(f"resume_path in config/user.json does NOT exist: {RESUME}")
    return RESUME


class MD5MismatchError(RuntimeError):
    pass


def _ensure_md5_stored():
    """Write config/resume.md5 from the canonical source if missing (first run)."""
    if os.path.exists(MDPATH):
        return
    h = md5_of(RESUME)
    if not h:
        raise MD5MismatchError(f"cannot hash canonical resume: {RESUME}")
    with open(MDPATH, "w") as f:
        f.write(f"{h}  {RESUME}\n")
    print(f"[resume-md5] stored known-good MD5 {h} -> {MDPATH}", flush=True)


def _ensure_hub_copy(force=False):
    """The upload target dir (macOS TCC: browser can't read ~/Downloads). Copy if stale."""
    if not HUB_COPY:
        return None
    need_copy = force
    if not os.path.exists(HUB_COPY):
        need_copy = True
    elif md5_of(HUB_COPY) != md5_of(RESUME):
        need_copy = True  # mismatched/mangled -> refresh from canonical
    if need_copy:
        shutil.copy2(RESUME, HUB_COPY)
        print(f"[resume-md5] copied canonical -> {HUB_COPY} (integrity restored)", flush=True)
    return HUB_COPY


def PICK(with_copy=True):
    """GATE 1 — verify the resume we are ABOUT to apply with. Call before opening the form."""
    _ensure_md5_stored()
    good, src = known_good()
    path = resolve()
    if with_copy:
        path = _ensure_hub_copy() or path
    if not verify_md5(path, good):
        _ensure_hub_copy(force=True)          # retry once from canonical
        if not verify_md5(path, good):
            raise MD5MismatchError(
                f"PICK gate FAILED md5 {md5_of(path)} != {good} for {path}")
    print(f"[resume-md5] PICK ✓ {good}  {os.path.basename(RESUME)} -> upload name {UPLOAD_NAME}", flush=True)
    return good


def upload_target():
    """Resolve the exact file the apply script should hand to the ATS (after a PICK-safe copy)."""
    PICK(with_copy=True)
    target = HUB_COPY if os.path.exists(HUB_COPY) else RESUME
    return target


def BEFORE_UPLOAD():
    """GATE 2 — right before giving bytes to the ATS. Returns the path to upload."""
    good, _ = known_good()
    target = upload_target()
    if not verify_md5(target, good):
        raise MD5MismatchError(f"UPLOAD gate FAILED md5 for {target}")
    return target


def POST():
    """GATE 3 — after submit, verify a local copy of the resume still matches (no silent corrupt)."""
    good, _ = known_good()
    target = HUB_COPY if os.path.exists(HUB_COPY) else RESUME
    h = md5_of(target)
    if h != good:
        raise MD5MismatchError(f"POST gate FAILED md5 {h} != {good} (resume corrupted/failed upload)")
    print(f"[resume-md5] POST ✓ {good}", flush=True)
    return True


# Back-compat: scripts that just want the verified path
def verify_all():
    """Run all three gates in sequence (for a single-shot script / dry-run check)."""
    PICK()
    BEFORE_UPLOAD()
    POST()


if __name__ == "__main__":
    print(f"resume path: {RESUME}")
    print(f"md5 of source:       {md5_of(RESUME)}")
    print(f"md5 of hub copy:     {md5_of(HUB_COPY)}")
    print("known-good:", known_good())
    verify_all()
    print("\n✅ all three gates passed")
