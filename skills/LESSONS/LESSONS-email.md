# EMAIL LESSONS
## 2026-08-12
- Kotak811 draft (recruiter@example.com) + M2P Fintech (hr@example.com) = saved Gmail drafts, resume-attached, "Found via" links
- Always create a FRESH draft (editing flaky); never send

## 2026-09-23
- OTP/verification order: trigger Send OTP or the verification-link action on the webpage first; then check or refresh Gmail for the newly generated code/link. Do not search Gmail first or reuse an older OTP/link.
- Authentication preference: when offered, use visible Gmail/Google sign-in first, then LinkedIn sign-in/apply, before email/password and finally email OTP.
- Speed/rate-limit guard: make one webpage OTP request, switch to a separate persistent GMAIL tab for one refresh, then switch back to VERIFY; HTTP 429 or no fresh message is a blocker, not a reason to resend.
- Keep FORM/VERIFY and GMAIL as two explicit tabs; use `browser_tabs` `switch` by current tab ID instead of navigating the verification tab to Gmail.
