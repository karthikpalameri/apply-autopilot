#!/usr/bin/env python3
"""onboarding.py — friendly guided setup for Apply Autopilot (cross-platform).

Run:  python3 onboarding.py        (or:  python3 hub.py onboard)

What it does, in order:
  1. Explains WHAT the tool does, WHY, and HOW (short).
  2. Checks the environment and offers to install dependencies.
  3. Collects identity / experience / compensation / resume / education (same as setup.py).
  4. GRILLS you with structured, interview-style questions to extract your skills,
     achievements, target roles, and interview answers.
  5. Explains exactly how your Gmail is used (OTP reads, ATS account sign-ups,
     recruiter cold-email drafting/sending) and asks for explicit consent.
  6. Generates a tailored profile (headline, summary, key skills, elevator pitch,
     strengths/weaknesses, cold-email draft) and SAVES it locally so you are
     never asked the same questions again.

Everything is written to git-ignored files only:
    config/user.json    (identity + credentials, chmod 600)
    config/profile.json (full grilled profile)
    config/profile.md   (human-readable profile + interview notes)
    config/resume.md5   (your resume hash)
    core/.env           (CapSolver key, optional)
"""
import json
import os
import sys

HUB = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HUB)

from setup import ask, ask_bool, ask_int, chmod600, slugify, derive_resume_filename  # noqa: E402

CFG_PATH = os.path.join(HUB, "config", "user.json")
PROFILE_PATH = os.path.join(HUB, "config", "profile.json")
PROFILE_MD = os.path.join(HUB, "config", "profile.md")

IS_WINDOWS = os.name == "nt"


def section(n, title):
    print("\n" + "=" * 64)
    print(f"  {n}  {title}")
    print("=" * 64)


def heading(t):
    print("\n  • " + t)


def multi(prompt, options, allow_free=True):
    """Let the user pick comma-separated option numbers, type free text, or skip."""
    print(prompt)
    for i, o in enumerate(options, 1):
        print(f"    {i:2d}. {o}")
    v = input("  → numbers (comma-separated), free text, or Enter to skip: ").strip()
    if not v:
        return []
    picked = []
    for part in v.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(options):
            picked.append(options[int(part) - 1])
        elif part:
            picked.append(part)
    if allow_free and not any(p in options for p in picked):
        # treat entire input as free text list
        return [x.strip() for x in v.split(",") if x.strip()]
    return picked


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


def explain():
    print("=" * 68)
    print("  🎯 APPLY AUTOPILOT — your personal job-application copilot")
    print("=" * 68)
    print("""
WHAT IT DOES
  Finds relevant openings at product companies, verifies they match your profile,
  applies with YOUR tailored resume, emails recruiters, and tracks everything.

WHY
  Job hunting is 80% repetitive form-filling and searching. This automates the
  repetitive parts (ATS forms, LinkedIn Easy Apply, resume uploads, OTP reads)
  so you spend your energy on the 20% that matters: choosing roles and talking
  to recruiters.

HOW (3 steps, one time)
  1. This onboarding → builds your profile + explains Gmail use.
  2. `python3 hub.py install` → installs Python/npm/pi dependencies.
  3. `python3 hub.py start`  → starts the browser stack; you log in once.

Your data lives ONLY in git-ignored local files (config/user.json + config/profile.json).
Nothing is uploaded anywhere by the setup itself.
""")


def env_check():
    section("0/8", "Environment check")
    ok = True
    py = sys.executable
    print(f"  • Python: {py}")
    for name, cmd in (("node", "node"), ("npx", "npx"), ("pi", "pi")):
        found = shutil_which(cmd)
        print(f"  • {name}: {'✅ ' + found if found else '❌ not found'}")
        if not found:
            ok = False
    if not os.path.exists(os.path.join(HUB, ".venv")):
        print("  • .venv: ❌ not created yet")
        ok = False
    else:
        print("  • .venv: ✅")
    if not ok:
        if ask_bool("Some dependencies are missing — run `python3 hub.py install` now?", True):
            import subprocess
            subprocess.run([sys.executable, "hub.py", "install"])
    else:
        print("  ✅ environment looks good")


