# iCIMS RECIPE (symplr — hCaptcha-gated)

## FLOW
1. Email step (`#email` name=css_loginName) → Next → **hCaptcha = USER solves**
2. Candidate Profile form (icims_content_iframe):
   - Login/email, First/Last, Phone, DOJ (Aug/15/2026), Address, City, Zip
   - Password 13ch MATCH (typing doubles — always clear+retype, verify lengths)
   - Type=Mobile, Country=India, State=Karnataka, how-heard
3. Resume step → "My computer" → upload → resume.pdf chip
4. Submit Profile → proof?

## KEY LESSONS
- **Verify EVERY field before submit** (read values, not the a11y label)
- Password doubling: 26ch vs 13ch mismatch = silent required-error
- DOJ year must be 2026 (typing shifts)
- hCaptcha = user click (never report past unsolved)
