#!/usr/bin/env python3
"""setup.py — one-time interactive wizard (cross-platform: macOS / Linux / Windows).

Walks you through YOUR details step by step and writes everything into
`config/user.json` (git-ignored, chmod 600 on POSIX) + `config/resume.md5`
+ `core/.env`. No secrets are ever written to a tracked file.

Run:
    python3 setup.py            # interactive
    python3 setup.py --check    # print what's configured (never prints secrets)
"""
import getpass
import hashlib
import json
import os
import shutil
import sys

HUB = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(HUB, "config", "user.json")
MD5_PATH = os.path.join(HUB, "config", "resume.md5")
ENV_PATH = os.path.join(HUB, "core", ".env")

IS_WINDOWS = os.name == "nt"


def ask(prompt, default="", secret=False, required=False):
    """Prompt for a value. Returns default on empty. Secret -> hidden input."""
    d = f" [{default}]" if default else ""
    while True:
        try:
            v = (getpass.getpass(f"{prompt}{d}: ") if secret else input(f"{prompt}{d}: ")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)
        if v:
            return v
        if default:
            return default
        if required:
            print("  (required — please enter a value)")
            continue
        return ""


def ask_bool(prompt, default_yes=True):
    suffix = " [Y/n]" if default_yes else " [y/N]"
    v = input(prompt + suffix + ": ").strip().lower()
    if not v:
        return default_yes
    return v in ("y", "yes", "1", "true")


def ask_int(prompt, default):
    v = ask(prompt, str(default))
    try:
        return int(v)
    except ValueError:
        print(f"  ({v!r} is not a number — using {default})")
        return default


def chmod600(path):
    if not IS_WINDOWS:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def slugify(s):
    out = "".join(c if c.isalnum() else "_" for c in s).strip("_")
    return out or "Candidate"


def derive_resume_filename(full_name, role):
    first = full_name.strip().split()[0] if full_name.strip() else "Candidate"
    last = full_name.strip().split()[-1] if len(full_name.strip().split()) > 1 else ""
    base = f"{first}_{last}_{slugify(role)}" if last else f"{first}_{slugify(role)}"
    return f"{base}.pdf"


