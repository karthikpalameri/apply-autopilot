# LEVER RECIPE (proven)

## FILL (via one `browser_run_code_unsafe` transaction)
```js
const { page } = cloak;
await page.evaluate(() => {
  const set = (name, v) => { /* input[name=...] native setter + input/change */ };
  set('name', 'Jane Doe'); set('email', ...); set('phone', ...);
  set('location', 'Bengaluru'); set('org', '<current employer>');
  set('urls[LinkedIn]', ...); set('urls[GitHub]', ...);
});
return await page.locator('input, textarea').evaluateAll(els => els.map(e => [e.name, e.value]));
```
- Questions = textareas/inputs "Type your response" — fill BY DOM ORDER (map labels first!)
- Native selects (years): `page.selectOption('select', { label: '<years> years' })`
- Radios (job mode/interview): `input[value=Hybrid].click()` etc

## RESUME
- `setInputFiles('#resume-upload-input')` — verify "Success!" chip

## CAPTCHA
- "Drag the correct pipe to complete the path" = USER solves (drag) → submit

## PROOF
- URL `/thanks` = DONE (no captcha needed sometimes)
- DUP GATE: "already submitted / previous application" = NOT new → record + skip

## CTC
- Expected = <expected CTC>; Current = <current CTC>; Notice = serving, last working day <your last working day>
