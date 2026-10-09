#!/usr/bin/env python3
"""onboarding.py — resume-first guided setup for Apply Autopilot (cross-platform).

Run:  python3 onboarding.py        (or:  python3 hub.py onboard)

Flow:
  0. Explain WHAT / WHY / HOW (short).
  1. RESUME FIRST — ask for your resume PDF, read everything from it.
     If pypdf is missing we offer to install it.
  2. REVIEW — show everything we extracted and let you confirm each field:
        [Enter] keep   [c] change   [s] skip   [d] done = keep ALL remaining
  3. FILL GAPS — only ask for what the resume didn't contain (compensation,
     notice period, target roles…).
  4. SKILLS — confirm/adjust the skills + achievements we detected.
  5. INTERVIEW — draft your pitch, strengths, weakness, salary answer together.
  6. GMAIL — explain the 4 uses and ask consent + credentials.
  7. ENVIRONMENT — flag missing dependencies and offer to install them.
  8. SAVE — write config/user.json + config/profile.json + config/profile.md.

Everything is saved to git-ignored files only. Nothing is uploaded by setup.
"""
import json
import os
import shutil
import subprocess
import sys

HUB = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HUB)

from setup import ask, ask_bool, ask_int, chmod600, derive_resume_filename  # noqa: E402
import resume_parser as rp  # noqa: E402

CFG_PATH = os.path.join(HUB, "config", "user.json")
PROFILE_PATH = os.path.join(HUB, "config", "profile.json")
PROFILE_MD = os.path.join(HUB, "config", "profile.md")


def section(n, title):
    print("\n" + "=" * 68)
    print(f"  {n}  {title}")
    print("=" * 68)


def heading(t):
    print("\n  • " + t)


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path, data, secret=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    if secret:
        chmod600(path)


# ---------------------------------------------------------------- 0. explain
def explain():
    print("=" * 68)
    print("  🎯 APPLY AUTOPILOT — your personal job-application copilot")
    print("=" * 68)
    print("""
WHAT IT DOES
  Finds relevant openings, verifies they match you, applies with YOUR resume,
  emails recruiters, and tracks every application.

WHY
  Job hunting is 80% repetitive form-filling. This automates the repetitive parts
  (ATS forms, LinkedIn Easy Apply, resume uploads, OTP reads) so you spend your
  energy on choosing roles and talking to recruiters.

HOW (we'll do it together now)
  1. I read your resume → build your profile (you confirm/correct every field).
  2. You run `python3 hub.py install` → all dependencies.
  3. `python3 hub.py start` → browser stack; you log in once.
""")

    existing = load_json(CFG_PATH)
    if existing:
        print("  ℹ️  An existing config was found. You can keep it or rebuild it.")
        if not ask_bool("Re-run the full questionnaire?", False):
            print("  ✅ Keeping existing config. Edit anytime: python3 onboarding.py")
            return "skip"
    return "continue"


# ---------------------------------------------------------------- 1. resume
def ensure_pypdf():
    try:
        import pypdf  # noqa: F401
        return True
    except ImportError:
        print("  ℹ️  I need the `pypdf` library to read your resume PDF.")
        if ask_bool("Install pypdf now (small, pure-Python)?", True):
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "pypdf"])
            if r.returncode == 0:
                print("  ✅ pypdf installed")
                return True
        print("  ⚠️  Skipping resume reading — I'll ask you to type the details instead.")
        return False


def resume_first():
    section("1/8", "Resume first — I'll read everything from it")
    default = os.path.join(os.path.expanduser("~"), "Downloads", "Resume.pdf")
    path = os.path.abspath(os.path.expanduser(ask("Absolute path to your resume PDF", default)))
    if not os.path.exists(path):
        print(f"  ⚠️  Not found: {path}")
        return None, path
    if not ensure_pypdf():
        return None, path
    try:
        data = rp.parse_pdf(path)
        data["resume_path"] = path
        print("\n  ✅ Read your resume. Here's what I extracted:")
        return data, path
    except rp.ParseError as e:
        print(f"  ❌ {e}")
        return None, path


# ---------------------------------------------------------------- 2. review (ABCD)
def _flat_review_items(data):
    edu = data.get("education") or {}
    items = [
        ("full_name", "Full name", data.get("full_name", "")),
        ("email", "Email", data.get("email", "")),
        ("phone", "Phone", data.get("phone", "")),
        ("location", "Location", data.get("location", "")),
        ("current_role", "Current role", data.get("current_role", "")),
        ("years_exp", "Years of experience", str(data.get("years_exp", ""))),
        ("linkedin_url", "LinkedIn", data.get("linkedin_url", "")),
        ("github", "GitHub", data.get("github", "")),
        ("degree", "Degree", edu.get("degree", "")),
        ("school", "School", edu.get("school", "")),
        ("edu_year", "Graduation year", edu.get("year", "")),
        ("summary", "Summary", data.get("summary", "")),
    ]
    return items