def shutil_which(name):
    import shutil
    return shutil.which(name)


def collect_identity(cfg):
    section("1/8", "Identity")
    cfg["full_name"] = ask("Full name", cfg.get("full_name", "Jane Doe"), required=True)
    cfg["email"] = ask("Email (used on applications)", cfg.get("email", "jane.doe@example.com"), required=True)
    cfg["phone"] = ask("Phone (with country code)", cfg.get("phone", "+91 00000 00000"))
    cfg["location"] = ask("Current city", cfg.get("location", "Bengaluru"))
    cfg["city"] = cfg["location"]
    cfg["state"] = ask("State / province", cfg.get("state", "Karnataka"))
    cfg["country"] = ask("Country", cfg.get("country", "India"))
    cfg["postal_code"] = ask("Postal code", cfg.get("postal_code", ""))
    cfg["address"] = ask("Street address (optional)", cfg.get("address", ""))
    cfg["dob"] = ask("Date of birth YYYY-MM-DD (optional)", cfg.get("dob", ""))
    cfg["gender"] = ask("Gender (Male/Female/Other)", cfg.get("gender", "Female"))


def collect_experience(cfg):
    section("2/8", "Experience & target roles")
    cfg["current_role"] = ask("Current / most recent job title", cfg.get("current_role", "Senior QA Automation Engineer"))
    cfg["current_company"] = ask("Current / most recent company", cfg.get("current_company", ""))
    cfg["years_exp"] = ask_int("Years of experience", cfg.get("years_exp", 8))
    heading("Target roles (comma-separated)")
    target = input("  → e.g. Senior QA Automation Engineer, SDET, QA Lead: ").strip()
    cfg["target_roles"] = [r.strip() for r in target.split(",") if r.strip()] or [cfg["current_role"]]
    cfg["target_locations"] = [l.strip() for l in ask(
        "Target locations (comma-separated)", cfg.get("location", "Bengaluru")).split(",") if l.strip()]
    cfg["remote_pref"] = ask("Remote / hybrid / onsite preference", cfg.get("remote_pref", "Hybrid"))
    cfg["linkedin_url"] = ask("LinkedIn profile URL", cfg.get("linkedin_url", "https://www.linkedin.com/in/janedoe"))
    cfg["github"] = ask("GitHub URL (optional)", cfg.get("github", ""))


def collect_compensation(cfg):
    section("3/8", "Compensation & notice")
    cfg["current_ctc_lpa"] = ask_int("Current CTC in LPA (0 if n/a)", cfg.get("current_ctc_lpa", 0))
    default_exp = round(cfg["current_ctc_lpa"] * 1.22, 1) if cfg.get("current_ctc_lpa") else 30
    cfg["expected_ctc_lpa"] = ask_int("Expected CTC in LPA", cfg.get("expected_ctc_lpa", default_exp))
    cfg["expected_ctc"] = int(cfg["expected_ctc_lpa"] * 100000)
    cfg["notice_days"] = ask_int("Notice period in days (0 if already resigned)", cfg.get("notice_days", 0))
    cfg["last_working_day"] = ask("Last working day YYYY-MM-DD (if serving notice)", cfg.get("last_working_day", ""))
    cfg["availability"] = ask("Availability text for forms", cfg.get("availability", "Immediate"))


def collect_resume(cfg):
    section("4/8", "Resume")
    default_resume = cfg.get("resume_path") or os.path.join(os.path.expanduser("~"), "Downloads", "Resume.pdf")
    resume_path = ask("Absolute path to your resume PDF", default_resume)
    resume_path = os.path.abspath(os.path.expanduser(resume_path))
    if not os.path.exists(resume_path):
        print(f"  ⚠️  Not found: {resume_path} — you can fix it later and re-run onboarding.")
    cfg["resume_path"] = resume_path
    cfg["resume_filename"] = derive_resume_filename(cfg["full_name"], cfg["current_role"])


