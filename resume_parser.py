#!/usr/bin/env python3
"""resume_parser.py — best-effort extraction of profile data from a resume PDF.

This is a heuristic reader: it pulls out what is reliably regex-able (email, phone,
links, skills, years, education) and best-effort guesses the rest (name, role,
location, summary). Every extracted value is ALWAYS shown back to the user for
confirmation (see onboarding.py), so a wrong guess is never saved silently.

Dependencies: pypdf (optional — onboarding offers to install it if missing).

Usage:
    from resume_parser import parse_pdf, extract_text
    data = parse_pdf("/path/to/resume.pdf")
"""
import os
import re

# ---------------------------------------------------------------- skills dictionary
LANGUAGES = ["Java", "Python", "JavaScript", "TypeScript", "C#", "C++", "C", "Go", "Golang",
             "Kotlin", "Ruby", "Swift", "PHP", "Scala", "Rust", "Shell", "Bash", "SQL", "HTML", "CSS"]
FRAMEWORKS = ["Selenium", "Playwright", "Appium", "Cypress", "RestAssured", "REST Assured",
              "WebdriverIO", "WebDriver", "TestNG", "JUnit", "Pytest", "Cucumber", "BDD",
              "Robot Framework", "Karate", "Espresso", "XCTest", "Detox", "SpecFlow"]
API_TESTING = ["Postman", "SOAP UI", "SoapUI", "GraphQL", "gRPC", "Swagger", "OpenAPI", "Karate"]
PERFORMANCE = ["JMeter", "k6", "Gatling", "Locust", "LoadRunner", "BlazeMeter"]
CICD = ["Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Azure DevOps", "Docker",
        "Kubernetes", "Terraform", "Ansible", "Maven", "Gradle", "npm", "AWS CodePipeline"]
CLOUD = ["AWS", "Amazon Web Services", "GCP", "Google Cloud", "Azure", "Heroku", "DigitalOcean"]
DATABASES = ["PostgreSQL", "MySQL", "MongoDB", "Oracle", "SQL Server", "SQLite", "Redis",
             "Cassandra", "DynamoDB", "Elasticsearch", "NoSQL"]
TOOLS_OTHER = ["JIRA", "Jira", "TestRail", "Zephyr", "Agile", "Scrum", "Git", "GitHub",
               "GitLab", "Bitbucket", "Confluence", "Mobile Testing", "iOS", "Android",
               "Security Testing", "Accessibility Testing", "API Testing", "Manual Testing",
               "Automation Testing", "Regression Testing", "Functional Testing", "E2E",
               "CI/CD", "DevOps", "SDET"]
DOMAINS = ["Fintech", "Payments", "Banking", "Healthcare", "E-commerce", "Ecommerce", "Retail",
           "SaaS", "B2B", "Telecom", "Gaming", "Logistics", "Media", "Streaming", "Insurance",
           "EdTech", "Travel", "AdTech", "IoT"]

ALL_SKILLS = {
    "languages": LANGUAGES,
    "automation_frameworks": FRAMEWORKS,
    "api_testing": API_TESTING,
    "performance": PERFORMANCE,
    "cicd": CICD,
    "cloud": CLOUD,
    "databases": DATABASES,
    "tools_other": TOOLS_OTHER,
    "domains": DOMAINS,
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-().]{6,18}\d")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[A-Za-z0-9\-_%]+")
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_]+")
YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years|yrs)", re.I)
EDU_DEGREES = ["Bachelor", "B.E.", "B.E", "B.Tech", "B.S.", "B.Sc", "Master", "M.Tech",
               "M.S.", "M.Sc", "MBA", "Ph.D", "Diploma", "Associate"]
CITIES = ["Bengaluru", "Bangalore", "Mumbai", "Delhi", "Pune", "Chennai", "Hyderabad",
          "Kolkata", "Gurgaon", "Gurugram", "Noida", "Ahmedabad", "Remote", "Karnataka",
          "Maharashtra", "Tamil Nadu", "Telangana", "India", "USA", "United States",
          "UK", "Canada", "Germany", "Singapore", "Dubai"]
ROLE_RE = re.compile(r"\b(?:Senior|Lead|Staff|Principal|Associate|Junior)?\s*(?:QA|SDET|Software|Automation|Test|Quality)"
                     r"[A-Za-z ]*(?:Engineer|Developer|Analyst|Tester|Specialist|Architect|Manager|Lead)\b", re.I)

STOPWORDS = {"resume", "cv", "curriculum", "vitae", "updated", "final", "latest", "new", "doc"}


class DependencyMissing(RuntimeError):
    pass


class ParseError(RuntimeError):
    pass


def extract_text(pdf_path):
    """Return all text from a PDF, or raise DependencyMissing/ParseError."""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise DependencyMissing("pypdf is not installed") from e
    try:
        reader = PdfReader(pdf_path)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except Exception as e:
        raise ParseError(f"could not read PDF: {e}") from e


# ---------------------------------------------------------------- field extractors
def _first_email(text):
    m = EMAIL_RE.search(text)
    if m and not m.group(0).lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        return m.group(0)
    return ""


