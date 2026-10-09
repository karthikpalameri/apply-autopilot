# EMAIL LESSONS

Generic email workflow for cold outreach and application follow-ups. No real addresses here — your send/receive accounts live in `config/user.json` (git-ignored).

## DRAFT FIRST, SEND LATER
- Always create a FRESH draft for each recipient (editing an existing draft is flaky); **never send** without an explicit, fresh approval from the user.
- Attach the resume to the draft and include a "Found via <source>" line so the recipient can trace the referral.
- Keep the body in `skills/recipes/email-template-humble.md` (the humble template) — personalize the first line per company/role.

## OTP / VERIFICATION ORDER
- Trigger the "Send OTP" or verification-link action on the webpage FIRST; then check or refresh the Gmail tab for the newly generated code/link.
- Do NOT search Gmail first and do NOT reuse an older OTP/link.
- Prefer visible Gmail/Google sign-in, then LinkedIn sign-in, before email/password and finally email OTP.
- Rate-limit guard: one webpage OTP request → one refresh of a separate persistent GMAIL tab → back to VERIFY. HTTP 429 or no fresh message = a blocker, not a reason to resend.

## TWO-TAB MODEL
- Keep FORM/VERIFY and GMAIL as two explicit tabs; switch by current tab ID instead of navigating the verification tab to Gmail.
- Read the authoritative DATE + request-id from the confirmation email and update both trackers to match.

## CONSENT
- Cold emails and ATS sign-up emails are **draft-by-default**. Sending requires the user's fresh approval (see `gmail_consent` set during onboarding).

## RELATED
- `skills/email/SKILL.md` · `skills/recipes/email-template-humble.md` · `skills/REFERENCE.md`
- `skills/LESSONS/LESSONS-verify.md`
