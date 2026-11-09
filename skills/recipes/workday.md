# WORKDAY RECIPE (proven — Fox R50033578 + JioStar)

## NEVER STALL FOR DOB (2026-11-05)
- DOB is **known**. Read it from `config/user.json` (`date_of_birth`, `date_of_birth_display_us`); authoritative identity note: **`skills/REFERENCE.md#identity`**. Do not restate the values in recipes — one source, no drift.
- Source of record is the RESUME, recovered by `find/resume_facts.py` (a derived cache; `user.json` wins every conflict).
- A Workday tenant must NEVER be skipped, parked, or handed back to the user for "missing DOB". Read `config/user.json`, fill the field, continue.
- Same for work history/education: the ATS parses the resume but mangles it (seen on HARMAN: First/Last = "Unknown", employer = "Meredith"). **Read the parsed rows back and correct them** from `config/resume_facts.json` / `skills/REFERENCE.md#identity` before continuing — never submit employer/name junk.

## ACCOUNT
- With user authorization, create/sign in using the approved email and an existing, user-provided, or securely retained credential. If no credential exists and an approved OS keychain/password manager is available, generate a strong unique password, store it there before entry, and retain it through immediate sign-in.
- **Never record passwords, reset links, or OTPs in `progress.json`, repository files, or gitignored files.** Account creation is not an application proof.
- Keep sign-up/reset → sign-in atomic; reset links are single-use and permit one recovery attempt per site/session. If no approved vault is available for a generated credential, use a user-provided credential or visible user entry; if the link is stale/consumed, record the exact blocker.
- Account SAVES progress → resume at `/apply` → "Apply Manually" → Sign In

## FIELD COMMIT (THE WIN — ~20 other methods fail)
```js
// browser_run_code_unsafe; keep discovery, action, and readback in one call.
const { page } = cloak;
const select = page.getByRole('button', { name: /Q/ });
await select.click();
const option = page.getByRole('option', { name: 'X', exact: true }).first();
await option.waitFor({ state: 'visible' });
await option.click();
return await select.innerText();
```
- Verify the selected label in the same call; use one short settle delay only if the option does not expose a waitable state.
- Strict-violation ("Male" ×2) → `exact: true` + `.first()`
- Search selectinput: same pattern (Job Board = CATEGORY → expand → LinkedIn.com)

## TEXTAREAS/TEXTBOXES
- REAL keys: focus → `browser_press_key` per char (native setter REJECTED)
- `browser_press_key` = the keyboard tool (browser_keyboard = phantom name)
- Application questions = textareas `name^=primaryQuestionnaire` (sort by y)
  q1 salary=3300000, q2 worked-previous=N/A

## SELECTS (phone device etc)
- open via JS click → trusted `browser_mouse` on the option (works for plain selects)

## CHECKBOXES / TERMS
- label click: `document.querySelector('label[for=ID]').click()` (proven)

## STEPS
- 5-step: My Information → Experience (resume) → Questions → Voluntary → Review
- Use one scoped discovery + one sequential action batch per step; read the step anchor once after transition.
- "step N of 5" nav; save via DOM click (refs churn)
- Voluntary: Gender = Male (getByRole option); "I DO NOT WISH" = also selectable
- Submit → capture `/jobTasks/completed/application` + exact "Application Submitted" text immediately; do not navigate away before recording proof.

## CTC
- Salary field = 3300000 (22% rule → <your current CTC> → <your expected annual INR>; see skills/REFERENCE.md#compensation)

## DEEP DIVE 2026-11-04 (IQVIA R1566251 · AVEVA R014589 · Light & Wonder R322807 · Scientific Games R505378)
### 1. TYPE + ENTER IS THE UNIVERSAL COMMIT
Every Workday picker (single-select, multiselect, degree grid, nationality, "reason for interest") commits on **type → Enter**. `.fill()` and DOM `.click()` on the option silently no-op.
```js
const b = page.locator('#<btnId>'); await b.focus();
await page.keyboard.press('ArrowDown');           // opens list
await page.keyboard.type('Bachelor', {delay:120}); // filters
await page.waitForTimeout(800);
await page.keyboard.press('Enter');                // COMMIT
```
Read back `getAttribute('aria-label')` / `innerText` of the `formField-*` wrapper to prove the commit **before** clicking Next.

### 2. SEARCH BOX ACCUMULATES TEXT
Typing twice into a multiselect search (`education-43--fieldOfStudy`) gives `ComputerComputer Sc` → clear first:
`Meta+A` → `Backspace` → type once → Enter.

### 3. VIRTUALIZED GRIDS (140+ options, no filter)
Degree / field-of-study lists render in **`ReactVirtualized__Grid`** (outer scroller, inner div has `scrollHeight === clientHeight`). Scrolling the inner div does nothing.
**Never hand-write `for (i<40) scrollTop += 600`** — a miss grinds the whole list (measured 4.87 s of continuous scrolling, 24 000 px). Use the bounded helper, which stops at the hit, at the end of the list, or at a 3 s budget:
```python
from core.ui import scroll_until
scroll_until("document.querySelector('.ReactVirtualized__Grid')"
             ".innerText.includes('Bachelor of Engineering')",
             container='.ReactVirtualized__Grid', max_ms=3000)
```
Fallback that always works: type the label + Enter (see §1).

### 4. DATES: type + Enter, never Tab
- `dateSectionMonth/Day/Year-input` are spinbuttons. Typing `1` may land `2` → settle with `ArrowDown`/`ArrowUp`.
- **Enter commits; Tab/blur often does not** (leaves "To* current value is … Error: required").
- If still red: `Meta+A` → retype → Enter, then confirm the `formField-endDate` wrapper error text is gone.

### 5. "How Did You Hear About Us" = nested multiselect
Submenu is truncated (11 rendered) and usually lacks LinkedIn. The **parent category is selectable via keyboard**: ArrowDown → type `Job Boards` → **Enter** commits `Job Boards/Websites`. Good enough, honest, and unblocks Next.

### 6. SIGN-UP / RESET (IQVIA-proven recovery)
- `Create Account` → POST `/register` → **303 → /login** = registration did NOT complete. Retrying silently loops; do not grind.
- Recovery that works: **Forgot your password?** → email → Gmail query `newer_than:2h (iqvia OR verify OR "candidate account")` → open reset link (`/passwordreset/<token>/?username=<urlencoded email>`) → set password (upper+lower+digit+special) → "Password has been reset" → sign in.
- Sign-in error "wrong email or password" = account truly absent → reset mail never arrives.
- Reset link is single-use.

### 7. VOLUNTARY DISCLOSURES BLOCK ON DOB
IQVIA step 5 requires `Date of Birth*` (`dateOfBirth-dateSectionMonth/Day/Year-input`) — **not in config**, must ask the user. Also Nationality = **India** (country list), Country of Birth = **India**; tick `termsAndConditions--acceptTermsAndAgreements` before Next.

### 8. KNOWN TENANT QUIRKS
- Autofill-with-resume frequently parses to **zero** fields (IQVIA, L&W) → expect manual fill.
- Autofill invents a junk row ("Test / Software Developer") and marks old jobs "current" → delete the junk row via `element.click()` on its Delete (mouse coords deleted the wrong row once), uncheck "currently work here".
- Education `Overall Result (GPA)` rejects `N/A`; needs a number (user-confirmed: **8**).
- Review page is the truth: read "I currently work here", From/To and education before Submit.
