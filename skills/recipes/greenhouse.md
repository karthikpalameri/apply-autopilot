# GREENHOUSE RECIPE (proven)

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
- Click EXACT option ("Bengaluru, Karnataka, India") and read the selected value back in the same call.

## PROOF
- "Thank you for applying. Your application has been received."
- Sign in to MyGreenhouse = extra confirmation

## CTC
- 22% rule (<expected CTC>)
