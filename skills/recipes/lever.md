# LEVER RECIPE (proven — Netomi + Acceldata)

## FILL (via one `browser_run_code_unsafe` transaction)
```js
const { page } = cloak;
await page.evaluate(() => {
  const set = (name, v) => { /* input[name=...] native setter + input/change */ };
  set('name', A['full_name']); set('email', A['email']); set('phone', A['phone']);
  set('location', A['location']); set('org', /* current employer: config/user.json */ ...);
  set('urls[LinkedIn]', ...); set('urls[GitHub]', ...);
});
return await page.locator('input, textarea').evaluateAll(els => els.map(e => [e.name, e.value]));
```
- Questions = textareas/inputs "Type your response" — fill BY DOM ORDER (map labels first!)
- Native selects (years): `page.selectOption('select', { label: '8 years - 10 years' })`
- Radios (job mode/interview): `input[value=Hybrid].click()` etc

## RESUME
- `setInputFiles('#resume-upload-input')` — verify "Success!" chip

## CAPTCHA
→ `REFERENCE.md#standing-rule--captcha-handling`. Drag-pipe grid = user solves.

## PROOF
- URL `/thanks` = DONE (no captcha needed sometimes)
- DUP GATE: "already submitted / previous application" = NOT new → record + skip

## CTC
- Expected = <your expected annual INR>; Current = <your current CTC>; Notice = available from 28 Nov 2026, last working day 27 Nov 2026

## HIGHLEVEL (gohighlevel) — hCaptcha on submit (2026-11-05, 2 sessions)
- Form fills fine; `#btn-submit` shows but is wired to a hidden `#hcaptchaSubmitBtn`. Clicking surfaces an **hCaptcha image challenge**.
- See `REFERENCE.md#standing-rule--captcha-handling`. Fill once, submit once, report, move on. Never refill in a loop.
- Useful field facts if it ever opens: consent cards are `cards[<uuid>][fieldN]` (radio: authorised=Yes, sponsorship=No, OCI=No), comp is `cards[5fd76fff-d276-4961-8fa4-a09cd4df4a38][field0]`, notice is a radio group (`30 days or less`). Resume must show `input[name="resumeStorageId"]` non-empty — that's the real upload proof, not the filename.
- `input[name="location"]` gets mangled by concurrent typing; native-set the display string after the geo pick commits (`selectedLocation` JSON is what matters).