def collect_education(cfg):
    section("5/8", "Education")
    cfg["degree"] = ask("Degree level", cfg.get("degree", "Bachelor"))
    cfg["discipline"] = ask("Field of study", cfg.get("discipline", "Computer Science"))
    cfg["school"] = ask("School / university", cfg.get("school", ""))
    cfg["edu_start_month"] = ask("Start month", cfg.get("edu_start_month", "August"))
    cfg["edu_end_month"] = ask("End month", cfg.get("edu_end_month", "May"))
    cfg["edu_start_year"] = ask_int("Start year", cfg.get("edu_start_year", 2013))
    cfg["edu_end_year"] = ask_int("End year", cfg.get("edu_end_year", 2017))


# ---------------------------------------------------------------- the GRILL
def grill_skills(profile, cfg):
    section("6/8", "SKILL GRILL — what are you actually good at?")

    profile["languages"] = multi(
        "\nProgramming languages you can code in:",
        ["Java", "Python", "JavaScript/TypeScript", "C#", "Go", "Kotlin", "Ruby", "Shell/Bash"])

    profile["automation_frameworks"] = multi(
        "\nTest-automation frameworks you have USED (not just heard of):",
        ["Selenium", "Playwright", "Appium", "Cypress", "RestAssured", "WebdriverIO",
         "TestNG", "JUnit", "Pytest", "Cucumber/BDD"])

    profile["api_testing"] = multi(
        "\nAPI / backend testing tools:",
        ["Postman", "REST Assured", "SOAP UI", "GraphQL", "gRPC", "Karate"])

    profile["performance"] = multi(
        "\nPerformance / load testing tools:",
        ["JMeter", "k6", "Gatling", "Locust", "LoadRunner"])

    profile["cicd"] = multi(
        "\nCI/CD & DevOps:",
        ["Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Azure DevOps", "Docker", "Kubernetes"])

    profile["cloud"] = multi(
        "\nCloud platforms:",
        ["AWS", "GCP", "Azure", "None / on-prem only"])

    profile["databases"] = multi(
        "\nDatabases:",
        ["SQL (any)", "PostgreSQL", "MySQL", "MongoDB", "Oracle", "NoSQL general"])

    profile["tools_other"] = multi(
        "\nOther tools / practices:",
        ["JIRA", "TestRail", "Zephyr", "Agile/Scrum", "Mobile testing (iOS/Android)",
         "Security testing", "Accessibility testing", "Git"])

    profile["domains"] = multi(
        "\nDomains you have worked in:",
        ["Fintech/Payments", "Healthcare", "E-commerce/Retail", "SaaS/B2B", "Telecom",
         "Gaming", "Logistics", "Media/Streaming"])

    # quantified achievements
    heading("Achievements (the interview gold)")
    print("  Recruiters want NUMBERS. Answer in the form: 'did X → saved/reduced Y by Z%'.")
    profile["achievements"] = []
    for i in range(1, 4):
        a = input(f"  Achievement {i} (Enter to stop): ").strip()
        if not a:
            break
        profile["achievements"].append(a)

    certs = input("  Certifications (comma-separated, e.g. ISTQB, AWS SAA; Enter for none): ").strip()
    profile["certifications"] = [c.strip() for c in certs.split(",") if c.strip()]

    profile["years_exp"] = int(cfg.get("years_exp") or 0)


def grill_interview(profile, cfg):
    section("7/8", "INTERVIEW GRILL — let's write your answers together")
    print("  (You'll thank yourself later — these become your cheat sheet.)")

    profile["pitch"] = ask(
        "Tell me about yourself (2-3 sentences, or press Enter and I'll draft one for you):", "")
    profile["strengths"] = ask("Top 2-3 strengths:", "")
    profile["weakness"] = ask("A real weakness + how you're working on it:", "")
    profile["why_leave"] = ask("Why are you looking for a change?", "")
    profile["why_hire"] = ask("Why should a company hire YOU (one line)?", "")
    profile["salary_answer"] = ask(
        "How do you answer 'salary expectation'?", f"{cfg.get('expected_ctc_lpa', 'X')} LPA (slightly negotiable)")


