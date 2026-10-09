# LINKEDIN RECIPE

## LOGIN (NEW page — anti-bot)
- refs: `textbox "Email or phone"` / `textbox "Password"` / `button "Sign in"`
- NO input#username (random ids). Google/Apple = alternative path
- Google: passkey wall → "Try another way" → "Enter your password" → skip home/profile prompts
- Naukri: Apply button needs mouse-event dispatch (mousedown/up/click)

## FINDING JOBS
- One scoped DOM extraction for the visible listing page; LinkedIn is virtualized, so use the jobs-guest API/loaded body text for the full card set.
- Cache the next three `{company, exact role, LinkedIn ID, ATS URL/domain}` tuples and do not rescan unchanged pages.
- Verify POSTING company (staffing re-tags: "AcmeTen"→"Innova ESI") before opening an ATS.
- f_EA unreliable via API; verify Easy Apply controls in the live page.

## APPLY (easy-apply)
- Fill → direct upload → submit → capture the live ACK immediately → proof.
- Batch related field fills and readbacks in one stable-page script; ordinary text uses `.fill()`, React/custom controls use the proven exact-option or real-mouse path.
- "Apply on company website" → external ATS (popup tab — check browser_tabs); use the employer URL directly after verifying company/domain.

## ABANDONED / SAVE-FOR-LATER RECOVERY
- Do not refresh, navigate, switch tabs, or restart the browser while the Easy Apply modal contains data; LinkedIn can discard the live modal state and leave only a tracker entry.
- Recovery path: LinkedIn **Jobs → Job tracker → In Progress → Draft**. Also inspect **Clicked apply** when the form was opened but no draft was persisted.
- Open the draft card itself and resume only if the job is still accepting applications. If it says **No longer accepting applications**, do not retry or delete it automatically; record it as `blocked`/closed.
- A visible `Draft` count is the reliable discovery signal; `Applied` is not proof of submission. Submit only after the positive acknowledgement is captured, then Gmail-check and reconcile.

## EASY APPLY (proven — AcmeTwentyFive)
- Modal flow: basics → Next → resume (Upload resume btn → filechooser) → Next/Review → questions → Submit application
- Fields DOUBLE on reuse (Janejane) + phone gets describe-text concat — ALWAYS clear via browser_press_key Meta+A+Backspace → retype → OCR-verify
- "How soon can you join? (In days)" = 0 (Immediate — serving notice, LWD <your last working day>)
- Review = DOM click (ref churn); Submit application = getByRole click
- PROOF: capture "Your application was sent to <company>!" or "You can keep track of your application in the Applied tab of My Jobs" live before leaving the FORM. Then map the employer confirmation in one Gmail batch; LinkedIn-only ACK remains `submitted-awaiting-email`.