def _first_phone(text):
    # pick the most phone-like candidate (8-14 digits, prefers +/separators)
    best, best_score = "", -1
    for m in PHONE_RE.finditer(text):
        cand = m.group(0).strip(" .-")
        digits = re.sub(r"\D", "", cand)
        if len(digits) < 8 or len(digits) > 14:
            continue
        score = len(digits)
        if cand.startswith("+") or any(ch in cand for ch in " -()"):
            score += 3
        if score > best_score:
            best, best_score = cand, score
    return best


def _first_linkedin(text):
    m = LINKEDIN_RE.search(text)
    return m.group(0) if m else ""


def _first_github(text):
    m = GITHUB_RE.search(text)
    return m.group(0) if m else ""


def _name_from_filename(path):
    base = os.path.splitext(os.path.basename(path))[0]
    toks = [t for t in re.split(r"[_\-\s]+", base) if t.lower() not in STOPWORDS and not t.isdigit()]
    if not toks:
        return ""
    # drop a trailing generic token like "seniorqa"
    return " ".join(t.title() for t in toks[:3])


def _name_from_text(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines[:6]:
        words = l.split()
        if not (2 <= len(words) <= 4):
            continue
        # accept Title Case (Jane Doe) or ALL-CAPS headers (JANE DOE)
        title = all(w[:1].isupper() and w[1:].islower() for w in words)
        caps = all(w.isupper() for w in words)
        if (title or caps) and not EMAIL_RE.search(l) and not PHONE_RE.search(l):
            return l.title()
    return ""


def _first_role(text):
    m = ROLE_RE.search(text)
    return m.group(0).strip() if m else ""


def _years(text):
    m = YEARS_RE.search(text)
    return int(m.group(1)) if m else ""


def _education(text):
    found_deg = ""
    for d in EDU_DEGREES:
        if re.search(r"\b" + re.escape(d) + r"\b", text, re.I):
            found_deg = d
            break
    school = ""
    for l in text.splitlines():
        if re.search(r"university|college|institute|school", l, re.I):
            school = l.strip()[:80]
            break
    # prefer the graduation year from the education line, not a job date
    yr = ""
    m = re.search(r"\b(19|20)\d{2}\b", school)
    if m:
        yr = m.group(0)
    else:
        m = re.search(r"\b(19|20)\d{2}\b", text)
        if m:
            yr = m.group(0)
    return {"degree": found_deg, "year": yr, "school": school}


def _location(text):
    for c in CITIES:
        if re.search(r"\b" + re.escape(c) + r"\b", text, re.I):
            return c
    return ""


def _skills(text):
    low = text.lower()
    out = {}
    for cat, words in ALL_SKILLS.items():
        found = []
        for w in words:
            if w.lower() in low:
                found.append(w)
        out[cat] = found
    return out


def _summary(text):
    for l in text.splitlines():
        if re.search(r"^\s*(summary|profile|objective)\s*:?", l, re.I):
            # take this + next 2 lines
            idx = text.splitlines().index(l)
            return " ".join(x.strip() for x in text.splitlines()[idx:idx + 3] if x.strip())[:400]
    return ""


def _achievements(text):
    lines = text.splitlines()
    ach = []
    for l in lines:
        if re.search(r"\d+\s*%|reduced|improved|automated|increased|saved|delivered|built|led|migrated|cut|accelerated", l, re.I):
            if 10 < len(l) < 160 and not EMAIL_RE.search(l):
                ach.append(l.strip())
    return ach[:3]


# ---------------------------------------------------------------- public API
def parse_text(text):
    """Parse raw resume text into a profile dict (best-effort)."""
    skills = _skills(text)
    return {
        "full_name": _name_from_text(text),
        "email": _first_email(text),
        "phone": _first_phone(text),
        "linkedin_url": _first_linkedin(text),
        "github": _first_github(text),
        "location": _location(text),
        "current_role": _first_role(text),
        "years_exp": _years(text),
        "education": _education(text),
        "summary": _summary(text),
        "achievements": _achievements(text),
        "skills": skills,
        "raw_text": text,
    }


def parse_pdf(pdf_path):
    """Extract text from a PDF and parse it. Raises DependencyMissing/ParseError."""
    if not os.path.exists(pdf_path):
        raise ParseError(f"file not found: {pdf_path}")
    text = extract_text(pdf_path)
    if not text.strip():
        raise ParseError("the PDF has no extractable text (scanned image?). Please enter details manually.")
    data = parse_text(text)
    # name fallback: filename if text didn't yield one
    if not data["full_name"]:
        data["full_name"] = _name_from_filename(pdf_path)
    return data


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print("usage: python3 resume_parser.py <resume.pdf>")
        sys.exit(1)
    try:
        d = parse_pdf(sys.argv[1])
        safe = {k: v for k, v in d.items() if k != "raw_text"}
        print(json.dumps(safe, indent=2, ensure_ascii=False))
    except (DependencyMissing, ParseError) as e:
        print(f"❌ {e}")
        sys.exit(1)
