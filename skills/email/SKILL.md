---
name: email
description: EMAIL node — recruiter outreach via Gmail (draft by default; send only with fresh user consent).
parent: skills/SKILL.md
---

# EMAIL

## CONSENT GATE (read first)
- Gmail is used ONLY when `gmail_consent: true` is present in `config/user.json`
  (set during `python3 hub.py onboard`). Without it, skip OTP reads + cold emails.
- DRAFTING a recruiter email is the default. SENDING requires a FRESH user approval
  per email (show the subject + body, ask, then send). Never auto-send.

## TAB SAFETY
- Follow `skills/SKILL.md` → **TWO-TAB SESSION**. Gmail drafts/reads use the one reusable GMAIL tab; never navigate FORM to Gmail.

## FLOW
1. Find recruiter (LinkedIn post/company page)
2. Draft = humble template (skills/recipes/email-template-humble.md) + name + "Found via: <link>"
3. Gmail compose URL → save as DRAFT (create fresh — editing flaky)
4. Attach resume (filechooser); save draft
5. Show the user the draft → ask "send now?" → only on explicit YES, click Send
6. Track config/progress.json (status: draft | sent)

## TONE
- Humble + specific (role, company, found-via link)
- Expected CTC = current × 1.22 (auto)

## OTP / VERIFICATION ORDER
- When resetting an email, requesting an OTP, or requesting a verification link, first perform the Send OTP/verification action on the webpage.
- Only after that webpage action succeeds, open or refresh Gmail and use the newly received OTP/link. Never search Gmail first and reuse a stale code or link.

## READ CONFIRMATIONS
- core/gmail_read.py (browser Gmail, read-only — IMAP needs App Password)

## LESSONS
- skills/LESSONS/LESSONS-email.md


---

## RELATED (skill graph — every node is one click away)
- **Master:** `skills/SKILL.md` · **Reference:** `skills/REFERENCE.md` · **Reliability:** `skills/RELIABILITY.md`
- **Nodes:** `apply` · `email` · `find` · `learn` · `ops` · `resume` · `searxng` · `track` · `verify` (each `skills/<node>/SKILL.md`)
- **Recipes:** `skills/recipes/` — workday · greenhouse · lever · icims · linkedin · phenom · breezy · jobvite · oraclehcm · email-template-humble
- **Lessons:** `skills/LESSONS/LESSONS-*.md` — apply · find · verify · email · ops · naukri-profile
- **Index:** `skills/README.md` · **Repo entry for agents:** `AGENTS.md`
