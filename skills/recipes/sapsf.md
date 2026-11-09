---
name: sapsf
description: SAP SuccessFactors career portal (career<N>.sapsf.com/portalcareer) — juic/rcm widgets. Resume upload needs the "+" icon, not the label.
parent: skills/apply/SKILL.md
version: 1.0.0
proven: 2026-11-08 (Teradyne / Universal Robots req 11718 — submitted)
---

# SAP SuccessFactors (`*.sapsf.com/portalcareer`)

Guest apply, no account wall (an account is created on first Apply).

## DETECT

URL contains `sapsf.com` + `portalcareer`. DOM uses `juic` + `rcm*` classes
(`rcmSaveButton`, `rcmpaginatedselectinput`, `attachmentBtn`).

## RESUME UPLOAD — the one that blocks everything

The visible text "Upload a Resume" (`div#51:_attachLabel`) **has no click
handler**. Clicking it does nothing and no `input[type=file]` ever appears —
this is what causes the "inert upload widget / 0 file inputs" park.

The real trigger is the **`+` icon** in the same container:

```js
document.getElementById('51:_attachIcon')   // class "addAttachments"
// onclick="juic.fire('51:','action',event)"  <-- 'action', not 'click'
```

Sequence:

1. `scrollIntoView` the attach container (`#51:_attach` sits far above the
   fold, often y ≈ -900).
2. Click `span#51:_attachIcon` (use `[id="51:_attachIcon"]` — the `:` in ids
   breaks CSS selectors; never use `page.locator('#51\\:...')`).
3. Immediately after, `input#52:_file` (name `fileData1`) exists →
   `setInputFiles(BEFORE_UPLOAD())`.
4. **Post-check:** `document.body.innerText` must contain
   `Download document <your filename>` + `Last Modified: <date>`.
   `#51:_attachSuccess` going `inline-block` alone is not enough.

Ids are `51:` resume / `53:` cover letter / `55:` additional docs; the icon is
`<id>:_attachIcon`.

## PICKLISTS (`input.rcmpaginatedselectinput`)

Not native selects. Click input → type the exact option text → click the
matching `[role=option], li[class*=option]`. Verify `el.value` after each.

Options are **paginated** — type to filter, never scroll-guess.

## FIELD IDS (shift after upload rerender — re-read, never cache)

| Field | Notes |
|---|---|
| First/Last/Middle | `*:_txtFld`, `aria-required=true` |
| Country / State | paginated picklist |
| Employment History | 5 rows pre-created and often pre-filled (sometimes junk: "Now"/"Software Dev" — inspect, fix) |
| Company/Tech per row | Company+Title text, **Present Employer / Type of Business / Country** picklists |
| Formal Education | School text, **Degree** + **Major** picklists, Still Attending picklist |
| How did you hear | `Job Boards` → follow-up picklist has `Linked In`, `Indeed`, `Glassdoor`… |
| Salary | numeric only → `3300000` |
| Typed Signature | full legal name |
| Submit | `span#<n>:_submitBtn` text "Apply" (Save = `_saveBtn`) |

## COMPLETENESS GATE

Count `aria-required=true` inputs with empty value. Must be `0` before Apply.

## PROOF

Success page title becomes
`Career Opportunities: Successfully Applied to <Role> (<Company>) (<reqId>)`
and body shows `Thank you for applying!`. Capture the title — it carries the
role and req id.

## TRAPS

- `page.goto` / `page.reload` on this SPA → `net::ERR_ABORTED` or an aborted
  tool call. Never reload; the widget stays broken and filled values may be
  lost. Work with the live page.
- Clicking "Upload a Resume" text, `juic.fire(id,'click')`, or instantiating
  `SFFileUploadDialog` / `RCMFileUploadCalloutPopup` by hand **all fail** —
  the dialog renders an empty `table#227:_layoutTbl`. Only the `+` icon works.
- Do not inject your own `input[type=file]` into `form#<n>:` — the form has no
  `action`/`method`/`enctype` (pure JS uploader), so it POSTs nothing.
