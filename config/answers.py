#!/usr/bin/env python3
"""config/answers.py — SINGLE source of truth (DRY). Loads config/user.json (YOUR data).

No hardcoded secrets. Every script imports from here:
    from config.answers import A, RESUME, RESUME_NAME, num
    A['email'], A['phone'], A['expected_ctc'], A['first'], A['last'], ...

If config/user.json is missing, run `python3 setup.py` first.
"""
import json
import os
import sys

_HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HUB not in sys.path:
    sys.path.insert(0, _HUB)

_CFG = {}


def _load():
    global _CFG
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                _CFG = json.load(f)
        except Exception:
            _CFG = {}
    else:
        print("⚠️  config/user.json missing — run `python3 setup.py` first")
    return _CFG


_CFG = _load()


def _fmt_lpa(v):
    try:
        return f"{float(v):.1f} LPA"
    except Exception:
        return str(v)


def _full():
    return _CFG.get("full_name", "")


A = {
    "full_name": _full(),
    "first": _full().split()[0] if _full() else "",
    "last": _full().split()[-1] if len(_full().split()) > 1 else "",
    "email": _CFG.get("email", ""),
    "phone": _CFG.get("phone", ""),
    "location": _CFG.get("location", ""),
    "city": _CFG.get("city", _CFG.get("location", "")),
    "state": _CFG.get("state", ""),
    "country": _CFG.get("country", ""),
    "postal_code": _CFG.get("postal_code", ""),
    "address": _CFG.get("address", ""),
    "dob": _CFG.get("dob", ""),
    "gender": _CFG.get("gender", ""),
    "current_company": _CFG.get("current_company", ""),
    "current_role": _CFG.get("current_role", ""),
    "ctc": _fmt_lpa(_CFG.get("current_ctc_lpa", "")),
    "current_ctc_lpa": _CFG.get("current_ctc_lpa", ""),
    "expected": _fmt_lpa(_CFG.get("expected_ctc_lpa", "")),
    "expected_ctc_lpa": _CFG.get("expected_ctc_lpa", ""),
    "expected_ctc": _CFG.get("expected_ctc", ""),
    "notice": _CFG.get("notice_days", "0"),
    "availability": _CFG.get("availability", ""),
    "last_working_day": _CFG.get("last_working_day", ""),
    "years": _CFG.get("years_exp", ""),
    "linkedin": _CFG.get("linkedin_url", ""),
    "github": _CFG.get("github", ""),
    "gender": _CFG.get("gender", "Female"),
    "summary": _CFG.get("summary", ""),
    "degree": _CFG.get("degree", ""),
    "discipline": _CFG.get("discipline", ""),
    "school": _CFG.get("school", ""),
    "edu_start_month": _CFG.get("edu_start_month", ""),
    "edu_end_month": _CFG.get("edu_end_month", ""),
    "edu_start_year": _CFG.get("edu_start_year", ""),
    "edu_end_year": _CFG.get("edu_end_year", ""),
    # credentials (only read by login/gmail modules; never logged)
    "linkedin_user": _CFG.get("linkedin_user", _CFG.get("email", "")),
    "linkedin_pass": _CFG.get("linkedin_pass", ""),
    "gmail_user": _CFG.get("gmail_user", _CFG.get("email", "")),
    "gmail_app_pw": _CFG.get("gmail_app_pw", ""),
    "capsolver_key": _CFG.get("capsolver_key", ""),
    "answers_india": _CFG.get("application_answers_india", {}),
}

# Resume: absolute path + the professional upload filename
RESUME = _CFG.get("resume_path", "")
RESUME_NAME = _CFG.get("resume_filename", "")


def num(key):
    """String form of a numeric config value (for form fields)."""
    return str(_CFG.get(key, ""))


def answer_yes_no(question_key, default="Yes"):
    """Look up a saved India application answer by its snake_case key."""
    ans = (_CFG.get("application_answers_india", {}) or {}).get(question_key)
    return ans or default


if __name__ == "__main__":
    safe = {k: v for k, v in A.items() if k not in ("linkedin_pass", "gmail_app_pw", "capsolver_key")}
    print(json.dumps(safe, indent=2, ensure_ascii=False))