def review_extracted(data):
    """Show extracted fields and let the user confirm/correct each one (ABCD)."""
    section("2/8", "Review — confirm or correct what I read")
    items = _flat_review_items(data)
    print("  Here's what I extracted from your resume. For each field:")
    print("    [Enter] ✔ keep   [c] change   [s] skip/clear   [d] done = keep ALL remaining\n")

    result = {}
    i = 0
    while i < len(items):
        key, label, val = items[i]
        shown = val if val and val != "None" else "(empty)"
        print(f"  [{i + 1}/{len(items)}] {label}: {shown}")
        choice = input("      → ").strip().lower()
        if choice == "":
            result[key] = val
            i += 1
        elif choice == "c":
            new = input(f"      new {label}: ").strip()
            result[key] = new if new else val
            i += 1
        elif choice == "s":
            result[key] = ""
            i += 1
        elif choice == "d":
            for k2, _, v2 in items[i:]:
                result[k2] = v2
            print("  ✅ Keeping all remaining fields as shown.")
            break
        else:
            print("      (enter=keep · c=change · s=skip · d=done-all)")
    return result


# ---------------------------------------------------------------- 3. gaps
def fill_gaps(cfg):
    section("3/8", "Fill the gaps — only what the resume didn't say")
    req = {
        "full_name": ("Full name", "Jane Doe"),
        "email": ("Email", "jane.doe@example.com"),
        "phone": ("Phone (with country code)", "+91 00000 00000"),
        "location": ("Current city", "Bengaluru"),
        "current_role": ("Current / most recent job title", "Senior QA Automation Engineer"),
        "years_exp": ("Years of experience", "8"),
    }
    for key, (label, default) in req.items():
        if not str(cfg.get(key, "")).strip():
            cfg[key] = ask(label, default, required=(key in ("full_name", "email")))

    cfg["current_company"] = ask("Current / most recent company", cfg.get("current_company", ""))
    cfg["state"] = ask("State / province", cfg.get("state", "Karnataka"))
    cfg["country"] = ask("Country", cfg.get("country", "India"))
    cfg["postal_code"] = ask("Postal code", cfg.get("postal_code", ""))
    cfg["address"] = ask("Street address (optional)", cfg.get("address", ""))
    cfg["dob"] = ask("Date of birth YYYY-MM-DD (optional)", cfg.get("dob", ""))
    cfg["gender"] = ask("Gender (Male/Female/Other)", cfg.get("gender", "Female"))

    heading("Compensation & notice (not on a resume)")
    cfg["current_ctc_lpa"] = ask_int("Current CTC in LPA (0 if n/a)", cfg.get("current_ctc_lpa", 0))
    default_exp = round(cfg["current_ctc_lpa"] * 1.22, 1) if cfg.get("current_ctc_lpa") else 30
    cfg["expected_ctc_lpa"] = ask_int("Expected CTC in LPA", cfg.get("expected_ctc_lpa", default_exp))
    cfg["expected_ctc"] = int(cfg["expected_ctc_lpa"] * 100000)
    cfg["notice_days"] = ask_int("Notice period in days (0 if already resigned)", cfg.get("notice_days", 0))
    cfg["last_working_day"] = ask("Last working day YYYY-MM-DD (if serving notice)", cfg.get("last_working_day", ""))
    cfg["availability"] = ask("Availability text for forms", cfg.get("availability", "Immediate"))

    heading("Target roles & preferences")
    target = ask("Target roles (comma-separated)", cfg.get("current_role", ""))
    cfg["target_roles"] = [t.strip() for t in target.split(",") if t.strip()] or [cfg["current_role"]]
    locs = ask("Target locations (comma-separated)", cfg.get("location", "Bengaluru"))
    cfg["target_locations"] = [l.strip() for l in locs.split(",") if l.strip()]
    cfg["remote_pref"] = ask("Remote / hybrid / onsite preference", cfg.get("remote_pref", "Hybrid"))
    cfg["resume_path"] = cfg.get("resume_path") or ask("Resume PDF path (again, if missing)", "")
    if cfg.get("full_name"):
        cfg["resume_filename"] = derive_resume_filename(cfg["full_name"], cfg["current_role"])


