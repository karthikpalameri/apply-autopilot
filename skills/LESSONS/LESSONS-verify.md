# VERIFY LESSONS

Proof-gating rules for "did my application actually submit?". Mechanics only — no employer names.

## THE PROOF HIERARCHY (use ≥2 sources)
1. **Inbox confirmation email** — subject names the role/req-id and carries the authoritative date.
2. **Success URL / page** — e.g. GH `/confirmation` or `/embed/job_app/confirmation?for=<org>&token=<id>`, Phenom `/applythankyou?status=success` (+ candidateId), Lever `/thanks`, Workday `/jobTasks/completed/application`, SuccessFactors "Successfully Applied".
3. **Body text** — "Applied" marker or Apply-button-gone.

A "Applied" marker on LinkedIn is NOT proof (it can be stale) — the ATS thank-you is proof.

## RULES
- AFTER EVERY submit → MUST read the positive final message (OCR/DOM): "Thank you for applying" / "Application Submitted" / Lever `/thanks` / Workday completed page.
- NEVER report "submitted" on inference (form closed / button gone / errs=0 ≠ done).
- If the positive message is ABSENT → NOT done → keep fixing (agentic loop) or record `in-progress: <exact blocker>`.
- Record the EXACT proof text in `progress.json` (proof field) — not a paraphrase.
- Capture proof IN the same action as submit; if the page navigates away the proof is lost. Do NOT re-verify by re-navigating (a GH confirmation URL can reload to the plain job page).
- GH embed option-click proof BEFORE submit: read the control innerText (auth=Yes/visa=No/…) + checkbox states, then submit.
- LinkedIn Easy Apply is UNREADABLE headless (Applied tab virtualized; job page hides the Apply button but shows no "Applied" text). Apply-button-gone = best-effort signal → record as best-effort, do NOT count as hard-verified. Always run the **visible** browser.

## DUP GATE
- A "previous application" page = NOT a new application — never count it as applied.
- OCR beats a11y: a11y can show stale/doubled values.

## KAIZEN
- Any new win/lesson → standardize → next session baseline.
- The easy-apply stuck-Review FIX: DOM click 2-3× with 6s waits + consent via a raw checkbox + getByRole Submit.
- Phone "too long" error = wrong country code picked — verify the country option exactly.

## RELATED
- `skills/verify/SKILL.md` · `skills/apply/SKILL.md` · `skills/REFERENCE.md`
- `skills/LESSONS/LESSONS-apply.md`
