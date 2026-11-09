#!/usr/bin/env python3
"""core/decide.py — ONE owner of the typed decision layer.

Every fuzzy decision the agent makes is layered the same way (see
skills/jev/SKILL.md — "cheaper than reading, not cheaper than knowing"):

    1. deterministic  (0 tokens)  — lookup / regex / comparison, in code here
    2. Jev            (cheap)     — choice among known options, threshold 0.65
    3. main model     (last)      — only on a Jev miss, or free text

SoC: this module is DATA (enums/dataclasses) + LOGIC only. Transport stays in
core/ctl, core/browser, core/fetch. Vocabulary single-owners are imported, never
re-declared:

    status strings  -> config/dedupe.py        (TERMINAL_STATUSES)
    company identity-> core/applied_ledger.py  (co_key, is_applied)
    QA title fit    -> config/dedupe.py        (is_qa_title)
    code extraction -> core/gmail_otp.py       (extract_codes)
    page health     -> core/page_guard.py      (dead/frozen/ok — NOT re-typed here)
    user facts      -> config/answers.py       (A — imported lazily, no import side effect)

stdlib only, no third-party deps. No PII literals: values come from config/answers
at runtime, never written here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.logger import log


class CandidateClass(str, Enum):
    """The four buckets every find/apply gate collapses into."""
    READY = "ready"
    DUPLICATE = "duplicate"
    MISMATCH = "mismatch"
    BLOCKED = "blocked"


class Gate(str, Enum):
    """What (if anything) is blocking a submit. page_guard owns page health
    (dead/frozen/ok); this owns the *blocker taxonomy* from the STOP RULES."""
    OK = "ok"
    CAPTCHA = "captcha"
    ACCOUNT_WALL = "account-wall"
    EMAIL_CODE = "email-code"
    SILENT_NOOP = "silent-noop"
    UNKNOWN = "unknown"


class AuthPhase(str, Enum):
    """The signup/signin/reset/OTP state machine states (REFERENCE.md#auth-priority)."""
    FORM = "form"
    REQUEST = "request"
    WAIT_CODE = "wait-code"
    SIGNIN = "signin"
    DONE = "done"
    BLOCKED = "blocked"


class FieldKind(str, Enum):
    """The HTML control shapes a FieldPlan can point at."""
    TEXT = "text"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DATE = "date"
    UPLOAD = "upload"
    TEXTAREA = "textarea"


@dataclass
class FieldPlan:
    """One field -> one answer. resolved_by says which layer settled it."""
    label: str
    kind: FieldKind
    value: str = ""
    commit: str = ""          # fill | select | check | setInputFiles | native-setter
    resolved_by: str = "deterministic"   # deterministic | jev | model


@dataclass
class WorkHistoryRow:
    """One parsed employment row, normalized. The ATS must never rename these."""
    employer: str
    title: str = ""
    start: str = ""
    end: str = ""
    current: bool = False


@dataclass
class Code:
    """One extracted verification code (Greenhouse 8-char or classic 6-8 digit)."""
    kind: str                 # alnum8 | digits  (from core/gmail_otp.extract_codes)
    value: str
    sender: str = ""
    ts: str = ""


@dataclass
class Proof:
    """Evidence mapped to the canonical ledger status string."""
    status: str               # member of config/dedupe.TERMINAL_STATUSES
    source: str = ""          # employer-page | gmail | both | none
    url: str = ""
    text: str = ""


# Field-label aliases -> config/answers key. Labels only (no values = no PII).
# The VALUE comes from config.answers at runtime; a miss means "escalate to Jev".
FIELD_ALIASES = {
    "email": "email", "e-mail": "email", "email address": "email", "email id": "email",
    "phone": "phone", "phone number": "phone", "mobile": "phone", "mobile number": "phone",
    "first name": "first", "last name": "last", "full name": "full_name",
    "current ctc": "ctc", "expected ctc": "expected", "annual salary": "expected",
    "notice period": "notice", "notice period in days": "notice",
    "total years of experience": "years", "years of experience": "years",
    "linkedin": "linkedin", "linkedin url": "linkedin",
    "gender": "gender", "location": "location", "current location": "location",
    "github": "github", "availability": "availability",
    "last working day": "last_working_day",
}

# Auth state machine — the deterministic part of auth routing. The POLICY
# (priority, single-use reset links, one recovery attempt) stays in
# skills/REFERENCE.md#auth-priority for the agent; these are the hard edges.
_AUTH_TRANSITIONS = {
    (AuthPhase.FORM, "request_code"): AuthPhase.REQUEST,
    (AuthPhase.REQUEST, "code_sent"): AuthPhase.WAIT_CODE,
    (AuthPhase.WAIT_CODE, "code_entered"): AuthPhase.SIGNIN,
    (AuthPhase.SIGNIN, "signed_in"): AuthPhase.DONE,
    (AuthPhase.DONE, "reset"): AuthPhase.FORM,
}


def classify_candidate(company: str, role: str) -> CandidateClass:
    """Deterministic dedupe + title-scope gate. Composes the owners, never re-implements.

    is_applied() owns "have we applied here" (ledger, counts blocked rows — a
    blocked role is still a duplicate); is_qa_title() owns the QA/SDET stack scope
    (config/dedupe). BLOCKED is set by the agent when a required fact (PAN/DOB/etc.)
    is missing — not decidable from these two.

    Scope note: this is NOT the full candidate gate. The staffing/consulting
    filter (SERVICES) and the seniority/stack filters live in find/preflight.py;
    core/ cannot import find/ (layering), so they stay there. Call this for the
    dedupe + title part; the full gate is preflight's classify loop.
    """
    from core.applied_ledger import is_applied
    from config.dedupe import is_qa_title

    if not company or not role:
        log.debug("classify_candidate: empty company/role -> MISMATCH")
        return CandidateClass.MISMATCH
    if is_applied(company, role):
        return CandidateClass.DUPLICATE
    if not is_qa_title(role):
        return CandidateClass.MISMATCH
    return CandidateClass.READY


def validate_work_history(parsed, known):
    """Compare ATS-parsed rows against the known-good history.

    parsed: list of dicts {employer, title, start, end, current} from the ATS.
    known:  list of dicts (same keys) from config/resume_facts.json (the truth).
    Returns (rows, problems): normalized WorkHistoryRow list + human-readable
    diffs. Employer identity uses core.applied_ledger.co_key — the ONE owner —
    so "Bottomline Technologies" vs "Bottomline" is not a false rename.
    """
    from core.applied_ledger import co_key

    rows = []
    problems = []
    known_keys = {co_key(str((r or {}).get("employer") or "")) for r in (known or [])}
    known_keys.discard("")

    for raw in (parsed or []):
        raw = raw or {}
        emp = str(raw.get("employer") or "").strip()
        key = co_key(emp)
        if not key:
            problems.append("dropped row with empty employer")
            continue
        rows.append(WorkHistoryRow(
            employer=emp,
            title=str(raw.get("title") or "").strip(),
            start=str(raw.get("start") or "").strip(),
            end=str(raw.get("end") or "").strip(),
            current=bool(raw.get("current")),
        ))
        if key not in known_keys:
            problems.append(f"employer {emp!r} not in known history (possible ATS rename)")

    if problems:
        log.warning("validate_work_history: %d problem(s) in %d parsed row(s)",
                    len(problems), len(rows))
        for p in problems:
            log.warning("  %s", p)
    else:
        log.info("validate_work_history: %d row(s) all match known history", len(rows))
    return rows, problems


def proof_status(found_text, email_confirmed: bool = False) -> str:
    """Map submit evidence to the canonical ledger status (config/dedupe owns the words).

    found_text = the positive employer message (DOM/OCR), email_confirmed = Gmail
    confirmation. No page proof = blocked; page-only = submitted-awaiting-email;
    page + Gmail = confirmed-email. Never "confirmed" from a LinkedIn-only ack.
    """
    from config.dedupe import TERMINAL_STATUSES

    if not found_text:
        return "blocked"
    status = "confirmed-email" if email_confirmed else "submitted-awaiting-email"
    assert status in TERMINAL_STATUSES, f"{status} drifted from TERMINAL_STATUSES"
    return status


def extract_code(text):
    """Wrap core/gmail_otp.extract_codes (the regex owner) into typed Code rows."""
    from core.gmail_otp import extract_codes

    found = extract_codes(text or "")
    out = []
    for v in found.get("alnum8", []):
        out.append(Code(kind="alnum8", value=v))
    for v in found.get("digits", []):
        out.append(Code(kind="digits", value=v))
    if out:
        log.info("extract_code: %d code(s) found", len(out))
    return out


_A_CACHE = None


def _answers():
    """Lazy + memoized: config.answers loads config/user.json at import (side effect),
    so import once and reuse the same A dict for every field lookup."""
    global _A_CACHE
    if _A_CACHE is None:
        from config.answers import A
        _A_CACHE = A
    return _A_CACHE


def plan_field(label: str):
    """Deterministic field -> answer lookup (0 tokens). None = lookup miss.

    The label is normalized to a config.answers key via FIELD_ALIASES; the VALUE
    is read at runtime, never stored here. On a miss the caller escalates to Jev
    (field_question) then the main model — exactly the Jev layering.
    """
    key = FIELD_ALIASES.get(str(label or "").strip().lower())
    if not key:
        return None
    value = _answers().get(key)
    if value in (None, ""):
        log.debug("plan_field: %r -> key %s present but empty in answers", label, key)
        return None
    kind = FieldKind.DATE if "day" in key or key == "availability" else FieldKind.TEXT
    return FieldPlan(label=label, kind=kind, value=str(value), commit="fill")


def route_auth(phase: AuthPhase, event: str) -> AuthPhase:
    """Deterministic auth state edge. Unknown edge -> BLOCKED (never guess)."""
    nxt = _AUTH_TRANSITIONS.get((phase, event))
    if nxt is None:
        log.warning("route_auth: no transition for (%s, %s) -> BLOCKED", phase.value, event)
        return AuthPhase.BLOCKED
    log.debug("route_auth: %s + %s -> %s", phase.value, event, nxt.value)
    return nxt


# ---------------------------------------------------------------------------
# Jev payload builders. PII-free by construction: they send field labels /
# option lists / structural signals / a job title — never names, emails, phones,
# salaries, visa status, or config/user.json. The agent passes these to
# jev_evaluate unchanged (see skills/jev/SKILL.md).
# ---------------------------------------------------------------------------

def field_question(label: str, options):
    """Jev choice payload: which option answers this field? (no value sent)."""
    opts = [str(o) for o in (options or [])]
    return {
        "state": {"label": str(label or ""), "options": opts},
        "questions": {
            "answer": {
                "type": "choice",
                "instructions": "Which option answers this form field?",
                "criteria": {o: f"the field's answer is '{o}'" for o in opts},
            },
        },
    }


def gate_questions(evidence):
    """Jev choice payload: which blocker explains the stalled submit?

    evidence is structural only (booleans/counts), no page text or PII:
        {"submit_disabled": bool, "code_boxes": int, "captcha_frame": bool,
         "signin_prompt": bool}
    Criteria keys come from the Gate enum, so the choice options can never drift
    from the typed vocabulary.
    """
    ev = evidence or {}
    return {
        "state": {
            "submit_disabled": bool(ev.get("submit_disabled")),
            "code_boxes": int(ev.get("code_boxes") or 0),
            "captcha_frame": bool(ev.get("captcha_frame")),
            "signin_prompt": bool(ev.get("signin_prompt")),
        },
        "questions": {
            "gate": {
                "type": "choice",
                "instructions": "Which blocker best explains a form that will not submit?",
                "criteria": {
                    Gate.CAPTCHA.value: "a captcha challenge is present or the submit silently no-ops",
                    Gate.ACCOUNT_WALL.value: "a sign-in / create-account wall is blocking the form",
                    Gate.EMAIL_CODE.value: "an email security-code input is waiting for a code",
                    Gate.SILENT_NOOP.value: "form looks valid but submit does nothing",
                    Gate.OK.value: "no blocker — the form is ready to submit",
                },
            },
        },
    }


def gate_from(raw):
    """Parse a raw blocker string (e.g. a Jev answer) back into a Gate.

    Unknown strings become Gate.UNKNOWN instead of raising, so a classifier
    miss is a value, not a crash.
    """
    try:
        return Gate(str(raw or "").strip().lower().replace("_", "-"))
    except ValueError:
        return Gate.UNKNOWN


def candidate_fit_question(title: str):
    """Jev choice payload for a borderline title the deterministic gate could not settle."""
    return {
        "state": {"title": str(title or "")},
        "questions": {
            "fit": {
                "type": "choice",
                "instructions": "Is this title a QA/SDET role inside the user's stack scope?",
                "criteria": {
                    "ready": "QA/SDET/test-automation role, stack is acceptable",
                    "mismatch": "not a QA/SDET role, or stack is out of scope",
                },
            },
        },
    }


def _smoke():
    """Exercises every export so the module is self-checking (and vulture-clean)."""
    from config.answers import A  # noqa: F401 - proves the import path works

    assert classify_candidate("", "QA Engineer") == CandidateClass.MISMATCH
    assert classify_candidate("Acme", "Frontend Developer") == CandidateClass.MISMATCH

    rows, problems = validate_work_history(
        [{"employer": "Test", "title": "Software Developer", "start": "2019", "current": True}],
        [{"employer": "Bottomline", "title": "Senior QA Engineer"}],
    )
    assert rows and problems, "junk 'Test' row must be flagged"

    assert proof_status("") == "blocked"
    assert proof_status("Thank you for applying") == "submitted-awaiting-email"
    assert proof_status("Thank you for applying", email_confirmed=True) == "confirmed-email"

    assert [c.value for c in extract_code("code: ABCDEF12 and 123456")]

    plan = plan_field("Email Address")
    assert plan and plan.value, "known label must resolve from config.answers"
    assert plan_field("some novel question") is None

    for phase, event in [("form", "request_code"), ("request", "code_sent"),
                         ("wait-code", "code_entered"), ("signin", "signed_in")]:
        assert route_auth(AuthPhase(phase), event) != AuthPhase.BLOCKED
    assert route_auth(AuthPhase.FORM, "bogus") == AuthPhase.BLOCKED

    # Gate round-trip: Jev answer string -> typed Gate, UNKNOWN on a miss.
    assert gate_from("captcha") == Gate.CAPTCHA
    assert gate_from("account_wall") == Gate.ACCOUNT_WALL
    assert gate_from("bogus") == Gate.UNKNOWN
    gq = gate_questions({"submit_disabled": True, "code_boxes": 0,
                         "captcha_frame": False, "signin_prompt": True})
    assert gq["questions"]["gate"]["criteria"][Gate.CAPTCHA.value]
    assert field_question("Are you authorized to work in India?", ["Yes", "No"])["state"]["options"]
    assert candidate_fit_question("SDET")["questions"]["fit"]
    assert _answers() is A  # the lazy loader returns the shared A dict

    print("decide: smoke OK — all typed decisions exercised")


if __name__ == "__main__":
    _smoke()
