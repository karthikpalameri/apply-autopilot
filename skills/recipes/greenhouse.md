# GREENHOUSE RECIPE (proven — AKKO ×2 + Netskope + JioStar-adjacent)

## FILL
- Basics by name/id: `input[name=first_name]`, `last_name`, `email`, `phone`, `urls[LinkedIn]`
- Resume: `setInputFiles('#resume_upload_input' / input[type=file])` (invisible input ok)
- Country react-select: `#country` → click → pressSequentially("India") → option **"India +91"** (not "India")

## REACT-SELECTS (THE WIN)
```js
// browser_run_code_unsafe; use the server-global cloak object.
const { page } = cloak;
const ci = page.locator('#' + id);          // country, question_XXXX
await ci.click();
await ci.pressSequentially(text, {delay: 40});   // real keys render options
const option = page.getByRole('option', { name: pat }).first();
await option.waitFor({ state: 'visible' });
await option.click();
return await ci.inputValue();
```
- Bucket options: 1-2 / 3-4 / 5+ (not exact numbers)
- Missed-select class: "Are you based in the US?" + "Monday-Sunday schedule" = Yes/No selects — find via error-driven submit

## NESTED IFRAME (embed)
- `browser_evaluate` target=<embed-ref> drills the inner frame (name ROTATES)
- ONE form-open (never re-open); one-call discovery + fill/readback. Submit only after the final pre-check.
- react-select options render ONLY on real per-char keydowns; wait for the exact option to become visible instead of sleeping 2–3s.
- Click EXACT option ("<your city, country>") and read the selected value back in the same call.

## COUNTRY = PHONE DIAL-CODE, not a country field (2026-11-06, blocked 2 submits)
`#country` is **intl-tel-input's hidden input**; the visible control is `.iti__selected-country`. The flag
can read "India" while `#country` is `""` — Greenhouse validates `#country`, so submit fails with
`Select a country` under **Phone Country\***. Synthetic `.click()` on the option does not sync it.
```js
// set the submitted value directly, then fire the events GH listens for
const c = document.getElementById('country');
Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(c, 'in');
['input','change','blur'].forEach(t => c.dispatchEvent(new Event(t,{bubbles:true})));
// verify: document.getElementById('country').value === 'in'
```
- **`.helper-text--error` is unreliable.** A stale `Select a country` banner persists after the value is
  correct (`aria-invalid="false"`, submit enabled). **Submit anyway and read the server result** — it is cosmetic.
- Escaping to close the phone dropdown **cancels** the selection — reopen and pick India again.

## EMAIL SECURITY CODE (`#security-input-0..7`)

**TRIAGE FIRST — dead submit is USUALLY this, not a CAPTCHA (2026-11-06, wasted ~20 calls on Rubrik).**

```js
// ONE call decides disabled-vs-captcha. Run it before touching any captcha.
({ btnDisabled: (document.querySelector('button[type=submit]')||{}).disabled,
   codeBoxes: document.querySelectorAll('[id^="security-input-"]').length })
```
- `codeBoxes > 0` **or** `btnDisabled === true` ⇒ **email-code gate. STOP. Read Gmail.** Do not solve a
  CAPTCHA, do not click the widget, do not run `grecaptcha.enterprise.execute`.
- The disabled button is why clicks look like a no-op: **no POST fires at all**, so `waitForResponse`
  returns null and the console stays clean. That silence *looks* exactly like a failed CAPTCHA token — it isn't.
- A visible `recaptcha/enterprise/anchor` iframe with `ar=1` is a **badge**, not a challenge. The badge is
  always present on these boards and means nothing. Do not treat its presence as a CAPTCHA blocker.

- Appears only **after** a submit. 8 alnum chars. Read from the **Gmail browser tab** first
  (→ `REFERENCE.md#credential-vault--macos-keychain-only`; IMAP is the fallback and usually unavailable).
  Sender is `Greenhouse`, subject `Security code for your application to <Company> Job Board`; the body
  reads "Copy and paste this code into the security code field". `document.body.innerText` of the search
  tab surfaces it in one read — no need to open the message.
