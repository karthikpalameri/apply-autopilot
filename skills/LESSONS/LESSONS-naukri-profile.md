# NAUKRI PROFILE OPTIMIZATION — skills & settings that get recruiter calls

Concern: how to make the Naukri profile rank in recruiter searches (Resdex) so
recruiters call / schedule interviews. Applies to your configured target role
(see `config/user.json`).

## WHAT ACTUALLY DRIVES CALLS (research-consistent)
- Recruiters SEARCH a database (Resdex), they don't scroll. Calls come from being
  findable, NOT from applying to more jobs.
- Ranked by: key skills relevance (~35%), profile completeness (~25%),
  recent activity / login (~20%), resume freshness (~20%) — treat weights as estimates.
- 100% complete + recent login + photo = top of results.

## KEY SKILLS (THE 250-CHAR TRAP)
- Naukri caps the `keySkills` string at **250 characters** — verified via API error.
  Most blog advice ("add 30-50 skills") is WRONG for Naukri. You cannot hit 50.
- Use QA synonyms/variants recruiters search: Manual + Automation + API Testing,
  Selenium, Appium, Rest Assured, Webdriverio, Postman, JMeter, Java, Javascript,
  Python, SQL, TestNG, Cucumber, Jenkins, CI/CD, Git, AWS, Kubernetes, Docker,
  JIRA, Agile, POM, SDET, Functional/Regression Testing, GitLab.
- Stored in the configured user/profile source (`config/user.json` when present; otherwise `config/answers.py`) — keep the exact 249-char list,
  source of truth for the Naukri field).

## SAVE METHOD (bypass broken suggestor UI)
- Naukri's skill suggestor UI is fragile (phantom chips, data-id=undefined, maxlength
  toggles, clicks don't register). Don't fight it.
- Save key skills DIRECTLY via API:
  `POST https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v1/users/self/fullprofiles`
  Headers: Content-Type application/json, X-HTTP-Method-Override PUT, clientid d3skt0p,
  appid 105, systemid Naukri, authorization Bearer <token>, X-Requested-With XMLHttpRequest.
  Body: `{"profile":{"keySkills":"<comma-separated skills>"},"profileId":"<pid>"}`
- Get the auth token by hooking XHR.setRequestHeader on a real Save click; store in window.__tok.
- profileId = <your-naukri-profile-id>

## HEADLINE FORMULA (biggest click-lever)
`[Role] | [Years] yrs | [Top 3-4 skills] | [Company tier] | [Open to]` — <100 chars.
Example: "<Role> | <years> yrs | <top skills> | <current employer tier> → <target role>, <city>"
NO: "Looking for opportunities", "Hard-working", vague "Quality Analyst".

## SUMMARY (200-300 word pitch)
Role+years+domain → 3-4 skills → ONE quantified metric → stack → certs → target role.
Your configured cover text should already fit this shape; if `config/profile.json` is missing, generate it via onboarding rather than probing for it.

## OTHER SETTINGS THAT GATE CALLS
- "Visible to Recruiters" + "Show contact details" = ON (privacy). If off: no calls.
- Job status = "Immediately looking for a job".
- Notice period: "Negotiable" or <=15 days tends to get more calls than 60-90 days. If you are serving notice, set the Naukri notice field to "Negotiable"/"Immediate" (0–15 days).
- Expected CTC: never blank; set it 15-25% above current. Store the real numbers only in `config/user.json` (git-ignored) — never hardcode them here.

## FREE "BOOST" CADENCE (matters as much as content)
- Log in weekly (Recently Active top-of-search)
- Edit headline/summary monthly (Profile Updated)
- Re-upload resume every 60 days (freshness)
- Apply to 3-5 jobs weekly
- Set calendar reminders — replicates ~60-70% of paid Profile Boost for free.

## VERIFIED vs ANECDOTAL
- Verified: 250-char keySkills cap (hit the API error), headline/search mechanics,
  visibility toggle, notice filter, photo boost.
- Anecdotal: exact weight %s, "4x"/"5x" multipliers, "3x calls" — treat as estimates.