# ---------------------------------------------------------------- 4. skills
def _pick_skills(skills_map):
    """Show detected skills per category and let the user add/remove."""
    confirmed = {}
    for cat, label in [
        ("languages", "Programming languages"),
        ("automation_frameworks", "Automation frameworks"),
        ("api_testing", "API testing tools"),
        ("performance", "Performance tools"),
        ("cicd", "CI/CD & DevOps"),
        ("cloud", "Cloud"),
        ("databases", "Databases"),
        ("tools_other", "Other tools / practices"),
        ("domains", "Domains"),
    ]:
        found = skills_map.get(cat, [])
        print(f"\n  {label}: {', '.join(found) if found else '(none detected)'}")
        v = input("      add/remove (comma-separated; Enter to keep): ").strip()
        final = list(found)
        if v:
            for part in [p.strip() for p in v.split(",") if p.strip()]:
                if part.startswith("-"):
                    final = [x for x in final if x.lower() != part[1:].strip().lower()]
                elif part and part not in final:
                    final.append(part)
        confirmed[cat] = final
    return confirmed


def review_skills(profile, data):
    section("4/8", "Skills — confirm what I detected")
    profile["skills"] = _pick_skills((data.get("skills") or {}))
    ach = data.get("achievements") or []
    if ach:
        print("\n  Achievements detected (you can edit):")
        for i, a in enumerate(ach, 1):
            print(f"    {i}. {a}")
    else:
        print("\n  No achievements detected — add a few with numbers (interview gold).")
    profile["achievements"] = []
    for i in range(1, 4):
        default = ach[i - 1] if i - 1 < len(ach) else ""
        a = input(f"  Achievement {i}" + (f" [{default}]" if default else "") + ": ").strip() or default
        if a:
            profile["achievements"].append(a)
        elif not default and i > 1:
            break
    certs = input("  Certifications (comma-separated; Enter for none): ").strip()
    profile["certifications"] = [c.strip() for c in certs.split(",") if c.strip()]


# ---------------------------------------------------------------- 5. interview
def grill_interview(profile, cfg):
    section("5/8", "Interview — let's write your answers together")
    profile["pitch"] = ask("Tell me about yourself (Enter and I'll draft one):", "")
    profile["strengths"] = ask("Top 2-3 strengths:", "")
    profile["weakness"] = ask("A real weakness + how you're improving:", "")
    profile["why_leave"] = ask("Why are you looking for a change?", "")
    profile["why_hire"] = ask("Why should a company hire YOU (one line)?", "")
    profile["salary_answer"] = ask(
        "How do you answer 'salary expectation'?",
        f"{cfg.get('expected_ctc_lpa', 'X')} LPA (slightly negotiable)")


# ---------------------------------------------------------------- 6. gmail
def collect_gmail(profile, cfg):
    section("6/8", "Gmail access — read this carefully")
    print("""
I use Gmail for FOUR specific things, only with your consent:

  1. READ OTP / verification codes   — company ATS sites email a 6-digit code
     during account sign-up; I read it so you don't copy-paste by hand.
  2. READ application confirmations  — to VERIFY an application really went
     through before I count it as "applied".
  3. REGISTER / log into company ATS  — Workday/Greenhouse/Lever often need
     account creation with email verification.
  4. DRAFT + (only if you approve) SEND cold emails to recruiters.

Your Gmail password is NEVER stored in the repository — only in this local
chmod-600 config file or the logged-in browser session.
""")
    consent = ask_bool("Do you consent to Gmail for the 4 purposes above?", True)
    profile["gmail_consent"] = consent
    profile["gmail_user"] = ask("Gmail address", cfg.get("email"))
    profile["gmail_app_pw"] = ask("Gmail App Password (IMAP — optional, faster reads)", "", secret=True)
    if not consent:
        print("  ⚠️  Gmail disabled — OTP/confirmation reads and cold emails will ask you to do them manually.")
    else:
        print("  ✅ Gmail consent recorded. Revoke anytime by deleting gmail_consent in config/user.json.")

    profile["linkedin_user"] = ask("LinkedIn login email", cfg.get("email"))
    profile["linkedin_pass"] = ask("LinkedIn password (stored locally only)", "", secret=True)
    profile["capsolver_key"] = ask("CapSolver API key (optional, for captchas)", "", secret=True)


# ---------------------------------------------------------------- 7. environment
def env_report():
    """Return a list of (name, ok, fix) tuples for missing dependencies."""
    checks = []
    checks.append((".venv", os.path.exists(os.path.join(HUB, ".venv")),
                   "python3 hub.py install"))
    checks.append(("node", bool(shutil.which("node")),
                   "install from https://nodejs.org (LTS)"))
    checks.append(("npx", bool(shutil.which("npx")), "bundled with Node.js"))
    checks.append(("pi (coding agent)", bool(shutil.which("pi")),
                   "see docs/INSTALL.md to install pi"))
    checks.append(("tesseract (OCR)", bool(shutil.which("tesseract")),
                   "brew install tesseract | apt install tesseract-ocr | winget install tesseract"))
    checks.append(("docker (SearXNG, optional)", bool(shutil.which("docker")),
                   "install Docker Desktop (optional)"))
    return checks


