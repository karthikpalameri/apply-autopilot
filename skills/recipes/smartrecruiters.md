# SMARTRECRUITERS RECIPE (proven — Tieto, 2026-11-05)

`jobs.smartrecruiters.com/<Co>/<id>` → **I'm interested** → `oneclick-ui` Angular app.

## THE SHAPE
- Fields are **custom elements**: `<spl-input>`, `<spl-autocomplete>`, `<spl-phone-field>`, `<spl-button>`.
- `page.locator('#first-name-input').fill()` → **"Element is not an `<input>`"**. The host is not the input.
- Host `.value` can be an **object** (`{text, city, country, postalCode}`). That object is the real state.

## HANDLES THAT WORK
- Text: `page.locator('#first-name-input input')` → `fill()`.
- Comboboxes: `page.getByRole('combobox').nth(n)` in **DOM order** (0=hear-about-us, 1=tools, 2=years, 3=notice, 4=gender).
- Buttons: `page.locator('spl-button:has-text("Next") button')` — clicking the host alone does nothing.
- File input lives in a **shadow root**; `input[type=file]` in the light DOM is only the avatar:
```js
const h = await page.evaluateHandle(() => {
  function find(r, d){ if(!r || d>8) return null;
    const f = r.querySelector && r.querySelector('input[type=file]');
    if (f && /pdf/i.test(f.accept||'')) return f;
    for (const el of (r.querySelectorAll ? r.querySelectorAll('*') : []))
      if (el.shadowRoot) { const x = find(el.shadowRoot, d+1); if (x) return x; }
    return null; }
  return find(document, 0);
});
await h.asElement().setInputFiles('config/Your_Name_Resume.pdf');
```

## AUTOCOMPLETES OPEN ONLY ON REAL MOUSE EVENTS
If the menu renders but `.select__option` / `[role=option]` returns 0 → use a local viewport crop + OCR per `skills/REFERENCE.md#screenshot-budget-measured-2026-11-07--the-single-biggest-token-sink`, then `browser_mouse_click_xy` on the verified option row. Stop re-querying.

## TWO-STEP WIZARD — THE TRAP
- Step 2 (**screening**) has ~6 **required** questions that are **off-screen**: how did you hear / tools / current job title / years of experience / notice period / gender.
- **`Back` wipes City, Phone and Resume from step 1.** Never go back to "verify" — read back all required step-1 values before Next. If you do go back, re-enter resume + city + phone, then Next.
- Consent checkbox must be checked or **Submit no-ops with zero errors**.
- `#spl-form-element_N` ids are positional and renumber per employer — never hardcode.

## PROOF
`/success` + **"Application submitted!"**. Read the resume filename row from the DOM; if visual-only, use local cropped OCR (never attach the image to model context).
