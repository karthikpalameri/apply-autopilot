# AVATURE RECIPE (proven — IBM PowerVC test engineer, 2026-11-05)

## LOGIN — GOOGLE OAUTH BEATS IBMid PASSWORD
- `careers.ibm.com` → Apply now → `login.ibm.com` IBMid wall.
- Prefer **Continue with Google** (recipe order in REFERENCE.md). It signs in with the existing Gmail, no new password, no email loop.
- The button is an `<a>`; if `getByRole('button')` misses it, click by `getBoundingClientRect` centre.
- Google chooser → pick the account → consent screen → **Continue**. Lands back on the job with the application open.

## APPLICATION LAYOUT (single scrolling page, % progress)
- 25% resume → 50% personal → 75% additional → 99% review → Submit Application.
- Resume step: **From Device** then `page.locator('input[type=file]').setInputFiles(path)`. A repeat file input appears at 99% (`#21273`) — set it again or Submit blocks.

## SELECT2 WIDGETS (same pattern as HARMAN)
- `#ui-widget_<id>` wrapper; the real control is `.select2Container<id>`.
- click container → `input.select2-search__field` → pressSequentially → wait 2–3 s for `Searching…` to clear → click option by id.
- Country / Type of degree / "How did you hear" / "Is current position?" / past-experience are all this widget.
- "How did you hear": there is **no LinkedIn** option — use **Job Board**.

## GOTCHAS THAT COST A ROUND TRIP
- Preferred-name Yes/No (`9002_*`) is required but sits inline with other radios — miss it and Continue bounces.
- "Have you ever worked at IBM before?" (`10531_*`) required, easy to miss.
- Disability question (`11936_*`) is OPTIONAL — do not answer Yes by accident; use **Do not wish to declare** unless the user said otherwise.
- Aadhaar name (`10900`/`10901`) must be the legal name.
- DOB here is **day + month + year** separate fields — read the parts from `config/user.json` (`date_of_birth` is ISO, so split it). Never hardcode the numbers in a recipe: **`skills/REFERENCE.md#identity`** is the one source.
- Work history rows come from the resume but drop the current employer — re-add the current employer as "Is current position? = Yes" (value from `skills/REFERENCE.md#identity`).
- Errors surface only as "There are some errors… Show details" at the top — always click **Show details** and read every line.

## ACCOUNT WALL IS OFTEN FAKE — guest apply via `requestSubmit` (proven BMC 2026-11-08)

`jobs.bmc.com/Careers/ApplicationMethods?jobId=N` renders a login panel that looks mandatory
(Username/Password + "Forgot your password?", no "create account" link). It is **not**. The page
says "First time here?" and offers Copy&Paste / Upload CV / LinkedIn / Indeed / **Without Resume**.

What actually blocks progress:
1. `#resumeFile` is `display:none` and its containing file fieldset
   (`#methodButton--fileFieldSetContainer`) is `visibility`-hidden. `setInputFiles` alone leaves the
   name in `#fileNameContainer` but Continue still errors "This field is required". Reveal the
   fieldset (`display:block; visibility:visible; height:auto`) first.
2. `#uploadFileResume` is `type="submit"` inside `#manualRegisterMethodsForm`. **`.click()` does
   nothing** — no navigation, no error. Call **`form.requestSubmit(btn)`** and it advances to
   `/Careers/Register`. Same class of bug as the SAP attachment `+` icon: the DOM has the mechanism,
   the synthetic click is not it.
3. `/Careers/Register` is the real form (46 fields). Same `requestSubmit` for `#16656-next`.

**Unstarred fields that server-requires anyway.** `22678` ("If hired, would you be working under a
visa/work permit?") has **no `*`** and no client validation, but the POST rejects with
"This field is required". It is a **select2** with 1 empty option — open the container, mouseup the
"No" option. Always re-submit after filling an unstarred gap; never trust the absence of `*`.

Other traps: Source → `Job Board` then Source Details → **`LinkedIn Job Posting`**; PAN is required
(`#16631`); State options populate only after Country commits (re-read, don't cache); final step is
the voluntary EEO (Gender + "break in career") with `#16688-goto` Submit.