def collect_gmail(profile, cfg):
    section("8/8", "Gmail access — read this carefully")
    print("""
We ask for your Gmail so the agent can do FOUR specific things FOR YOU:

  1. READ OTP / verification codes  — many company ATS sites email a 6-digit code
     during account sign-up; the agent reads it so you don't copy-paste by hand.
  2. READ application confirmations  — to VERIFY an application really went through
     (proof gate) before it is counted as "applied".
  3. REGISTER / log into company ATS  — Workday/Greenhouse/Lever etc. often need
     account creation with email verification.
  4. DRAFT and (only if you approve) SEND cold emails to recruiters  — humble,
     personalized follow-ups with your resume attached.

Your Gmail password is NEVER stored in this repository. It lives only in the
git-ignored config/user.json (chmod 600) or in the logged-in browser session.
""")
    consent = ask_bool("Do you consent to the agent using Gmail for the above 4 purposes?", True)
    profile["gmail_consent"] = consent
    profile["gmail_user"] = ask("Gmail address", cfg.get("email"))
    profile["gmail_app_pw"] = ask("Gmail App Password (IMAP — optional, enables a faster read path)", "", secret=True)
    if not consent:
        print("  ⚠️  Gmail use disabled — OTP/confirmation reads and cold emails will ask you to do them manually.")
    else:
        print("  ✅ Gmail consent recorded. You can revoke it anytime by deleting gmail_consent in config/user.json.")


def collect_credentials(profile, cfg):
    profile["linkedin_user"] = ask("LinkedIn login email", cfg.get("email"))
    profile["linkedin_pass"] = ask("LinkedIn password (stored locally only)", "", secret=True)
    profile["capsolver_key"] = ask("CapSolver API key (optional, for captchas)", "", secret=True)


# ---------------------------------------------------------------- generation
def generate_artifacts(cfg, profile):
    """Fill in the gaps with sensible drafts + build the human-readable profile.md."""
    years = profile.get("years_exp") or cfg.get("years_exp") or 0
    role = cfg.get("current_role") or "QA Engineer"
    company = cfg.get("current_company") or "my current company"
    langs = ", ".join(profile.get("languages", []) or ["Java", "Python"]) or "Java, Python"
    frameworks = ", ".join(profile.get("automation_frameworks", []) or ["Selenium", "Playwright"])
    tools = ", ".join((profile.get("api_testing", []) or ["Postman"]) + (profile.get("cicd", []) or ["CI/CD"]))

    if not profile.get("pitch"):
        profile["pitch"] = (f"I'm a {role} with {years}+ years building reliable test automation. "
                            f"At {company} I work on {profile.get('domains', ['fintech'])[0] if profile.get('domains') else 'product'} "
                            f"quality using {frameworks}, {langs}, and {tools}. I care about shipping confidence, not just test cases.")

    if not profile.get("why_hire"):
        profile["why_hire"] = (f"I turn flaky manual QA into fast, deterministic automation "
                               f"({frameworks}, {langs}) and I own quality end-to-end.")

    if not profile.get("weakness"):
        profile["weakness"] = "I sometimes over-engineer frameworks; I now timebox design and ship the MVP first."

    # key skills (Naukri 250-char cap)
    all_skills = []
    for k in ("languages", "automation_frameworks", "api_testing", "performance", "cicd",
              "cloud", "databases", "tools_other"):
        all_skills += profile.get(k, []) or []
    seen, key_skills = set(), []
    for s in all_skills:
        if s and s.lower() not in seen:
            seen.add(s.lower())
            key_skills.append(s)
    profile["key_skills"] = ", ".join(key_skills)[:249]

    profile["headline"] = (f"{role} | {years} yrs | {frameworks} | {langs} | "
                           f"{profile.get('domains', ['Fintech'])[0] if profile.get('domains') else 'Product'}")

    profile["summary"] = profile["pitch"]

    # cold email
    profile["cold_email"] = {
        "subject": f"Application – {role} – {cfg.get('location', '')} – {cfg.get('full_name', '')} ({years} yrs)",
        "body": (
            f"Dear <Name>,\n\n"
            f"I hope this finds you well. I came across your opening for a {role} and would\n"
            f"love to be considered. I bring {years} years of experience, most recently at\n"
            f"{company}, where I built and maintained {frameworks} automation for "
            f"{profile.get('domains', ['product'])[0] if profile.get('domains') else 'product'} quality.\n\n"
            f"My core skills are {langs}, {frameworks}, and {tools}. My resume is attached.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Warm regards,\n{cfg.get('full_name', '')}\n{cfg.get('phone', '')} · {cfg.get('email', '')}"
        ),
    }
    return profile


