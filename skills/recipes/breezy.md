# Breezy HR playbook (Zinier ×3 wins 2026-08-22)

URL: https://<co>.breezy.hr/p/<posId>-<slug>/apply

## Flow (all via Playwright/MCP run_code)
1. Fill [name=cName/cEmail/cPhoneNumber/cAddress] + cSummary (summary may be PRE-FILLED by resume parser → check inputValue first)
2. Resume: setInputFiles on input[type=file] — VERIFY via file.files.length + body text
3. gdprAgreement checkbox (req)
4. Required questions vary PER ROLE (SDET Lead = none; SDET-2 = work/edu + demographics):
   - Employment/Education rows AUTO-PARSED from resume (Bottomline + BMS appear) — but dates/summary may be empty/wrong
   - Date inputs: display mm/dd/yyyy, set ISO value "2013-06-01"
   - Race "I don't wish to answer" + **Gender=Male** (name=gender/race_ethnicity, label-scoped click)
5. Submit → URL /apply/submitted = CONFIRMED. If 0-errors but URL unchanged → re-click Submit after 2s.

## Gotchas
- Clicking job cards on co website opens "Schedule a Demo" modal (marketing trap) — go DIRECT to breezy.hr board
- Audit required controls and error text across the whole form with scoped DOM and bounded scroll. If an error only appears visually, use a local viewport crop + tesseract OCR per `skills/REFERENCE.md#screenshot-budget-measured-2026-11-07--the-single-biggest-token-sink` (never a full-page image).
