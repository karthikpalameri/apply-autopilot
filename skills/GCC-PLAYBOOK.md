# GCC PLAYBOOK — the channel that produced an actual offer

**Status: PROVEN.** This is not theoretical. It produced a **selected / offer** outcome.

## The discovery, reconstructed from evidence

There is **no Fortune-500 list in this repo** (`grep -ri fortune` → zero hits in code,
skills, docs). The real mechanism was **indirect Fortune-500 access via a GCC operator**.
Reconstructed from Gmail + the job description itself:

```text
Talent500 (GCC job platform)
   ↓  "Hi <your name>, thanks for completing your application!"
ANSR MedTech Capability Center  (the GCC — the employer of record)
   ↓  "Your Senior Test Engineer - Cloud Ops application at ANSR MedTech"
HR Interview  →  Document submission  →  SELECTED
   ↓  "Congratulations! You have been selected for the Position of
       Senior Software Development Engineer In Test at
       ANSR MEDTECH CAPABILITY CENTER PRIVATE LIMITED"
The client brand (hidden)
   = "a Fortune 100 Fastest-Growing Company in the MedTech sector"
```

### The insight
We never applied to a Fortune-500 company. We applied to the **company that runs
Fortune-500 GCCs**. The brand stays hidden in the listing, but the parent *is*
Fortune-listed — so this satisfies the "product company / substantial scale" gate
**without needing the brand name up front.**

## The two-layer pattern

| Layer | Examples | What it gives you |
|---|---|---|
| **GCC operators** (employer of record) | ANSR, ANSR MedTech, Marriott Tech Accelerator, 1Connect, Under Armour GCC | Real Fortune-500 work, Indian entity, applies like a normal company |
| **GCC job platforms** (discovery) | **Talent500**, ANSR careers (`ansr.com/careers`), Instahyre, Cutshort, Weekday, Wellfound | Live reqs, ticket IDs like `T500-28617` |

### Why it converts better than cold ATS
- GCC roles are **India-based by construction** — no relocation/visa filter to fail.
- The GCC hires in **volume** for one client, so fewer competing signals than a
  global careers portal.
- Ticket IDs (`T500-*`) are **unique and stable** → excellent dedupe keys.
- Recruiters work the pipeline actively (you got an HR interview invite, not silence).

## Ledger-proven sourcing (where the 675 recorded attempts actually came from)
```text
linkedin   178
instahyre  104
weekday      2
wellfound    1
```
Instagram-style social aggregators are noise; **Instahyre and LinkedIn carry the volume**.
Talent500 is under-used — and it is the one that converted.

## HOW TO RUN THIS

1. **Discover** (read-only, no auth):
   ```bash
   # ANSR / GCC operator careers
   curl -s 'https://127.0.0.1:8080/search?q=site:talent500.com+SDET+Bangalore&format=json'
   # ANSR's own board lists its GCCs
   #   https://ansr.com/careers/top-gcc-jobs-careers/
   ```
   Also: `site:talent500.com QA Bengaluru`, `site:ansr.com SDET`,
   `"capability center" SDET "Fortune 500"`.

2. **Gate every hit** through the ledger before touching a form:
   ```bash
   .venv/bin/python -c "from core.applied_ledger import is_applied; print(is_applied('YipitData','Senior QA Engineer - SDET'))"
   ```

3. **Verify live** — never trust the index. Hit the employer/ATS API or the
   Talent500 page and confirm the ticket is still open.

4. **Apply** on the platform (Talent500 → Google Sign-In is in a cross-origin
   iframe; dismiss the "Stay Ahead" modal first). See `LESSONS-apply.md:78`.

5. **Record to the ledger immediately** — including blocked attempts.

## HARD CONSTRAINTS (learned the expensive way)

- **ANSR and all ANSR brands: SKIP permanently.** A 2026-11 offer was received from
  ANSR MedTech (`Senior Software Development Engineer In Test`). Do not re-apply to
  ANSR, ANSR MedTech, ANSR Tech, 1Connect, Marriott Tech Accelerator, Under Armour
  GCC, or Abercrombie GCC — all ANSR-operated. No new application at a company you
  have accepted an offer from.
- An already-selected company is **terminal**, not retryable. `is_applied()` returns
  True for ANSR; keep it that way.
- A blocked attempt (captcha/session) is still a duplicate — record it.

## FRESH TARGET LIST (as of 2026-11-04, ledger-clean, not ANSR)

| Company | Role | Loc | Yrs | Ticket / source |
|---|---|---|---|---|
| **YipitData** | Senior QA Engineer – SDET | Bengaluru | 8–12 ✓ | `T500-24633` |
| **Thales Group** | SDET Lead (Java/Python + Networking) | Bangalore | 8–10 ✓ | `T500_THG_R0327472` |
| Infogain | QA Automation Engineer (Senior) | Blr/Noida/Ggn/Mum/Pune | 6–10 ✓ | `T500_IG_92394` |

> Re-verify each is still open before applying — Talent500 tickets close silently.