def env_check():
    section("7/8", "Environment — missing pieces get flagged")
    missing = []
    for name, ok, fix in env_report():
        print(f"  {'✅' if ok else '❌'} {name}" + ("" if ok else f"  →  {fix}"))
        if not ok:
            missing.append((name, fix))
    if missing:
        if ask_bool("\nSome dependencies are missing — run `python3 hub.py install` now?", True):
            subprocess.run([sys.executable, "hub.py", "install"])
    else:
        print("\n  ✅ Environment is ready.")


# ---------------------------------------------------------------- generation
def generate_artifacts(cfg, profile):
    years = profile.get("years_exp") or cfg.get("years_exp") or 0
    role = cfg.get("current_role") or "QA Engineer"
    company = cfg.get("current_company") or "my current company"
    langs = ", ".join(profile.get("skills", {}).get("languages", []) or ["Java", "Python"]) or "Java, Python"
    frameworks = ", ".join(profile.get("skills", {}).get("automation_frameworks", []) or ["Selenium", "Playwright"])
    tools = ", ".join((profile.get("skills", {}).get("api_testing", []) or ["Postman"])
                      + (profile.get("skills", {}).get("cicd", []) or ["CI/CD"]))
    domains = profile.get("skills", {}).get("domains", []) or []

    if not profile.get("pitch"):
        profile["pitch"] = (f"I'm a {role} with {years}+ years building reliable test automation. "
                            f"At {company} I work on {(domains[0] if domains else 'product')} quality using "
                            f"{frameworks}, {langs}, and {tools}. I care about shipping confidence, not just test cases.")
    if not profile.get("why_hire"):
        profile["why_hire"] = (f"I turn flaky manual QA into fast, deterministic automation "
                               f"({frameworks}, {langs}) and I own quality end-to-end.")
    if not profile.get("weakness"):
        profile["weakness"] = "I sometimes over-engineer frameworks; I now timebox design and ship the MVP first."

    all_skills = []
    for cat in ("languages", "automation_frameworks", "api_testing", "performance", "cicd",
                "cloud", "databases", "tools_other"):
        all_skills += profile.get("skills", {}).get(cat, []) or []
    seen, key_skills = set(), []
    for s in all_skills:
        if s and s.lower() not in seen:
            seen.add(s.lower())
            key_skills.append(s)
    profile["key_skills"] = ", ".join(key_skills)[:249]
    profile["headline"] = (f"{role} | {years} yrs | {frameworks} | {langs} | "
                           f"{(domains[0] if domains else 'Product')}")
    profile["summary"] = profile["pitch"]

    profile["cold_email"] = {
        "subject": f"Application – {role} – {cfg.get('location', '')} – {cfg.get('full_name', '')} ({years} yrs)",
        "body": (
            f"Dear <Name>,\n\n"
            f"I hope this finds you well. I came across your opening for a {role} and would\n"
            f"love to be considered. I bring {years} years of experience, most recently at\n"
            f"{company}, where I built and maintained {frameworks} automation for "
            f"{(domains[0] if domains else 'product')} quality.\n\n"
            f"My core skills are {langs}, {frameworks}, and {tools}. My resume is attached.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Warm regards,\n{cfg.get('full_name', '')}\n{cfg.get('phone', '')} · {cfg.get('email', '')}"),
    }
    return profile


