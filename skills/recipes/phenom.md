# PHENOM recipe (proven)
## URL: careers.<co>/global|us/en/apply?step=1&stepname=personalInformation
## WINS: multiple product companies via this flow | FAILS: none with this flow

## FILL — one Playwright transaction (`.fill()` + `selectOption()`)
- Use `browser_run_code_unsafe` with `const { page } = cloak;`; do not use an `async (page) => ...` wrapper.
- Discover the current step once, fill related fields sequentially, and return a compact readback of changed values. `.fill()` replaces; do not clear it first.
- Wait for the next-step anchor or visible upload input; fixed sleeps are fallback only.

## FILL — Playwright .fill() + selectOption ONLY (native setter/htype appends; React won't commit)
1. step 1: fill via `[id="..."]` (byId) — country/device/ccode/source via selectOption.
   ids: cntryFields.firstName/lastName/addressLine1/city/postalCode · email · phoneWidget.phoneNumber
2. consents: checkbox .check({force:true}) — or T&C dialog "Agree" button if present.
3. NEXT → resume upload is MANDATORY (modal "Resume Import is mandatory").
   `input[type=file]` setInputFiles(resume) → accept "You have Uploaded Resume Successfully." modal; read the canonical filename back before continuing.
4. Re-select country/device/ccode (resume re-render wipes them).
5. Experience: resume auto-parses. FIX: degree select = "Bachelor of Engineering"
   (auto-picks "Associates" — wrong), WE1 "currently work here" check, hidden `school` field set.
6. Questions: selects via selectOption (auth=Yes, sponsor=No, salary=<expected CTC numeric>, join=1-3mo).
7. Some questions are REACT-SELECTS disguised as text inputs:
   `click input → ArrowDown → getByRole('option', {name, exact:true}).first().click()`
   (check parent class: `select-shell remix-css...-container`)
8. reCAPTCHA (FIS): CapSolver token → set `textarea[name=g-recaptcha-response]`.
   Next may stay disabled (Phenom reads widget state, not textarea) → human click fallback.
9. Submit → capture `applythankyou?status=success&jobSeqNo=...` and the exact success text immediately in the same FORM state = PROOF. Gmail can be checked in the combined batch pass.
