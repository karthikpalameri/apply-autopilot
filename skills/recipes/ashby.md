# Ashby — `jobs.ashbyhq.com/<slug>/<uuid>`

Measured 2026-11-06 on CertifyOS `SDET` (Bengaluru): one confirmed submit after four false rejections.
Full play-by-play: `skills/LESSONS.md` → **2026-11-06 S6** §1-§4, §10-§11.

## THE TAB LIES AFTER A SUCCESSFUL SUBMIT

`POST /api/non-user-graphql?op=ApiSubmitSingleApplicationFormAction` returns
`{"applicationFormResult":{"__typename":"FormSubmitSuccess"}}` and the SPA swaps the form for
**"Your application was successfully submitted."** — **the URL never changes.**

- **Never reload `/application` after submitting.** The re-mounted tab renders a **blank form**, which then
  proudly shows `Missing entry for required field: Location`. That is a fresh form, not a rejection.
  Revisiting it cost two "is it submitted?" detours in one session.
- Real proof, in this order: POST body `FormSubmitSuccess` → Success panel text → confirmation email.

## FIELD SHAPES (all verified against the live form)

| Shape | What it actually is | How to commit |
|---|---|---|
| Name / Email / Phone / LinkedIn / notice / CTC / "anything else" | normal inputs, UUID `id`s | `.fill()` + read `.inputValue()` back |
| *Are you comfortable with hybrid…*, *Are you legally authorized…* | **yes/no `<button data-option="yes">`**, NOT radios | `page.locator('[data-option="yes"]').click()` → verify `aria-pressed="true"` |
| Years of experience / AI usage / languages | **radio groups** | click through the fieldset that owns the question: `page.locator('fieldset').filter({hasText:'<question substring>'}).getByText('Yes',{exact:true}).click()` |
| Location | text input + combobox, id **`_systemfield_location`** | click → type `<your city, country>` → click the exact option |
| Resume + Cover letter | **two** `input[type=file]` (index 0 and 1) | `setInputFiles` on **both**; `browser_file_upload` times out |

### Two traps that cost the most calls
1. **`getByLabel('Yes')` is ambiguous.** It matches the first Yes on the page (hybrid), so the *"legally
   authorized"* Yes was never set and the server kept returning
   `Missing entry for required field: Are you legally authorized…`. Worse, `.check()` returned `true` while
   the group still read unchecked. **Verify by reading the radio's `checked` inside its own fieldset.**
2. **UUID ids cannot go in a CSS selector.** `#6320f419-5206-…` throws
   `not a valid selector`. Use `[for="_systemfield_location"]` + `xpath=following::input[1]`, or
   `getElementById` inside `page.evaluate`.

## "Autofill from resume" FILLS NOTHING

Upload → wait ~9 s → banner *"Autofill completed! Please review the information we filled in for you below."*
→ **every field still empty** (measured twice, two independent form instances). Budget a full manual fill;
treat the banner as decoration. The upload only takes via `setInputFiles`.

## LIVENESS + BACKFILL: the posting API (no browser)

```bash
.venv/bin/python -c "from core.fetch import get_json; print(get_json('https://api.ashbyhq.com/posting-api/job-board/<slug>'))"
```
Returns every posting with `id`, `title`, `location`, `employmentType`, `isListed` — one call proves
requisition liveness (`isListed: true`) and lists sibling India roles for the next round.
**It is CORS-blocked from page context** (`TypeError: Failed to fetch`) — call it from Python only.
`find/preflight.py --resolve N` already does this for the top N candidates.

## SUBMIT CHECKLIST

1. Fill by id; read every value back.
2. Radio groups: click through the fieldset; re-verify `checked` **after** any later interaction (fixing a
   rejected field can silently un-check an earlier group).
3. Both file inputs populated.
4. Submit → inspect the POST body. `errorMessages` present = fix and resubmit; `FormSubmitSuccess` = done.
5. Record with the **email's** title (`SDET - II`) and keep the page title (`SDET`) in `proof`.