- **Single-use + short-lived, and re-sent unchanged** while the form sits unsubmitted → re-reading gives the
  same dead code (`Invalid security code`). Fix: `page.reload()` (clears code+banner) → refill → submit →
  the *new* code arrives. Observed: `88851365` dead → `80240858` live.
- Fill per box: `locator('[id^="security-input"]').all()` then `.fill(code[i])` per box.
- **Post-check is mandatory and is the real green light:** `btnDisabled === false` after entry. Rubrik:
  button flipped to enabled → click → POST `200` → `/confirmation` → "Thank you for applying."

## TWO SUBMIT BUTTONS — "Apply" is a decoy (2026-11-06, Rubrik)
`button:has-text("Apply")` matches the **job-description** button at the top (`type=button`, no-op). Clicking
it scrolls/expands and looks like a failed submit. The real control is:
```js
page.locator('button[type=submit]:has-text("Submit application"), input[type=submit]').first()
```
- Always assert `type === 'submit'` and `disabled === false` before clicking.
- Order: fill → `btnDisabled` check → email code if needed → click the `type=submit` button.

## PROOF
- "Thank you for applying. Your application has been received."
- Sign in to MyGreenhouse = extra confirmation

## CTC
- 22% rule (<your expected annual INR>)

## ATTACH BUTTON (modern GH — 2026-11-04)
- Newer Greenhouse forms have **NO `#resume` file input**. The old `setInputFiles('#resume')` silently no-ops and you submit with no resume (this happened on Point72 and caused a failed Lever submit earlier too).
- Correct flow — **never click Attach** (that opens the native macOS/Windows picker this harness cannot dismiss). Attach merely forwards to a hidden `input[type=file]`; reach that input directly. Upload procedure + fallback: **`skills/resume/SKILL.md#upload-method`** (single source).
- If no `input[type=file]` is reachable in light DOM or shadow root, the last resort is a *programmatic* chooser grab — `waitForEvent('filechooser')` fired by the button click, then `chooser.setFiles(path)`. The chooser object is Playwright-side, so no OS window survives, but the click itself may still flash one. Prefer injection.
- VERIFY after upload by asserting the filename text appears in `document.body.innerText` — `input[type=file]` may stay empty because GH stores the upload server-side.
- Education `#school--0` is a **typeahead against a fixed school DB**; "BMS College of Engineering" returns no options. Field is optional (no asterisk) — leave blank rather than typing free text that never commits.
- Phone uses intl-tel-input: after choosing country `India +91`, clear fully (Backspace loop + native setter) then `keyboard.type(...)` with the **national** digits from `config/user.json` (`phone_national`) — never hardcode them here. A naive fill yields `063628 57710` or `00 63 62 857 710`.

## REQUIRED-BUT-HIDDEN FIELDS (2026-11-05, hit on 5/5 boards)
`?questions=true` does NOT list these. They appear at submit and block it:
- `#country` → react-select, pick **"India +91"**
- `#candidate-location` → async geo typeahead: `type('Bengaluru')` → wait ~2s → click option. `fill()` sets nothing.
- `#degree--0` → react-select, **"Bachelor's Degree"** (Contentstack needs it; Five9 also needs `#school--0`)
- Order of operations: API questions → resume → country/location/education → submit.

### Embed iframe (`job-boards.greenhouse.io/embed/job_app?for=<token>`)
```js
const f = page.frameLocator('iframe[src*="greenhouse.io/embed/job_app"]');
await f.locator('#question_XXX').fill(v);   // ALL locators go through f
```
- Required questions can hide **above the fold** — enumerate all required controls and validation flags in the form DOM before deciding it is complete; for visual ambiguity follow `skills/REFERENCE.md#screenshot-budget-measured-2026-11-07--the-single-biggest-token-sink` (local cropped OCR, never a full-page image).
- **CORRECTED 2026-11-06.** "Valid + zero errors + submit no-op + no navigation" is **NOT** proof of a
  CAPTCHA. Run the disabled/code-box triage above **first** — on Rubrik it was a `disabled` submit held by
  an 8-char email code, and treating it as a CAPTCHA burned ~20 calls. Only after `btnDisabled === false`,
  `codeBoxes === 0`, a real challenge frame, and a still-silent submit may you conclude CAPTCHA, then stand
  down per `REFERENCE.md#standing-rule--captcha-handling` (Securly did exactly this).