def write_profile_md(cfg, profile):
    lines = [
        "# Your profile (auto-generated by onboarding.py — git-ignored)",
        "",
        f"## Headline",
        f"`{profile.get('headline', '')}`",
        "",
        f"## Summary / elevator pitch",
        f"{profile.get('summary', '')}",
        "",
        f"## Key skills (Naukri ≤250 chars)",
        f"`{profile.get('key_skills', '')}`",
        "",
        "## Strengths",
        f"{profile.get('strengths', '')}",
        "",
        "## Weakness + improvement",
        f"{profile.get('weakness', '')}",
        "",
        "## Why I'm looking",
        f"{profile.get('why_leave', '')}",
        "",
        "## Why hire me",
        f"{profile.get('why_hire', '')}",
        "",
        "## Salary expectation answer",
        f"{profile.get('salary_answer', '')}",
        "",
        "## Achievements",
    ]
    for a in profile.get("achievements", []) or ["(none recorded)"]:
        lines.append(f"- {a}")
    lines += [
        "",
        "## Certifications",
        ", ".join(profile.get("certifications", []) or ["(none)"]) ,
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


def main():
    explain()

    existing = load_json(CFG_PATH)
    if existing:
        print("  ℹ️  Existing config/user.json found — showing redacted summary:")
        red = {k: ("***" if k in ("linkedin_pass", "gmail_app_pw", "capsolver_key") else v)
               for k, v in existing.items()}
        print(json.dumps(red, indent=2, ensure_ascii=False)[:1200])
        if not ask_bool("Re-run the full questionnaire (re-ask everything)?", False):
            print("  ✅ Keeping existing config. To edit later: python3 onboarding.py")
            return

    env_check()

    cfg = dict(existing)
    profile = load_json(PROFILE_PATH)

    collect_identity(cfg)
    collect_experience(cfg)
    collect_compensation(cfg)
    collect_resume(cfg)
    collect_education(cfg)

    profile = dict(profile)
    grill_skills(profile, cfg)
    grill_interview(profile, cfg)
    collect_gmail(profile, cfg)
    collect_credentials(profile, cfg)

    # merge grilled profile into user.json (single source of truth)
    for k, v in profile.items():
        cfg[k] = v
    cfg["gmail_consent"] = profile.get("gmail_consent", True)

    generate_artifacts(cfg, profile)

    save_json(CFG_PATH, cfg, secret=True)
    save_json(PROFILE_PATH, profile, secret=True)
    write_profile_md(cfg, profile)

    print("\n" + "=" * 68)
    print("  ✅ PROFILE SAVED — you will NOT be asked these again.")
    print("=" * 68)
    print(f"  • config/user.json     (identity + credentials, chmod 600)")
    print(f"  • config/profile.json  (skills, achievements, interview answers)")
    print(f"  • config/profile.md    (human-readable — open this to review)")
    print(f"  • resume upload name:  {cfg.get('resume_filename', '')}")
    print("\nNext steps:")
    print("  1. python3 hub.py install")
    print("  2. python3 hub.py start")
    print("  3. python3 hub.py health")
    print("\nTo edit your profile later, just run:  python3 onboarding.py")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except (KeyboardInterrupt, EOFError):
        print("\nAborted — nothing was saved.")
        sys.exit(130)
