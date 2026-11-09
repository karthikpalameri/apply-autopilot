# NAUKRI RECIPE (proven 2026-11-04 — Bounteous submitted)

Naukri has **no dedicated apply script**; apply is driven live in the MCP browser.
This recipe encodes four traps that each cost a failed attempt.

## 🔴 THE FOUR TRAPS (each observed directly)

### 1. `saveApply` HTTP 200 is NOT proof of submission
Three different outcomes all return **HTTP 200** with title `"Apply Confirmation"`:

| Body text | Meaning |
|---|---|
| `Applied to "<title>"` | ✅ **submitted** |
| `Oops! Your application was not accepted due to incomplete information…` | ❌ **rejected** (mandatory questions) |
| `You were redirected to the company website…` (`multiApplyResp: 202`) | ❌ **not submitted** — external ATS |

**ALWAYS read the body text.** Never infer from HTTP status, page title, or URL.

### 2. The chatbot overlay intercepts clicks
```text
<div id="_kpq…" class="chatbot_Overlay show">  ← intercepts pointer events
<div class="_chatBotContainer" id="_kpq…ChatbotContainer">
```
Symptom: `locator.click: Timeout 30000ms exceeded … subtree intercepts pointer events`.
Remove before clicking:
```js
await page.evaluate(() => {
  document.querySelectorAll('._chatBotContainer,[class*=chatbot],[class*=Overlay]').forEach(e => e.remove());
});
```

### 3. TWO elements share `id="apply-button"`
`querySelector('#apply-button')` grabs the **hidden duplicate** → silent no-op, no network call.
Click the **visible** one (or the last in DOM order):
```js
const all = [...document.querySelectorAll('#apply-button')];
const vis = all.filter(b => b.offsetParent !== null);
(vis[0] || all[all.length - 1]).click();
```

### 4. Mandatory questionnaire may gate the apply
If the body says "not accepted due to incomplete information", the listing has a
questionnaire. Re-open and answer **only** from `config/answers.py` /
`skills/REFERENCE.md`. Never invent salary, notice, or consent answers.

## FULL APPLY TRANSACTION

```js
const { page } = cloak;
await page.waitForTimeout(4000);

// guard: already applied?
const pre = await page.evaluate(() => document.body.innerText.replace(/\s+/g,' '));
if (/already applied/i.test(pre)) return 'DUPLICATE';

// 1. clear overlays
await page.evaluate(() => {
  document.querySelectorAll('._chatBotContainer,[class*=chatbot],[class*=Overlay]').forEach(e => e.remove());
});

// 2. click the VISIBLE apply button + capture the network response
const resp = page.waitForResponse(r => /saveApply|showAcp|myapply/i.test(r.url()), { timeout: 18000 }).catch(() => null);
await page.evaluate(() => {
  const all = [...document.querySelectorAll('#apply-button')];
  const vis = all.filter(b => b.offsetParent !== null);
  (vis[0] || all[all.length - 1]).click();
});
const r = await resp;
await page.waitForTimeout(4500);

// 3. read the BODY TEXT — the only real proof
const body = await page.evaluate(() => document.body.innerText.replace(/\s+/g,' '));
return JSON.stringify({
  http: r ? r.status() : null,
  url: location.href.slice(0, 140),
  submitted: /Applied to "/.test(body),
  rejected:  /not accepted due to incomplete/i.test(body),
  redirect:  /redirected to the company website/i.test(body),
  head: body.slice(0, 220)
});
```

## CLASSIFY → RECORD (always)

| Signal | Ledger status |
|---|---|
| `Applied to "…"` | `submitted-confirmed` |
| `not accepted due to incomplete` | `blocked-mandatory-questions` |
| `redirected to the company website` | `blocked-external-redirect` (resolve the real ATS first) |
| No network call at all | `blocked-apply-button-unresponsive` |
| `already applied` | `DUPLICATE` — do not proceed |

## TARGETING — filter out service companies

Naukri's SDET shelf is dominated by outsourcing firms that fail the employer gate.
Exclude by name **before** queueing:

```text
capgemini itc-infotech tanisha quess cgi epam virtusa infosys tcs wipro accenture
cognizant hcl tech-mahindra mphasis ltimindtree persistent birlasoft hexaware
coforge zensar sonata artizent randstad manpower teksystems kezan infosys
altimetrik luxoft ascendion iqvia trigent wintech anlage squircle
```
Keep: product companies and genuine GCCs only.

## CARD EXTRACTION (one DOM pass, then scroll)

```js
const cards = [...document.querySelectorAll('[data-job-id]')];
cards.map(c => ({
  id: c.getAttribute('data-job-id'),
  txt: c.innerText.replace(/\s+/g,' ').slice(0,130),
  exp: (c.innerText.match(/(\d+)-(\d+)\s*Yrs/) || [])[0]
}))
```
Scroll lazily with the bounded helper instead of a fixed wheel count — `core.ui.scroll_until("document.querySelectorAll('[data-job-id]').length >= 20")`. A fixed `mouse.wheel ×5` + 1.4 s each costs **7.03 s measured** and keeps scrolling after the cards are already loaded. See **`skills/RELIABILITY.md#bounded-scrolling`**.
Job URL pattern: `https://www.naukri.com/job-listings-<slug>-<jobId>`.

## PRE-APPLY GATE (mandatory, in order)
1. `find/ledger_guard.py` must pass
2. `core.applied_ledger.is_applied(company, role)` → False
3. **Gmail search for the company name** — the ledger does NOT know about
   Talent500 / Naukri / direct-email applications. YipitData was applied **and
   rejected twice** yet looked ledger-clean.
4. Listing still live (card present, Apply button visible)

## CTC
- Expected `3300000` (₹33L) — user approved applying below target; still enter 33L.
- Current fixed `2700000`, variable `0`.
- Notice: date form = `available from 28 Nov 2026; last working day 27 Nov 2026`;
  numeric days = **23** (computed, never the stale stored 32).

## ONE-CLICK APPLY (verified 2026-11-05, LPL Financials)
- `#apply-button` exists **twice** in the DOM → `browser_click` with `#apply-button >> nth=0`.
- One click is enough; it redirects to
  `/myapply/saveApply?strJobsarr=[<jobId>]&...&multiApplyResp={"<jobId>":200}`
  and the body shows **`Applied to "<role>"`**.
- **That URL is the proof** — record it verbatim with `job_id=naukri-<jobId>`, status `submitted-confirmed`. No second tab, no questionnaire, no Gmail wait needed.
