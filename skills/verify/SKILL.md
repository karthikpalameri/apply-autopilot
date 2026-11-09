---
name: verify
description: VERIFY node — proof gate. Ground truth only, never inference. Caveman.
parent: skills/SKILL.md
---

# VERIFY (proof gate)

## DONE = PROOF ONLY (user called out 5+ times — NEVER over-claim)
- ✅ Employer success page/URL captured in the current FORM state: GH `/confirmation` + "Thank you for applying. Your application has been received." · Phenom `/applythankyou` · Lever `/thanks` · Workday `/jobTasks/completed/application` + "Application Submitted" · LinkedIn EA "Applied tab of My Jobs"
- ✅ Gmail confirmation email naming the exact role ← STRONGEST (esp. LinkedIn Easy Apply)
- ❌ form-closed + errs=0 ≠ done · "Application submitted/sent" (LinkedIn-only ack) ≠ employer-confirmed → `submitted-awaiting-email` until inbox proof (`confirmed-email`)
- The positive message VARIES by ATS (Black Duck = "Thank you for your interest…") — OCR/DOM-read the ACTUAL page; never regex-guess. No positive message read = NOT counted. Period.

## ACTION RELIABILITY
- Follow `skills/RELIABILITY.md`: pre-check → action → post-check (exact field value/state) on every step. A failed post-check = retry once with a fresh locator, then record the exact blocker.

## TAB SAFETY
- Follow **`skills/REFERENCE.md#two-tab-session`**. Capture employer proof in the submitted FORM tab before switching. Multi-role batch: capture all page proofs immediately, then ONE combined Gmail search mapped back to cached role tuples.

## GROUND TRUTH (in order)
1. **Scoped DOM**: field values, attachment filename, exact success text/URL and Gmail confirmation. Accessibility snapshots can be stale; re-read the live form.
2. **Local OCR of a viewport crop** only if success/error text is visual-only. Return text, never the raw image to the model; see `skills/REFERENCE.md#screenshot-budget-measured-2026-11-07--the-single-biggest-token-sink`.
3. HTML dumps + DOM rects for disputed click targets. A screenshot alone is never proof.

## CAPTCHA RULE
- Complete and verify all non-CAPTCHA required fields first (target ~99% of the application), then stop at reCAPTCHA/hCaptcha/image-puzzle and ask the user to solve it in the visible browser. Never bypass or solve it. Resume only after the user completes it; never report past an unsolved CAPTCHA.

## ERROR-DRIVEN SUBMIT (read the error, fix, retry)
- Submit → READ the error (DOM `[class*=error]`/`[aria-invalid=true]` + OCR) → fix the EXACT field → re-submit. Errors appear ONE at a time (GH/LinkedIn) — loop until the positive message or record in-progress.
- "Invalid input" = wrong format (CTC = number `3300000`, not "<your current CTC>") — check the field type.

## THE HARD-ASSERT (MANDATORY — call it in CODE, not just by eye)
```text
from core.hard_assert import assert_applied
proof = assert_applied(b, "<Company>")   # OCR + DOM read → positive msg or AssertionError
```
- Every submit ends with `assert_applied()` — NO exception = NOT done, do NOT record. AssertionError → read error → fix → re-submit → assert again. OCR = ground truth; DOM innerText = backup; assert against BOTH.

## RECORD
- Before applying, use Gmail plus the **ledger** (`core.applied_ledger.py`), `scratch/APPLIED.md`, and LinkedIn Applied/Job Tracker as duplicate/status evidence. After each attempt, call `core.applied_ledger.record(...)` (append-only — the authority) and mirror `config/progress.json`; record duplicate gates and blockers without deleting history. Statuses: `confirmed-email` | `submitted-awaiting-email` | `blocked`.
- **Typed status mapping:** `core.decide.proof_status(found_text, email_confirmed)` maps submit evidence to the canonical ledger status. `core/verify.py` prints this now — use it instead of hand-picking a status string.

## LESSONS
- skills/LESSONS.md
