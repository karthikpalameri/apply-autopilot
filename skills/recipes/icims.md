# iCIMS RECIPE (symplr, Docusign — hCaptcha-gated)

## FLOW
1. Email step (`#email` name=css_loginName) → Next → hCaptcha blocks (→ `REFERENCE.md#standing-rule--captcha-handling`)
2. Candidate Profile form (icims_content_iframe):
   - Login/email, First/Last, Phone, DOJ (Aug/15/2026), Address, City, Zip
   - Password 13ch MATCH (typing doubles — always clear+retype, verify lengths)
   - Type=Mobile, Country=India, State=Karnataka, how-heard
3. Resume step → "My computer" → upload → resume.pdf chip
4. Submit Profile → proof?

## AJAX DROPDOWNS — the `/jobs/profileoptions` endpoint (2026-11-06, cost 272 calls)
Every `<select>` with `icimsdropdown-ajax=1` renders **exactly one option** (`— Make a Selection —`) and the
widget never fires its XHR. `initializeAllIcimsDropdowns()` runs and does nothing. **The server is fine** —
call it yourself. Do not click, do not press keys, do not pixel-hunt.

**THE UNLOCK — `id` must be the BASE field name, not the DOM id:**

| `id` param | Result |
|---|---|
| `-2820602_PersonProfileFields.rcf3218` (real DOM id) | `""` → **200 OK with empty body** (silent!) |
| `PersonProfileFields.rcf3218` (base name) | `{"total":2,"options":[…]}` ✅ |

The `-2820602_` row prefix **regenerates on every render**, which is also why any handle you held goes stale.

```js
// harvest, then inject + commit. Works for every ajax dropdown on the form.
const s = document.querySelector('select[id$="PersonProfileFields.rcf3218"]');
const hash = s.getAttribute('hash');                       // per-select, required
const base = 'PersonProfileFields.rcf3218';                // strip /^-\d+_/
const j = await (await fetch(
  `https://<tenant>.icims.com/jobs/profileoptions?in_iframe=1&` +
  new URLSearchParams({ q:'India', page:'0', size:'50', parentValue:'', id:base, hash }),
  { credentials:'include', headers:{ Accept:'application/json' } })).json();
const el = document.createElement('option');
el.value = j.options.find(o => o.text === 'India').value; el.textContent = 'India';
s.appendChild(el);
s.setAttribute('icimsdropdown-enabled','0');               // disable the dead widget
s.value = el.value; s.dispatchEvent(new Event('change',{bubbles:true}));
```

- Dependent selects need `parentValue` (State after Country: `parentValue=13228` for India).
- **Hit the API, not the DOM, for option *content*.** The page rendered 3 source options; the API had 5,
  including the truthful `LinkedIn (Ad Posting)`.
- Real values seen: India `13228`, Karnataka `13245`, prior-Docusign `No` `28874`, sponsorship `No` `29267`.
- Work-experience rows are `-<rowid>_PersonProfileFields.rcf3212` (employer) `.rcf3213` (title)
  `.rcf3216` (city) `.rcf3218` (country) `.rcf3217` (state) — loop `[id$="_PersonProfileFields.rcfXXXX"]`.

## SELECTOR TRAP — `#-1_PersonProfileFields.PhoneNumber` is an INVALID CSS selector
It throws `SyntaxError: not a valid selector` (cost 4 calls). Use `document.getElementById('...')`,
`[id="..."]` attribute form, or `locator('input[id="..."]')`. Same for numeric ids (`#61945`).

## KEY LESSONS
- **Verify EVERY field before submit** (read values, not the a11y label)
- Password doubling: 26ch vs 13ch mismatch = silent required-error
- DOJ year must be 2026 (typing shifts)
- **Résumé parser re-runs on submit and re-sorts the work-experience rows**, clearing phone/phoneType and the
  re-created rows' country. Re-read every required value immediately before the final submit, in the same pass.
- Captcha: see standing rule. Never report past an unsolved one. **Park the filled tab** (→ `RELIABILITY.md#stop-rules`).