def setup_interactive():
    print("=" * 64)
    print("APPLY AUTOPILOT — SETUP (one time)")
    print("Everything is stored locally in config/user.json. Nothing is sent anywhere.")
    print("=" * 64)

    cfg = {}

    print("\n--- 1/6  Identity ---")
    cfg["full_name"] = ask("Full name", "Jane Doe", required=True)
    cfg["email"] = ask("Email (used on applications)", "jane.doe@example.com", required=True)
    cfg["phone"] = ask("Phone (with country code)", "+91 00000 00000")
    cfg["location"] = ask("Current city", "Bengaluru")
    cfg["city"] = cfg["location"]
    cfg["state"] = ask("State / province", "Karnataka")
    cfg["country"] = ask("Country", "India")
    cfg["postal_code"] = ask("Postal code", "")
    cfg["address"] = ask("Full street address (optional, for forms that require it)", "")
    cfg["dob"] = ask("Date of birth YYYY-MM-DD (optional)", "")
    cfg["gender"] = ask("Gender (Male/Female/Other — used for legal forms)", "Female")

    print("\n--- 2/6  Experience & target role ---")
    cfg["current_role"] = ask("Current / most recent job title", "Senior QA Automation Engineer")
    cfg["current_company"] = ask("Current / most recent company", "Your Current Company")
    cfg["years_exp"] = ask_int("Years of experience", 8)
    cfg["summary"] = ask(
        "One-line profile summary (used on profiles)",
        f"Senior {cfg['current_role']} with {cfg['years_exp']} yrs: automation, API testing, CI/CD")
    cfg["linkedin_url"] = ask("LinkedIn profile URL", "https://www.linkedin.com/in/janedoe")
    cfg["github"] = ask("GitHub URL (optional)", "https://github.com/janedoe")

    print("\n--- 3/6  Compensation & notice ---")
    cfg["current_ctc_lpa"] = ask_int("Current CTC in LPA (leave 0 if not applicable)", 0)
    expected_default = round(cfg["current_ctc_lpa"] * 1.22, 1) if cfg["current_ctc_lpa"] else 0
    cfg["expected_ctc_lpa"] = ask_int("Expected CTC in LPA", expected_default or 30)
    cfg["expected_ctc"] = int(cfg["expected_ctc_lpa"] * 100000)
    cfg["notice_days"] = ask_int("Notice period in days (0 if already resigned)", 0)
    cfg["last_working_day"] = ask("Last working day YYYY-MM-DD (if serving notice)", "")
    cfg["availability"] = ask("Availability text for forms", "Immediate")

    print("\n--- 4/6  Resume ---")
    default_resume = os.path.join(os.path.expanduser("~"), "Downloads", "Resume.pdf")
    resume_path = ask("Absolute path to your resume PDF", default_resume)
    resume_path = os.path.abspath(os.path.expanduser(resume_path))
    if not os.path.exists(resume_path):
        print(f"  ⚠️  Not found: {resume_path} — you can copy it there later and re-run setup.")
    cfg["resume_path"] = resume_path
    cfg["resume_filename"] = derive_resume_filename(cfg["full_name"], cfg["current_role"])

    print("\n--- 5/6  Education (for Greenhouse/Phenom forms) ---")
    cfg["degree"] = ask("Degree level", "Bachelor")
    cfg["discipline"] = ask("Field of study", "Computer Science")
    cfg["school"] = ask("School / university", "Your University")
    cfg["edu_start_month"] = ask("Start month (e.g. August)", "August")
    cfg["edu_end_month"] = ask("End month (e.g. May)", "May")
    cfg["edu_start_year"] = ask_int("Start year", 2013)
    cfg["edu_end_year"] = ask_int("End year", 2017)

    print("\n--- 6/6  Credentials (stored ONLY in local config/user.json + core/.env) ---")
    print("""
Gmail is used ONLY with your consent, for FOUR specific things:
  1. READ OTP / verification codes during company ATS sign-ups
  2. READ application confirmations (so we only count real submissions)
  3. REGISTER / log into company ATS accounts (Workday/Greenhouse/Lever…)
  4. DRAFT and (only if you approve) SEND cold emails to recruiters
Your Gmail password is never stored in the repository — only in this local
chmod-600 config file or the logged-in browser session.
""")
    gmail_consent = ask_bool("Consent to the agent using Gmail for the 4 purposes above?")
    cfg["gmail_consent"] = gmail_consent
    cfg["linkedin_user"] = ask("LinkedIn login email", cfg["email"])
    cfg["linkedin_pass"] = ask("LinkedIn password", "", secret=True)
    cfg["gmail_user"] = ask("Gmail address", cfg["email"])
    cfg["gmail_app_pw"] = ask("Gmail App Password (IMAP — optional)", "", secret=True)
    cfg["capsolver_key"] = ask("CapSolver API key (optional, for captchas)", "", secret=True)

    print("\n--- Application answers (India) ---")
    cfg["application_answers_india"] = {
        "work_authorization_without_sponsorship": "Yes" if ask_bool("Legally authorized to work without sponsorship?") else "No",
        "temporary_authorization_future_sponsorship": "No",
        "employment_restrictions": "No",
        "other_business_or_employment": "No",
        "previous_cigna_employment": "No",
        "previous_cigna_contracting": "No",
        "government_official_relationship": "No",
        "cigna_employee_relationship": "No",
        "citizenship_status": ask("Citizenship status", "Citizen (India)"),
    }

    # ---- persist ----
    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    chmod600(CFG_PATH)

    write_resume_md5(cfg)
    write_env(cfg)

    print("\n" + "=" * 64)
    print("✅ Saved to config/user.json (chmod 600)")
    if cfg["resume_filename"]:
        print(f"✅ Resume will be uploaded as: {cfg['resume_filename']}")
    if cfg["capsolver_key"]:
        print("✅ CapSolver key written to core/.env")
    print("\nNext steps:")
    print("  1. python3 hub.py install   # create venv + install all dependencies")
    print("  2. python3 hub.py start     # start the browser stack")
    print("  3. python3 hub.py health    # verify everything is green")
    print("=" * 64)


def write_resume_md5(cfg):
    """Persist config/resume.md5 from the canonical resume (used by core/resume_secure.py)."""
    resume = os.path.abspath(os.path.expanduser(cfg.get("resume_path", "")))
    if os.path.exists(resume):
        h = hashlib.md5()
        with open(resume, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        with open(MD5_PATH, "w", encoding="utf-8") as f:
            f.write(f"{h.hexdigest()}  {resume}\n")
        print(f"✅ Wrote config/resume.md5 ({h.hexdigest()[:12]}…)")
    else:
        print("⚠️  Resume not found — config/resume.md5 not written (fix resume_path, re-run setup).")


def write_env(cfg):
    if cfg.get("capsolver_key"):
        os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(f"CAPSOLVER_API_KEY={cfg['capsolver_key']}\n")
        chmod600(ENV_PATH)


def cmd_check():
    """Print a redacted view of the current config (no secrets)."""
    if not os.path.exists(CFG_PATH):
        print("❌ Not configured — run: python3 setup.py")
        sys.exit(1)
    cfg = json.load(open(CFG_PATH, encoding="utf-8"))
    redacted = dict(cfg)
    for k in ("linkedin_pass", "gmail_app_pw", "capsolver_key"):
        redacted[k] = "***" if redacted.get(k) else "(empty)"
    print(json.dumps(redacted, indent=2, ensure_ascii=False))
    print("resume exists:", os.path.exists(os.path.expanduser(cfg.get("resume_path", ""))))
    print("resume.md5 exists:", os.path.exists(MD5_PATH))


if __name__ == "__main__":
    if "--check" in sys.argv:
        cmd_check()
    else:
        setup_interactive()
