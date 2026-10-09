# VERIFY LESSONS
## 2026-08-12
- Workday proof: /jobTasks/completed/application + "Application Submitted" (Fox R50033578)
- Lever proof: /thanks URL (AcmeThree — no captcha needed)
- GH proof: "Thank you for applying. Your application has been received." (AKKO ×2)
- Dup gate ("previous application") = NOT a new application — never count as applied
- OCR beats a11y: a11y shows stale/doubled values (First Name "JaneJaneJane")

## RETRO 2026-08-12
- 10/10 proof-gated today: Workday completed-page, Lever /thanks, GH "Thank you" — all OCR-verified
- "Applied" marker on LinkedIn = NOT proof (could be old) — the ATS thank-you = proof
- Phone "too long" error = wrong country code picked (+246 vs +91) — verify country option exact

## RETRO — THE VERIFICATION MISS (USER CALLED OUT)
- AFTER EVERY submit → MUST read the positive final message (OCR): "Applied tab of My Jobs" / "Thank you for applying" / "Application Submitted" / Lever /thanks / Workday completed
- NEVER report "submitted" on inference (form closed / button gone / errs=0 ≠ done)
- If the positive message is ABSENT → NOT done → keep fixing (agentic loop) or record "in-progress: <exact blocker>"
- Record the EXACT proof text in progress.json (proof field) — not a paraphrase
- Caught: AcmeTwo (dup gates), Dialpad (how-heard), AcmeTwentyTwo (Review stuck), AcmeSmartRecruiters (fixed — verified "Applied tab")
- The easy-apply stuck-Review FIX: DOM click 2-3x with 6s waits + consent via raw checkbox + getByRole Submit = works (AcmeSmartRecruiters proof)

## RETRO 2026-08-25 (hard-proof discipline held)
- GH confirmed = **/confirmation** or `/embed/job_app/confirmation?for=<org>&token=<id>` URL + EXACT thank-you read in-session (AcmeFive "Thank you for applying. Your application has been received." · Fivetran "Thank you for your interest in Fivetran! We're delighted..." · Okta "Thank you for applying").
- proof capture = form gone + positive message + URL. Once — a re-fetch of the Fivetran job URL shows the plain job page (confirm lost) — do NOT re-verify by re-navigating.
- GH embed option-click proof BEFORE submit: read control innerText (auth=Yes/visa=No/...) + checkbox states → show committed, then submit.

## RETRO 2026-08-26 (proof discipline under hard walls)
- LinkedIn Easy Apply success is UNREADABLE headless (Applied tab virtualized; my-applied/collections/applied render 0 cards; job page hides Apply btn but no "Applied" text). Apply-btn-gone = best headless positive signal; record as best-effort, DON'T count as hard-verified, note the exact evidence.
- External-site PROOF variants captured: Cisco Phenom `/applythankyou?status=success` + candidateId + OCR "successfully applied" (hard). Fivetran GH `/confirmation` text (hard). These = the confirmed set.
- ABOVE ALL: read success message LIVE right after Submit (before any redirect/close). If it navigates away, the proof is lost — capture in the same action as submit.
- LinkedIn EasyApply proof = read "Your application was sent to <Co>!" LIVE (post-Submit, before page return) + body "Applied" + Apply-button-gone on job page. Triangulate all 3; OC a screenshot.

## KAIZEN-VERIFY 2026-08-26 (proof = success page + inbox email)
- CONFIRMED set (this session, email-verified): Glean, NetApp(#135871), Fivetran + prior Okta/AcmeFive/GitLab/Nutanix/Siemens/Amazon/WBD/Pearson/HackerRank.
- Hard-proof hierarchy: 1) inbox confirmation email (subject names role/req) 2) success URL (/confirmation, /applythankyou?status=success, "Successfully Applied", "sent") 3) body "Applied"/apply-btn-gone. Use ≥2 sources.
- READ email for the authoritative DATE + req-id; update both trackers to match. Before any new application, search Gmail and both trackers to prevent repeats.
- ACT: any new win/lesson → standardize → next session baseline (Kaizen continuity).
