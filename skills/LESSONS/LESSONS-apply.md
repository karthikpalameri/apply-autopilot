# APPLY LESSONS — compressed by topic (was 51 dated retros)

Read once before an apply session. Canonical rules live in **`skills/REFERENCE.md`**; this file keeps ATS-specific facts.

## PROOF (never over-claim — user called out 5+ times)
- "errs=0 + form closed" ≠ submitted (Zscaler#2). Proof = employer success page/URL + Gmail email. LinkedIn EA "submitted/sent" = `submitted-awaiting-email` ONLY (Dover/Bajaj 08-27 correction).
- Success strings: GH "Thank you for applying. Your application has been received." (Black Duck = "Thank you for your interest in joining our team at Black Duck Software…"); Phenom `/applythankyou?status=success` (+candidateId); Lever `/thanks`; Workday `/jobTasks/completed/application` + "Application Submitted"; SF "Successfully Applied"; UKG "Thank you! Your application was submitted."; LinkedIn EA "Your application was sent to <Co>!" (capture LIVE — unreadable later).
- Email subjects: "Thank you for applying to X" / "X has your application!" / "We've received your job application". Hard-verify = success page AND inbox email (subject+date). Statuses: `submitted-confirmed` | `submitted-awaiting-email` | `blocked`.
- Capture proof IN the current FORM state; never re-visit later (Fivetran URL reloads to plain job page). OCR-read the ACTUAL text — regex variants fail.
- CAPTCHA after Submit = failed/unverified → user solves in visible browser; keep tab active; never bypass or abandon silently. Record exact blocker text+URL; account/CAPTCHA/closed roles = blocked.

## FORM WIPE / ONE-SHOT TRANSACTION
- Nav between fill/submit wipes client state (GH); Workday account saves server-side → resume `/apply`. Zero nav: open→fill→upload→submit.
- GH embed submit RESETS the form on any failed attempt → refill everything each submit.
- One `browser_run_code_unsafe` per stable page: combos/picks FIRST (re-render wipes them) → texts LAST → submit same run. Never one call per field.
- Re-render churn: re-read values after each fill; verify selected label/value, phone, and resume filename before submit.

## SELECTS & INPUTS (proven recipes)
- Workday selects: ONLY `run_code_unsafe` + `page.getByRole('option',{name,exact:true}).first().click()` commits (~20 methods fail). Open select button first; verify via `getByRole('button').allInnerTexts()`; "Male" ×2 → exact+first.
- GH react-selects: click control → `pressSequentially` (real keys) → ArrowDown (some open menu) → exact option click. Scope options `[class*=select__menu] [role=option]` (unscoped collides with intl-tel ~260 dial codes). Country="India +91" (not "India"); location="Bengaluru, Karnataka, India"; start="I can start right away".
- GH education selects (`school--0/degree--0/discipline--0`) = SYSTEMATIC BLOCKER: typeahead "No options", setV+blur doesn't commit → SKIP the form. Simple GH (no edu) = winning pattern.
- GH fields: basics `first_name/last_name/preferred_name/email/phone` + `question_XXXX` custom; NEW embed uses `#id` not name; resume input appears only after clicking the dropzone (`.file-upload__wrapper`) → `setInputFiles`; filename in `.file-upload__filename` = proof; submit → `/embed/job_app/confirmation?for=<org>`.
- GH consent = checkbox group `input[name^=question_...][value=...]` → `.check({force:true})`; GDPR `name*=consent` (Black Duck).
- Phone typing APPENDS/mangles ("000000 00000", "Janejane") → ALWAYS native-set clean value (or Meta+A+Backspace + real keys) then read back. intl-tel self-formats "00000 00000" — accept. +91 forms: `+91-0000000000`; Workday = 10-digit no +91; postal `<postcode>` (no space).
- `browser_press_key` = THE keyboard tool (`browser_keyboard` = phantom). Workday textareas accept ONLY real per-char keys (native setter rejected "required").
- Real trusted mouse (`page.mouse.click`@coords) beats JS `.click()` on custom React editors (LI EA Yes/No radios, edu grids). scrollIntoView → getBoundingClientRect → click(center) → re-check.
- LinkedIn EA new render: no `[role=dialog]`/form/file-input; text inputs indexed nth; radios = real mouse; "Applied tab" unreadable headless → capture "sent" live. Stuck Review = click 2-4× with waits; consent = RAW checkbox click.
- Phenom: `.fill()` only (htype/native APPENDS, React won't commit); degree auto-picks "Associates" → set "Bachelor of Engineering", school "<your university>"; current-role = `experienceData[0].fromTo.currentlyWorkHere`; resume alert "Uploaded Resume Successfully" → handle_dialog(accept); resume upload MANDATORY.
- Oracle HCM: T&C = `button.app-dialog__footer-button`; cx-select = click+type+EXACT click (typing alone won't commit); pills `span.cx-select-pill-name`; email id `primary-email-0/1` varies.
- Select2 (AcmeEighteen): open → inspect `.select2-results__option` → exact click.
- Salary fields = number-only `<expected CTC numeric>` (never "<expected CTC>"/"<current CTC>"); historical <historical CTC values> superseded by the 22% rule.
- MCQ screens (Headout): read ALL options first; POM=breaks-abstraction, uniqueness=Set-approach, stale=retry-wrapper; years = checkbox groups clicked by label.
- Workday month/date widgets resist automation → user entry.

## ATS ROUTING (win-rate: GH embed > Phenom > LinkedIn EA > SuccessFactors > iCIMS)
- GH standalone embed `/embed/job_app?for=<org>&token=<id>` = cleanest (skip careers page). SPA wrapper (Fivetran/Okta): iframe hidden 0×0 until `dispatchEvent('click')` on `a[data-click-target=job-application]`.
- GH recaptcha auto-passes mostly; invisible v2 needs CapSolver `isInvisible:true` + EXACT embed URL (stale URL → 400). GH SPA submit does NOT honor the CapSolver token → human 1-click. Escalation = 8-char email code → 8 split inputs `#security-input-0..7` (maxLength=1) → Submit enables (AcmeFive/Glean/Groww/Britive).
- iCIMS: direct job URL redirects to intro/Welcome = the trap. Real path: iCIMS Search (searchKeyword) → real-mouse job title → detail → Apply → GDPR gate `css_loginName` + `accept_gdpr` (`.check({force:true})`) → Next (JS-gate may resist; retry label-click + dispatch + mouse).
- SF: `/errorpage?errortype=Exception` on deep-links (jobs.netapp.com); `careers.netapp.com` works. Unknown password: Forgot password → reset URL (preserves `career_job_req_id`) → policy pw (8-18, upper+lower+digit+punct) → login → profile prefills + resume pre-attached ("Add a Document" widget has no real `input[type=file]`). rcmpaginatedselect = mouse-open → option-click.
- Jobvite: consent select+Submit BEFORE the form; no "LinkedIn" source → "Web Search"; invisible reCAPTCHA may reset after Send.
- Workday: tenant = grep careers page for `wd[0-9].myworkdayjobs.com`; UP-check = HTTP 200 on `/en-US/<site>/search` (NOT cxs). Job Board source = CATEGORY chevron → expand → LinkedIn.com (no referral follow-up). Disclosures "Prefer not to answer". Global outages happen → probe `core/wday_probe.py` first.
- BrassRing: canonical resume attached BEFORE Continue ("Start Your Application" not enough).
- Rippling: Apply disabled until consents committed (check `aria-checked`); map questions via `__NEXT_DATA__…activeJobApplication` by UUID.
- Always compare company/role/ATS-ID/domain before fill (Eightfold→volkscience.com = MISMATCH). Missing file input = blocker.

## LOGINS / OTP / ACCOUNTS
- Provider order: Google → LinkedIn → email/password → email OTP. Visible buttons only; never duplicate accounts. Prefer "Sign in with LinkedIn" over unknown passwords (Workday/SF/Lever).
- Google: passkey → Try another way → password → skip home-address. LinkedIn new page: Google/Apple + refs (`input#username` gone). Naukri: header Login closes modal → click modal submit.
- OTP: request on the webpage FIRST → then fresh Gmail read → enter. Never search Gmail first / reuse a stale code (Oracle sends a NEW code each time; 30-min lock after fails). HTTP 429 → stop.
- Reset links single-use; one reset/site/session; "You have already used this link" = loop → stop. Signup must be atomic: vault credential (OS keychain/pw manager) BEFORE entry → immediate sign-in → verify auth state; never generate-and-lose.
- Okta escalated OTP (8-char code) → form won't complete → timebox. PAN/Aadhaar/unknown DOB → never guess (HDFC AcmeSixteen).

## FINDING / DEDUPE
- LinkedIn a11y = 1 virtualized card → jobs-guest API; staffing cos re-tag jobs ("AcmeTen"→"Innova ESI") → verify posting company; f_EA unreliable via API.
- Before applying, check `config/progress.json`, `scratch/APPLIED.md`, LinkedIn Applied/Job Tracker, and Gmail. Match company + exact role + LinkedIn/ATS IDs + employer domain. Skip an already attempted/confirmed exact role even if reposted with a new ID; if uncertain, reconcile/skip. Fivetran is an explicit repeat-application warning.
- `web_search`/SearXNG finds portal-only roles: `<product> QA SDET Bangalore greenhouse/lever/icims` (found Glean/Quince/HackerEarth/Konovo/JFrog). Verify board live via `boards-api.greenhouse.io/v1/boards/<slug>/jobs`; search URLs 404 fast.
- NEVER trust a recorded "blocked" — re-verify live (NetApp, AcmeNine false blockers). Try multiple domains/paths + the real apply button.
- `config/profile.json` absent → don't retry; use `user.json`/`answers.py`.
- BLR product-co QA pool on clean boards is near-exhausted — expect ~1-2 clean EA wins/session.

## SESSIONS / LOCKS
- MCP 400 "profile active (dead pid)" → `rm runtime/mcp-session/.cloakbrowser-mcp-profile.lock` + restart. One persistent-profile session at a time; sid `config/mcp_session.json` (stale → delete). Zombie Chromium → `lsof +D <profile>` kill.

## SPEED (audit: 2,310 waitForTimeout = 39m57s wasted)
- Preflight 3 roles once; cache tuples; classify before opening any ATS. Read the selected recipe once/session.
- One scoped discovery → one sequential transaction → one targeted readback per stable state; condition waits, no stacked sleeps.
- Gmail per role in one-by-one mode (combined search = explicit batch mode only). Batch tracker writes after proof gates. Parallelism only for independent read-only work.

## COMPANY-SPECIFIC QUICK NOTES
- Fox Workday: full win via option-click commits; proof `/jobTasks/completed/application`. Databricks: 2 file inputs → `.first()` = resume. HackerRank: years max "7+"; combos need ArrowDown to open. Blink: 4× years questions (8/6/4/6); phone input `name≠phone` → aria-label.
- AcmeOne EA: unchecked radio GROUPS block Review → click every group's Yes. AcmeTwentySeven: 7 react-selects + 2 consents. AcmeSelect: start = open empty → "Immediately" (user rule). AcmeSmartRecruiters: 7-page EA; SmartRecruiters → external careers → timebox+skip.
- AcmeNineteen: consent+verify-password; "already exists" → Sign In tab. Cisco Phenom: no-popup upload via `setInputFiles` + `cloak` global; proof `/applythankyou?status=success` + "Your Cisco Journey Begins Here".
- AcmeSeventeen Workday: "Congratulations! Thank you for applying…" + Gmail "Your job application with AcmeSeventeen" = the 2-source pattern. Darwinbox/The Standard India: "submitted" but no app email → awaiting; salary numeric-only.
- AcmeTwelve: Google sign-in lives in a cross-origin iframe → `frameLocator('iframe[title="Sign in with Google Button"]')`; close the "Stay Ahead" modal before card clicks (`Timeout 30000ms` = modal intercept).
- AcmeFifteen/GH: phone country selector ≠ job-location Country question; read back the hidden phone-country value as valid. Fivetran: address block + LinkedIn + preferred name = separate text Qs; fill all.