### React-select commit ladder (stop at the first that works)
1. click control → `page.locator('.select__option').filter({hasText:/^Exact/}).first().click({force:true})`
2. menu open but `.select__option` count is 0 → the query is unscoped; screenshot and use `browser_mouse_click_xy` on the row
3. never `ArrowDown`-count to an index — it lands **one option off** and silently records the wrong answer (cost me ₹55–65 LPA instead of ₹40–55 LPA). Always read the committed label back and assert it.

## PROVEN AGAINST A LIVE BOARD (2026-11-05 — Airbnb `8349121`, Securly `securly13/8331968`)

**Resume upload.** `browser_file_upload` **fails** here (5 s chooser timeout; the input is `visually-hidden`
behind `.file-upload__wrapper`). Use, in `browser_run_code_unsafe`:
```js
await page.locator('input[type=file]').first()
          .setInputFiles('config/Your_Name_Resume.pdf');
```
**Success looks like failure:** after upload GH removes `#resume` and renders a preview chip. So
`!!document.getElementById('resume')` → `false` means **done**. Verify by reading
`.file-upload__wrapper` / body text for the filename. Do not re-upload (it just adds another chip).

**Custom questions wipe state.** Answering a `question_*` re-renders the form: free-text fields you
filled earlier (`#question_*70`, CTC) come back empty. Re-read **every required field** right before submit.

**reCAPTCHA Enterprise is a hard stop.** Securly uses `iframe[src*=recaptcha/enterprise/anchor]`,
sitekey in the `k=` query param. No CAPTCHA-solving API here: finish safe fields, leave the page
for the user, record `waiting-user-captcha` (single source: **`REFERENCE.md#captcha--no-solving-no-api-key-standing-rule`**).

**Board token ≠ company name.** `for=securly` 404s; the real token was `for=securly13` (read it off the
`grnhse_iframe` src on the company careers page).

## Job-boards (2026-11-06) — `#edit-*` ids, 3 react-selects, one typeable select

Measured on StockX `job-boards.greenhouse.io/<slug>/jobs/<id>`: filled + submitted with 8 calls once the
shapes below were known. Full play-by-play: `skills/LESSONS.md` → **2026-11-06 S6** §5-§7.

| Field | Real control | Commit recipe |
|---|---|---|
| First/Last/Email/Phone/CTC/ECTC/Notice | plain `input` | `.fill()` — works first time |
| Country | react-select, `input=select__input` `value=""` | click **`.select__control` ancestor** → `keyboard.type('India')` → option **`India +91`** |
| Location (City) | same react-select | click control → type `Bengaluru` → option `<your city, country>` |
| *"How long before you can start"* | **`input[role=combobox]`** (typeable select) | `.fill()` is silently IGNORED → click → options → click `16-30 days` |
| Resume | `input[type=file]` (hidden behind a dropzone) | `setInputFiles` on the input; `browser_file_upload` times out |

- Ids: `#first_name #last_name #email #country #phone #candidate-location #question_<long>`. On the
  embed variant they are `#edit-<same>`, and **they only exist while the DOM is warm** — re-read the id in
  the same call that fills it, or the locator times out after a blur re-render.
- **The form renders no validation until Submit.** Submit once, read `[class*=error]`/`[aria-invalid]`,
  fix, submit again. Do not hunt for errors first.
- React-select country/location keep `input.value=""` after a valid commit — read back the
  `.select__control` `innerText` instead.
- Confirmation = URL `/jobs/<id>/confirmation` + "Your application has been received." `POST` alone is
  noisy here (uploads are also POSTs).
