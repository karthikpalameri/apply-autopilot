#!/usr/bin/env python3
"""resume_facts.py — extract candidate facts from the resume PDF.

STANDING RULE (2026-11-05): never mark a fact "UNKNOWN / must ask user" before
running this. The resume is uploaded to every ATS, so its values are internally
consistent and already available.

Usage:
    .venv/bin/python find/resume_facts.py            # print + write config/resume_facts.json
    .venv/bin/python find/resume_facts.py --text     # also dump raw extracted text

Order of truth: config/user.json (explicit) > resume text > ask user.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config", "user.json")
OUT = os.path.join(ROOT, "config", "resume_facts.json")

# This file is a DERIVED CACHE, not a source of truth. config/user.json wins every
# conflict and skills/REFERENCE.md#identity is the authoritative note. Regenerate it
# with `find/resume_facts.py` rather than editing it by hand.

MONTHS = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun",
         "jul", "aug", "sep", "oct", "nov", "dec"], start=1
    )
}


def load_user() -> dict:
    try:
        with open(CFG) as f:
            return json.load(f)
    except Exception:
        return {}


def resume_path(user: dict) -> str:
    p = user.get("resume_path") or ""
    if p and os.path.exists(p):
        return p
    for name in os.listdir(os.path.join(ROOT, "config")):
        if name.lower().endswith(".pdf"):
            return os.path.join(ROOT, "config", name)
    raise SystemExit("no resume PDF found under config/")


def extract_text(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise SystemExit("pypdf missing — run: .venv/bin/pip install pypdf") from None
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def find_dob(text: str) -> dict | None:
    """DOB is rendered many ways; normalise to ISO + the two form formats."""
    patterns = [
        r"(?i)\b(?:date\s*of\s*birth|d\.?o\.?b\.?|born)\b\s*[:\-]?\s*"
        r"([0-3]?\d)\s*(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?\s+((?:19|20)\d{2})",
        r"(?i)\b(?:date\s*of\s*birth|d\.?o\.?b\.?|born)\b\s*[:\-]?\s*"
        r"([A-Za-z]{3,9})\.?\s+([0-3]?\d)\s*,?\s+((?:19|20)\d{2})",
        r"(?i)\b(?:date\s*of\s*birth|d\.?o\.?b\.?|born)\b\s*[:\-]?\s*"
        r"([0-3]?\d)[/.\-]([01]?\d)[/.\-]((?:19|20)\d{2})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if not m:
            continue
        a, b, c = m.groups()
        if a.isdigit() and not b.isdigit():          # 15 April 1994
            day, mon, year = int(a), b, int(c)
        elif not a.isdigit() and b.isdigit():        # April 15, 1994
            day, mon, year = int(b), a, int(c)
        else:                                        # 15/04/1994 (dd/mm)
            day, mon, year = int(a), int(b), int(c)
        mm = MONTHS.get(mon[:3].lower()) if isinstance(mon, str) else int(mon)
        if not mm:
            continue
        return {
            "date_of_birth": f"{year:04d}-{mm:02d}-{day:02d}",
            "date_of_birth_display_us": f"{mm:02d}/{day:02d}/{year:04d}",
            "date_of_birth_display_eu": f"{day:02d}/{mm:02d}/{year:04d}",
            "date_of_birth_display_long": f"{day} {mon if isinstance(mon, str) else mm} {year}",
        }
    return None


def find_contacts(text: str) -> dict:
    out: dict[str, str] = {}
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    if m:
        out["email"] = m.group(0)
    m = re.search(r"(?:\+91[\s-]?)?([6-9]\d{4}[\s-]?\d{5})", text)
    if m:
        digits = re.sub(r"\D", "", m.group(0))
        out["phone"] = "+91 " + digits[-10:] if len(digits) >= 10 else digits
    m = re.search(r"(?:linkedin\.com/in/|linkedin:\s*)([\w\-]+)", text, re.I)
    if m:
        out["linkedin_url"] = f"https://www.linkedin.com/in/{m.group(1)}/"
    m = re.search(r"(?:github\.com/)([\w\-]+)", text, re.I)
    if m:
        out["github"] = f"https://github.com/{m.group(1)}"
    return out


def find_work_history(text: str) -> list[dict]:
    """Lines shaped 'Employer, City | Mon'YYYY – Now | Title'."""
    rows = []
    pat = re.compile(
        r"^(?P<comp>[^,|\n]+?)\s*,\s*(?P<city>[A-Za-z .]+?)\s*\|\s*"
        r"(?P<m1>[A-Za-z]{3})['\u2019]?(?P<y1>\d{4})\s*[\u2013\u2014\-]+\s*"
        r"(?P<end>Now|Present|[A-Za-z]{3})['\u2019]?(?P<y2>\d{4})?"
        r"(?:\s*\|\s*(?P<title>[^\n]+))?$",
        re.M,
    )
    for m in pat.finditer(text):
        d = m.groupdict()
        start = f"{d['y1']}-{MONTHS.get(d['m1'][:3].lower(), 1):02d}"
        if d["end"].lower() in ("now", "present"):
            finish = ""
        else:
            finish = f"{d['y2']}-{MONTHS.get(d['end'][:3].lower(), 1):02d}" if d["y2"] else ""
        rows.append({
            "employer": d["comp"].strip(),
            "title": (d["title"] or "").strip(),
            "location": d["city"].strip(),
            "start": start,
            "end": finish,
        })
    return rows


