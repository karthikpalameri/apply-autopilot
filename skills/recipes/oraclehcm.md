# ORACLE HCM recipe (Oracle · Pearson ×2 · Nokia · WESCO-type)
## URL: <co>.fa.*.oraclecloud.com/hcmUI/CandidateExperience/.../job/<id>/apply
## WINS: Pearson ×2, Oracle (90%), Nokia(3-field block) | FLOW:

1. EMAIL screen: `primary-email-0` or `-1` (varies per instance) → fill email.
   ACCEPT consent → T&C dialog "Agree" = `button.app-dialog__footer-button`.
   (Pearson T&C = AGREE button; Nokia "Are You Still With Us?" dialog = Continue Working.)
2. OTP: Oracle REQUIRES 6-digit email code (`input[id^=pin-code]`), real-type each digit → VERIFY.
   Pearson/Nokia: no OTP (goes straight to form). One clean pass: read freshest Gmail code FIRST.
3. IMPORT PROFILE: `input[type=file]` setInputFiles(resume) → auto-fills personal info
   (name/email/phone/address/links). Fix gaps after.
4. cx-selects (country/city/state/gender): **click → type → click EXACT dropdown option.**
   Typing alone commits display but NOT model. Options only appear after click+type+wait.
   Plain inputs (address/pin): native setter + blur commits.
5. Questions = cx-select pills: `span.cx-select-pill-name` → click the right Yes/No in order.
6. E-Signature: fill `fullName-N` (Full Name) before submit.
7. Work/education entries imported from resume need Edit→Save confirmation each
   (issue nav focuses them; also school "Other" pick if school not listed).
8. Submit → `/my-profile` "Thank you for your job application" + ACTIVE JOB APPLICATIONS = PROOF.