def write_profile_md(cfg, profile):
    sk = profile.get("skills", {})
    lines = [
        "# Your profile (auto-generated by onboarding.py — git-ignored)",
        "",
        "## Headline",
        f"`{profile.get('headline', '')}`",
        "",
        "## Summary / elevator pitch",
        profile.get("summary", ""),
        "",
        "## Key skills (Naukri ≤250 chars)",
        f"`{profile.get('key_skills', '')}`",
        "",
        "## Strengths",
        profile.get("strengths", ""),
        "",
        "## Weakness + improvement",
        profile.get("weakness", ""),
        "",
        "## Why I'm looking",
        profile.get("why_leave", ""),
        "",
        "## Why hire me",
        profile.get("why_hire", ""),
        "",
        "## Salary expectation answer",
        profile.get("salary_answer", ""),
        "",
        "## Achievements",
    ]
    for a in profile.get("achievements", []) or ["(none recorded)"]:
        lines.append(f"- {a}")
    lines += [
        "",
        "## Certifications",
        ", ".join(profile.get("certifications", []) or ["(none)"]),
        "",
        "## Skills by category",
    ]
    for cat, label in [("languages", "Languages"), ("automation_frameworks", "Automation"),
                       ("api_testing", "API testing"), ("performance", "Performance"),
                       ("cicd", "CI/CD"), ("cloud", "Cloud"), ("databases", "Databases"),
                       ("tools_other", "Other"), ("domains", "Domains")]:
        vals = sk.get(cat, []) or []
        if vals:
            lines.append(f"- **{label}:** {', '.join(vals)}")
    lines += [
        "",
        "## Cold email (draft)",
        f"Subject: {profile.get('cold_email', {}).get('subject', '')}",
        "",
        profile.get("cold_email", {}).get("body", ""),
        "",
        "---",
        "Regenerate anytime: `python3 onboarding.py`",
    ]
    with open(PROFILE_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✅ wrote config/profile.md")


# ---------------------------------------------------------------- 8. save + finish
def save_and_finish(cfg, profile):
    section("8/8", "Save & summary")
    save_json(CFG_PATH, cfg, secret=True)
    save_json(PROFILE_PATH, profile, secret=True)
    write_profile_md(cfg, profile)

    print("\n" + "=" * 68)
    print("  ✅ PROFILE SAVED — you will NOT be asked these again.")
    print("=" * 68)
    print(f"  • config/user.json     (identity + credentials, chmod 600)")
    print(f"  • config/profile.json  (skills, achievements, interview answers)")
    print(f"  • config/profile.md    (your profile + interview cheat sheet — open this!)")
    print(f"  • resume upload name:  {cfg.get('resume_filename', '')}")
    print(f"  • Gmail consent:       {'✅ yes' if profile.get('gmail_consent') else '❌ no'}")

    print("\n  Your headline:")
    print(f"    {profile.get('headline', '')}")
    print("\n  Your summary:")
    print(f"    {profile.get('summary', '')}")

    print("\n  Next steps:")
    print("    1. python3 hub.py install")
    print("    2. python3 hub.py start")
    print("    3. python3 hub.py health")
    print("\n  Edit your profile later:  python3 onboarding.py")


# ---------------------------------------------------------------- main
def main():
    r = explain()
    if r == "skip":
        return 0

    data, resume_path = resume_first()
    if data is None:
        print("\n  (No problem — I'll ask you directly for everything.)")
        data = {}

    cfg = {"resume_path": resume_path or ""}
    profile = {}

    # 2. review extracted (or empty) values
    if data.get("full_name") or data.get("email"):
        reviewed = review_extracted(data)
        cfg["full_name"] = reviewed.get("full_name", "")
        cfg["email"] = reviewed.get("email", "")
        cfg["phone"] = reviewed.get("phone", "")
        cfg["location"] = reviewed.get("location", "")
        cfg["current_role"] = reviewed.get("current_role", "")
        cfg["years_exp"] = reviewed.get("years_exp", "")
        cfg["linkedin_url"] = reviewed.get("linkedin_url", "")
        cfg["github"] = reviewed.get("github", "")
        cfg["summary"] = reviewed.get("summary", "")
        edu = {"degree": reviewed.get("degree", ""), "school": reviewed.get("school", ""),
               "edu_end_year": reviewed.get("edu_year", "")}
        for k, v in edu.items():
            cfg[k] = v
        profile["skills_hint"] = data.get("skills", {})
        profile["achievements_hint"] = data.get("achievements", [])
    else:
        # no resume / no text — fall back to the classic questions
        from setup import setup_interactive  # reuse the identity wizard
        setup_interactive()
        print("\n  ✅ Identity saved. Re-run onboarding later to add skills/interview answers.")
        return 0

    # 3. gaps
    fill_gaps(cfg)

    # 4. skills
    review_skills(profile, {"skills": profile.get("skills_hint", {}),
                            "achievements": profile.get("achievements_hint", [])})

    # 5. interview
    grill_interview(profile, cfg)

    # 6. gmail + creds
    collect_gmail(profile, cfg)

    # merge into cfg (single source of truth)
    for k, v in profile.items():
        cfg[k] = v
    cfg["gmail_consent"] = profile.get("gmail_consent", True)

    generate_artifacts(cfg, profile)

    # 7. environment
    env_check()

    # 8. save
    save_and_finish(cfg, profile)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except (KeyboardInterrupt, EOFError):
        print("\nAborted — nothing was saved.")
        sys.exit(130)
