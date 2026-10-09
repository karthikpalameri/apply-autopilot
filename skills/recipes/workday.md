# WORKDAY RECIPE (proven — Fox R50033578 + AcmeWorkday)

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
  q1 salary=<expected CTC numeric>, q2 worked-previous=N/A

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
- Salary field = <expected CTC numeric> (22% rule → <current CTC> → <expected CTC>; see skills/REFERENCE.md#compensation)
