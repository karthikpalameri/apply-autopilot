# APPLY LESSONS — compressed by topic

Read once before an apply session. Canonical rules live in **`skills/REFERENCE.md`**; this file keeps ATS-specific facts. Company names are intentionally omitted — these are mechanics that apply to any employer.

## PROOF (never over-claim)
- "errs=0 + form closed" ≠ submitted. Proof = employer success page/URL **AND** inbox email (subject + date).
- Success strings: GH "Thank you for applying. Your application has been received."; Phenom `/applythankyou?status=success` (+ candidateId); Lever `/thanks`; Workday `/jobTasks/completed/application` + "Application Submitted"; SuccessFactors "Successfully Applied"; UKG "Thank you! Your application was submitted."; LinkedIn EA "Your application was sent to <Co>!" (capture LIVE — unreadable later).
- Email subjects: "Thank you for applying to X" / "X has your application!" / "We've received your job application". Hard-verify = success page AND inbox email. Statuses: `submitted-confirmed` | `submitted-awaiting-email` | `blocked`.
- Capture proof IN the current FORM state; never re-visit later (a GH confirmation URL can reload to the plain job page). OCR-read the ACTUAL text — regex variants fail.
- CAPTCHA after Submit = failed/unverified → user solves it in the **visible** browser; keep the tab active; never bypass or abandon silently. Record exact blocker text + URL.

## FORM WIPE / ONE-SHOT TRANSACTION
- Navigating between fill and submit wipes client state (GH); Workday accounts save server-side → resume with `/apply`. Zero nav: open → fill → upload → submit.
- GH embed submit RESETS the form on any failed attempt → refill everything each submit.
- One `browser_run_code_unsafe` per stable page: combos/picks FIRST (re-render wipes them) → texts LAST → submit in the same run. Never one call per field.
- Re-render churn: re-read values after each fill; verify selected label/value, phone, and resume filename before submit.

## SELECTS & INPUTS (proven recipes)
- Workday selects: ONLY `run_code_unsafe` + `page.getByRole('option',{name,exact:true}).first().click()` commits (~20 other methods fail). Open the select button first; verify via `getByRole('button').allInnerTexts()`; when a label repeats ("Male" ×2) use exact + first.
- GH react-selects: click control → `pressSequentially` (real keys) → ArrowDown (some open the menu) → exact option click. Scope options `[class*=select__menu] [role=option]` (unscoped collides with intl-tel ~260 dial codes). Country = "India +91"; location = "<city>, <state>, India"; start = "I can start right away".
- GH education selects (`school--0/degree--0/discipline--0`) = SYSTEMATIC BLOCKER: typeahead "No options", setV+blur doesn't commit → SKIP the form. Simple GH (no edu) = winning pattern.
- GH fields: basics `first_name/last_name/preferred_name/email/phone` + `question_XXXX` custom; newer embeds use `#id` not name; the resume input appears only after clicking the dropzone (`.file-upload__wrapper`) → `setInputFiles`; filename in `.file-upload__filename` = proof; submit → `/embed/job_app/confirmation?for=<org>`.
- GH consent = checkbox group `input[name^=question_...][value=...]` → `.check({force:true})`; GDPR `name*=consent`.
- Phone typing APPENDS/mangles → ALWAYS native-set a clean value (or Meta+A+Backspace + real keys) then read back. intl-tel self-formats; accept it. +91 forms use `+91-<10 digits>`; Workday = 10-digit with no +91; postal = `<postcode>` (no space).
- `browser_press_key` = THE keyboard tool (`browser_keyboard` = phantom). Workday textareas accept ONLY real per-char keys.
- Real trusted mouse (`page.mouse.click`@coords) beats JS `.click()` on custom React editors (radios, edu grids): scrollIntoView → getBoundingClientRect → click(center) → re-check.
- LinkedIn EA new render: no `[role=dialog]`/form/file-input; text inputs indexed nth; radios = real mouse; "Applied tab" unreadable headless → capture "sent" live. Stuck Review = click 2-4× with waits; consent = RAW checkbox click.
- Phenom: `.fill()` only (htype/native APPENDS); degree auto-picks "Associates" → set "Bachelor of Engineering", school "<your university>"; current-role = `experienceData[0].fromTo.currentlyWorkHere`; resume alert "Uploaded Resume Successfully" → handle_dialog(accept); resume upload is MANDATORY.
- Oracle HCM: T&C = `button.app-dialog__footer-button`; cx-select = click + type + EXACT click; pills `span.cx-select-pill-name`; email id `primary-email-0/1` varies.
- Select2: open → inspect `.select2-results__option` → exact click.
- Salary fields = number-only `<expected CTC numeric>` (never "<expected CTC>"); use your configured 15-25%-above-current rule.
- MCQ screens: read ALL options first. Years = checkbox groups clicked by label.
- Workday month/date widgets resist automation → user entry.