def main() -> None:
    user = load_user()
    path = resume_path(user)
    text = extract_text(path)

    facts: dict = {"resume_path": path}
    dob = find_dob(text)
    if dob:
        facts.update(dob)
        facts["date_of_birth_source"] = f"resume:{os.path.relpath(path, ROOT)}"
    facts.update(find_contacts(text))
    work = find_work_history(text)
    if work:
        facts["work_history"] = work
        facts["employer_current"] = work[0]["employer"]
        facts["employer_current_start"] = work[0]["start"]
    # graduation: 'B.M.S College' + B.E. Computer Science
    m = re.search(r"(?i)(B\.?\s?E\.?|B\.?\s?Tech|Bachelor)[^\n]{0,60}?(Computer|Information)\s*Science", text)
    if m:
        facts["degree"] = "Bachelors (B.E.)"
        facts["field_of_study"] = "Computer and Information Science"
    m = re.search(r"(?i)^([A-Z][\w. ]{3,60}?(?:College|University|Institute))\s*,\s*([A-Za-z ]+?),?\s*((?:19|20)\d{2})", text, re.M)
    if m:
        facts["school"] = re.sub(r"\s+", " ", m.group(1)).strip(" ,.")
        facts["school_location"] = m.group(2).strip(" ,.")
        facts["graduation_year"] = m.group(3)

    # user.json explicit values win (order of truth). The previous version built
    # `merged` only for the *printout* and then wrote the raw scraped `facts`, so
    # config/resume_facts.json carried the resume's raw scraped phone while user.json
    # held the formatted one — a silent two-source drift on a field that goes into
    # every ATS. One value, one source: write the merged result, and never let the
    # scrape overwrite an explicit user.json key.
    merged = {**facts, **{k: v for k, v in user.items() if v not in (None, "", [])}}

    with open(OUT, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"resume : {os.path.relpath(path, ROOT)}")
    for key in (
        "date_of_birth", "date_of_birth_display_us", "date_of_birth_display_eu",
        "email", "phone", "linkedin_url", "github",
        "school", "degree", "field_of_study",
        "employer_current", "employer_current_start",
    ):
        if merged.get(key):
            print(f"  {key:<26} {merged[key]}")
    for row in merged.get("work_history", []):
        print(f"  WORK  {row['employer']:<28} {row['title']:<34} {row['start']} -> {row['end'] or 'now'}")
    print(f"\nwritten: {os.path.relpath(OUT, ROOT)}")

    if "--text" in sys.argv:
        print("\n======== RAW TEXT ========")
        print(text)


if __name__ == "__main__":
    main()
