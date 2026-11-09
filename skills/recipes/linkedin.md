# LINKEDIN RECIPE

## LOGIN (NEW page — anti-bot)
- refs: `textbox "Email or phone"` / `textbox "Password"` / `button "Sign in"`
- NO input#username (random ids). Google/Apple = alternative path
- Google: passkey wall → "Try another way" → "Enter your password" → skip home/profile prompts
- Naukri: Apply button needs mouse-event dispatch (mousedown/up/click)

## FINDING JOBS
- One scoped DOM extraction for the visible listing page; LinkedIn is virtualized, so use the jobs-guest API/loaded body text for the full card set.
- Cache the next three `{company, exact role, LinkedIn ID, ATS URL/domain}` tuples and do not rescan unchanged pages.
- Verify POSTING company (staffing re-tags: "Takeda"→"Innova ESI") before opening an ATS.
- f_EA unreliable via API; verify Easy Apply controls in the live page.
- Card extraction (proven 2026-11-05): `browser_evaluate` over `[componentkey^="job-card-component-ref"]`, regex `/(\d{9,})/` on the componentkey for the job id. **Do not hand-loop `ul.scrollTop += 2000` ×14** — measured 3.53 s of scrolling that always runs to the end. Use `core.ui.scroll_until(pred, container='ul.scrollTop', max_ms=3000)` from `skills/recipe-lib` (see **`skills/RELIABILITY.md#bounded-scrolling`**) — it stops at the last card, not at a fixed count. Returns 25 cards/page. Old `li[data-occludable-job-id]` is DEAD — 0 matches in the 2025+ UI.
- Search URL that works: `/jobs/search/?keywords=SDET&location=Bengaluru%2C%20Karnataka%2C%20India&f_TPR=r604800&f_AL=true&sortBy=DD` (+`&start=25` to page).
- Return each card as ONE flat string (`id :: company :: role`). Arrays of objects get truncated by output limits — flat strings survive.

## APPLY (easy-apply)
- Fill → direct upload → submit → capture the live ACK immediately → proof.

### VERIFY DOM STATE, NOT SCREEN (proven — cut every bad submit)
Before clicking Next/Review, dump every field in ONE call and read it back:
```js
[...document.querySelectorAll('input,select,textarea')]
  .filter(e => !/radio|checkbox/.test(e.type))
  .map(e => `${e.tagName}#${e.id}|` +
    (e.closest('label')?.innerText || e.getAttribute('aria-label') || '').replace(/\n+/g,' ').trim().slice(0,70) +
    '=' + (e.value||''))
```
- Resume step: check `input[type=radio]:checked` → its `aria-label` must equal the target PDF name. 22 radios render for ~21 duplicates; only ONE is checked.
- Error sweep in same call: `[role="alert"], .artdeco-inline-feedback--error` → must be `[]`.
- Prefer flat strings over object arrays (output truncation eats nested JSON).
- Job page "Application status: Application submitted" + Apply button GONE = submitted. If Easy Apply still renders and no status block exists, the past submit did NOT land — redo it.

### MODAL SCOPE + CLICK TARGETS (proven)
- New UI has NO `button.jobs-apply-button`. Click `role=button[name="Easy Apply"]`.
- Scope all dialog queries to `[data-testid="dialog-content"]` — the page behind has its own buttons.
- `role=button[name="Next"]` hits strict-mode violations (carousel has "Next" too). Always use `[data-testid="dialog-content"] button:has-text("Next")`.
- A profile-upsell modal (`Not now` / `Update profile`) overlays the page after submit and intercepts pointer events; `#interop-outlet` also blocks clicks. Do not fight it — proof is already captured; `browser_navigate` to the next job instead.
- Optional page 3 ("Mark as top choice") has zero inputs — just click Next.

### PAGE MAPS SEEN LIVE
- 4-page: contact → resume → (top choice) → questions → Review. 7-page: contact(+postal/country) → resume → (top choice) → work exp → education → questions → Review.
- Work-experience and education render in Ember, NOT as plain inputs — `querySelectorAll('input')` returns `[]`. Read `[data-testid="dialog-content"].innerText` instead; it is already populated and satisfies "(1 required)".
- Clicking Next on the education page can land on **Edit education** by accident. That is fine — set Degree=`Bachelor`, Field=`Computer_Engineering`, then click Save, then Next.
- Country/phone selects: values are opaque (`IND_91`, `IND`, `in`); select by visible text (`India (+91)`, `India`) and read back the value.
- Filling 5+ text fields at once: one `browser_fill_form` call, then read back all ids. Batch fills do not always fire per-field blur — verify before Next.
- Common question set: total yrs automation=8, agentic-AI yrs=2, current/expected CTC, notice, LinkedIn URL — **read every value from `config/user.json` via `config/answers.py`** (`A['ctc']`, `A['expected']`, `A['notice']`, `A['linkedin']`). Never hardcode them here: **`skills/REFERENCE.md#identity`** is the one source. Also: authorized=Yes, sponsorship=No, RTO 5-day=Yes, know anyone=No. Leave optional Website blank.
- Batch related field fills and readbacks in one stable-page script; ordinary text uses `.fill()`, React/custom controls use the proven exact-option or real-mouse path.
- "Apply on company website" → external ATS (popup tab — check browser_tabs); use the employer URL directly after verifying company/domain.

## ABANDONED / SAVE-FOR-LATER RECOVERY
- Do not refresh, navigate, switch tabs, or restart the browser while the Easy Apply modal contains data; LinkedIn can discard the live modal state and leave only a tracker entry.
- Recovery path: LinkedIn **Jobs → Job tracker → In Progress → Draft**. Also inspect **Clicked apply** when the form was opened but no draft was persisted.
- Open the draft card itself and resume only if the job is still accepting applications. If it says **No longer accepting applications**, do not retry or delete it automatically; record it as `blocked`/closed.
- A visible `Draft` count is the reliable discovery signal; `Applied` is not proof of submission. Submit only after the positive acknowledgement is captured, then Gmail-check and reconcile.

## EASY APPLY (proven — JoVE)
- Modal flow: basics → Next → resume (**inject, do not click** Upload resume — that button opens the native picker; procedure at **`skills/resume/SKILL.md#upload-method`**) → Next/Review → questions → Submit application
- Fields DOUBLE on reuse (NameName) + phone gets describe-text concat — ALWAYS clear via browser_press_key Meta+A+Backspace → retype → OCR-verify
- "How soon can you join? (In days)" = 32 (available from 28 Nov 2026, LWD 27 Nov 2026)
- Review = DOM click (ref churn); Submit application = getByRole click
- Browser process can die mid-modal (seen 2026-11-05 on JazzX). Recovery: `browser_close` → check `ps aux | grep -i cloakbrowser` is empty → reopen the job URL → re-read "Application status". If it shows `Application submitted`, it landed; if Easy Apply is still there, redo from page 1. Never assume.
- PROOF: capture "Your application was sent to <company>!" or "You can keep track of your application in the Applied tab of My Jobs" live before leaving the FORM. Then map the employer confirmation in one Gmail batch; LinkedIn-only ACK remains `submitted-awaiting-email`.