## ATS ROUTING (typical win-rate: GH embed > Phenom > LinkedIn EA > SuccessFactors > iCIMS)
- GH standalone embed `/embed/job_app?for=<org>&token=<id>` = cleanest (skip the careers page). SPA wrappers: the iframe is hidden 0×0 until `dispatchEvent('click')` on `a[data-click-target=job-application]`.
- GH recaptcha auto-passes mostly; invisible v2 needs CapSolver `isInvisible:true` + the EXACT embed URL (stale URL → 400). Some GH SPA submits don't honor the CapSolver token → human 1-click. Escalation = 8-char email code → 8 split inputs `#security-input-0..7` (maxLength=1) → Submit enables.
- iCIMS: a direct job URL redirecting to intro/Welcome is the trap. Real path: iCIMS Search (searchKeyword) → real-mouse job title → detail → Apply → GDPR gate `css_loginName` + `accept_gdpr` (`.check({force:true})`) → Next.
- SuccessFactors: `/errorpage?errortype=Exception` on deep-links; a working careers host exists. Unknown password: Forgot password → reset URL (preserves `career_job_req_id`) → policy pw (8-18, upper+lower+digit+punct) → login → profile prefills + resume pre-attached. rcmpaginatedselect = mouse-open → option-click.
- Jobvite: consent select + Submit BEFORE the form; no "LinkedIn" source → "Web Search"; invisible reCAPTCHA may reset after Send.
- Workday: tenant = grep the careers page for `wd[0-9].myworkdayjobs.com`; UP-check = HTTP 200 on `/en-US/<site>/search`. Job Board source = CATEGORY chevron → expand → LinkedIn.com. Disclosures "Prefer not to answer". Global outages happen → probe first.
- BrassRing: canonical resume attached BEFORE Continue.
- Rippling: Apply disabled until consents committed (check `aria-checked`); map questions via `__NEXT_DATA__…activeJobApplication` by UUID.
- Always compare company/role/ATS-ID/domain before fill. Missing file input = blocker.

## LOGINS / OTP / ACCOUNTS
- Provider order: Google → LinkedIn → email/password → email OTP. Visible buttons only; never create duplicate accounts. Prefer "Sign in with LinkedIn" over unknown passwords.
- Google: passkey → Try another way → password → skip home-address. LinkedIn new page: Google/Apple + refs. Naukri: header Login closes modal → click the modal submit.
- OTP: request on the webpage FIRST → then fresh Gmail read → enter. Never search Gmail first / reuse a stale code. HTTP 429 → stop.
- Reset links are single-use; one reset/site/session; "You have already used this link" = loop → stop. Signup must be atomic: store the credential in the OS keychain/pw manager BEFORE entry → immediate sign-in → verify auth state.
- Escalated OTP / unknown sensitive fields → timebox. PAN/Aadhaar/unknown DOB → never guess.

## FINDING / DEDUPE
- LinkedIn a11y = 1 virtualized card → use the jobs-guest API; staffing cos re-tag jobs → verify the posting company.
- Before applying, check `config/progress.json`, `scratch/APPLIED.md`, LinkedIn Applied/Job Tracker, and Gmail. Match company + exact role + LinkedIn/ATS IDs + employer domain. Skip an already attempted/confirmed exact role even if reposted with a new ID.
- `web_search`/SearXNG finds portal-only roles: `<product> QA SDET <city> greenhouse/lever/icims`. Verify the board live via `boards-api.greenhouse.io/v1/boards/<slug>/jobs`; search URLs 404 fast.
- NEVER trust a recorded "blocked" — re-verify live. Try multiple domains/paths + the real apply button.
- `config/profile.json` absent → don't retry; use `user.json`/`answers.py`.

## SESSIONS / LOCKS
- MCP 400 "profile active (dead pid)" → remove `runtime/mcp-session/.cloakbrowser-mcp-profile.lock` + restart. One persistent-profile session at a time; sid `config/mcp_session.json` (stale → delete). Zombie Chromium → `lsof +D <profile>` + kill.

## SPEED
- Preflight 3 roles once; cache tuples; classify before opening any ATS. Read the selected recipe once/session.
- One scoped discovery → one sequential transaction → one targeted readback per stable state; condition waits, no stacked sleeps.
- Gmail per role one-by-one (combined search = explicit batch mode only). Batch tracker writes after proof gates. Parallelism only for independent read-only work.

## ATS-SPECIFIC QUICK NOTES
- Workday: full win via option-click commits; proof `/jobTasks/completed/application`. Two file inputs → `.first()` = resume. Years max may be "7+" or a checkbox group. Phone input `name≠phone` → aria-label.
- LinkedIn EA: unchecked radio GROUPS block Review → click every group's answer. Stuck Review = repeated click + consent.
- Phenom: no-popup upload via `setInputFiles`; proof `/applythankyou?status=success`.
- Workday high-trust proof pattern: "Congratulations! Thank you for applying…" + Gmail "Your job application with <company>" = the 2-source pattern.
- Google sign-in inside a cross-origin iframe → `frameLocator('iframe[title="Sign in with Google Button"]')`; close promo modals before card clicks.
- GH: the phone country selector ≠ the job-location Country question; read back the hidden phone-country value. Address block + LinkedIn + preferred name may be separate text questions; fill all.

## RELATED
- `skills/SKILL.md` (master) · `skills/apply/SKILL.md` · `skills/verify/SKILL.md` · `skills/REFERENCE.md`
- `skills/LESSONS/LESSONS-verify.md` · `skills/LESSONS/LESSONS-find.md`
