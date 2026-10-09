#!/usr/bin/env python3
"""find/tracker_reconcile.py — APPLIED vs NOT-APPLIED tracker.

Reconciles two sources and writes an authoritative report to this folder:
  1. config/progress.json  (every application we recorded — the ground truth of what was attempted)
  2. Gmail inbox confirmations (via core/gmail_read.py --dump → logs/gmail_inbox.txt)

Output:
  - config/applied_vs_not_applied.md   (README-friendly, in-hub)
  - scratch/APPLIED.md                 (caveman dedupe tracker — kept in sync)

Two run modes:
  .venv/bin/python find/tracker_reconcile.py          # progress.json only (fast, no browser)
  .venv/bin/python find/tracker_reconcile.py --gmail  # + read inbox confirmations (needs CloakBrowser)
"""
import json, os, re, sys, datetime, collections

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = os.path.join(HUB, "config", "progress.json")
OUT = os.path.join(HUB, "config", "applied_vs_not_applied.md")
APPLIED_MD = os.path.join(HUB, "scratch", "APPLIED.md")
INBOX_TXT = os.path.join(HUB, "logs", "gmail_inbox.txt")

APPLIED_STATUS = {"submitted", "submitted-awaiting-email", "submitted-awaiting-employer-confirmation",
                  "applied", "done", "verified", "email-sent", "sent-by-user",
                  "confirmed-email", "confirmed-ats", "confirmed-linkedin", "email-verified",
                  "email-confirmed", "submitted-email", "submitted-confirmed", "duplicate-submitted"}


def load_progress():
    try:
        return json.load(open(PROG))
    except Exception as e:
        print(f"❌ cannot read {PROG}: {e}")
        sys.exit(1)


def company_of(v):
    for k in ("company", "Company", "Organization", "org", "name"):
        if isinstance(v, dict) and v.get(k):
            return v[k]
    return ""


def collect_applications(d):
    """Flatten progress.json, including the canonical verified_applications list.

    Older progress files used underscore-prefixed lists or flat company keys; keep
    those formats readable while deduplicating records that share a record_id/URL.
    """
    recs = []
    seen = set()

    def add(item, src, index=0, fallback_company=""):
        if not isinstance(item, dict):
            return
        co = company_of(item) or fallback_company
        if not co:
            return
        identity = item.get("record_id") or item.get("url") or (src, index)
        if identity in seen:
            return
        seen.add(identity)
        proof = item.get("proof") or item.get("note") or item.get("status") or ""
        recs.append({
            "company": co,
            "title": item.get("role") or item.get("title") or item.get("req") or "",
            "status": item.get("status", "submitted"),
            "date": item.get("date", ""),
            "proof": str(proof),
            "record_id": item.get("record_id", ""),
            "url": item.get("url", ""),
            "src": src,
        })

    # Current canonical format.
    for index, item in enumerate(d.get("verified_applications", [])):
        add(item, "verified_applications", index)

    # Legacy session-confirmed product lists.
    for k, v in d.items():
        if isinstance(k, str) and k.startswith("_") and isinstance(v, list):
            for index, item in enumerate(v):
                if isinstance(item, dict):
                    legacy = dict(item)
                    if "status" not in legacy:
                        legacy["status"] = "verified" if legacy.get("proof") else "submitted"
                    add(legacy, k, index)

    # Legacy flat company-session keys.
    for k, v in d.items():
        if isinstance(k, str) and not k.startswith("_") and isinstance(v, dict):
            add(v, "progress", k, fallback_company=k)

    # Legacy LinkedIn easy-apply list.
    for index, item in enumerate(d.get("linkedin", [])):
        if isinstance(item, dict):
            legacy = dict(item)
            legacy.setdefault("title", legacy.get("role", ""))
            add(legacy, "linkedin", index)

    return recs


def applied(rec):
    s = rec["status"].lower()
    return any(a in s for a in APPLIED_STATUS)


def is_email_verified(rec):
    """True only for explicit ATS or employer-email proof.

    LinkedIn's generic ``Application submitted`` state is retained for dedupe,
    but is intentionally not treated as employer confirmation.
    """
    s = str(rec.get("status") or "").lower()
    proof = str(rec.get("proof") or "").lower()
    status_ok = any(v in s for v in ["confirmed-email", "confirmed-ats", "email-verified",
                                     "email-confirmed", "submitted-email", "submitted-confirmed"])
    proof_mail = bool(re.search(r"(thank you for applying(?: to [a-z]+!)?|thank you for your application|"
                               r"we['’ ]ve received your application|your application has been received|"
                               r"successfully submitted|application acknowledgment|confirmed.?via.?email|"
                               r"\bgmail .*(thank you|received|applied|acknowledg)|email .*(confirmation|confirmed)|inbox .*confirm)", proof))
    # Generic LinkedIn text is not ATS/email evidence unless the record has an
    # explicit ATS/email status. Also let explicit negative wording win.
    external_marker = bool(re.search(r"(ats|successfactor|greenhouse|workday|lever|jobvite|breezy|oracle|"
                                     r"career portal|candidate home|gmail|employer email|recruiting)", proof))
    linkedIn_only = bool(_NON_VERIFIED_PROOF.search(proof)) and not external_marker
    negated = bool(re.search(r"(no|not|without|awaiting|pending|unavailable).{0,80}(email|confirmation|acknowledg)|"
                            r"email not received|no confirmation email|uuid~", proof))
    if status_ok:
        return True
    return proof_mail and not linkedIn_only and not negated


# EXCLUDE generic LinkedIn 'submitted'/'application sent' from email-verified proof
_NON_VERIFIED_PROOF = re.compile(r"(application sent|application submitted|application status|applied tab|to your inbox|by email)")


def read_inbox_confirmations():
    """If logs/gmail_inbox.txt exists, list companies with application-confirmation keywords."""
    if not os.path.exists(INBOX_TXT):
        return []
    confirm = []
    for line in open(INBOX_TXT, errors="ignore"):
        if re.search(r'(application received|thank you for applying|received your application|your application|application has been|application submitted|successfully applied|applied for)', line, re.I):
            confirm.append(line.strip()[:160])
    return confirm


def group_by_company(recs):
    g = collections.defaultdict(list)
    for r in recs:
        if r["company"]:
            g[r["company"].lower()].append(r)
    return g


def build_report(recs, inbox_confirmations, show_email_evidence):
    by_co = group_by_company(recs)
    applied_list, notapplied_list, unverified_list = [], [], []
    for co, items in by_co.items():
        label = items[0]["company"]
        verified = any(is_email_verified(i) for i in items) and any(applied(i) for i in items)
        any_applied = any(applied(i) for i in items)
        email_hit = any(co in c.lower() for c in inbox_confirmations) if inbox_confirmations else False
        if verified or (any_applied and email_hit):
            applied_list.append((label, items))
        elif any_applied:
            unverified_list.append((label, items))  # submitted but not email-proven
        else:
            notapplied_list.append((label, items))

    applied_list.sort(); notapplied_list.sort(); unverified_list.sort()
    today = datetime.date.today().isoformat()

    lines = []
    lines.append(f"# APPLIED vs NOT-APPLIED  —  {today}")
    lines.append("")
    lines.append(f"- **APPLIED (verified)** : {len(applied_list)}")
    lines.append(f"- **SUBMITTED / UNVERIFIED** (no email proof yet) : {len(unverified_list)}")
    lines.append(f"- **NOT APPLIED / PENDING** : {len(notapplied_list)}")
    lines.append("")
    lines.append("## ✅ APPLIED (verified — proof on record)")
    lines.append("| Company | Role | Date | Proof |")
    lines.append("|---|---|---|---|")
    for co, items in applied_list:
        for i in items[:2]:
            lines.append(f"| {co} | {i.get('title','')[:38]} | {i.get('date','')} | {(i.get('proof') or '')[:60]} |")
    lines.append("")
    lines.append("## ⏳ SUBMITTED / UNVERIFIED (in progress — email proof pending)")
    lines.append("| Company | Role | What's recorded |")
    lines.append("|---|---|---|")
    for co, items in unverified_list:
        for i in items[:2]:
            lines.append(f"| {co} | {i.get('title','')[:38]} | {(i.get('proof') or i.get('status') or '')[:60]} |")
    lines.append("")
    lines.append("## ❌ NOT-APPLIED / PENDING")
    lines.append("| Company | Role | Why |")
    lines.append("|---|---|---|")
    for co, items in notapplied_list:
        for i in items[:2]:
            lines.append(f"| {co} | {i.get('title','')[:38]} | {(i.get('proof') or i.get('status') or 'pending')[:60]} |")
    lines.append("")
    if inbox_confirmations and show_email_evidence:
        lines.append("## 📬 GMAIL confirmation emails seen (this check)")
        for c in inbox_confirmations[:15]:
            lines.append(f"- {c}")
        lines.append("")

    return "\n".join(lines), {
        "total_companies": len(by_co),
        "applied": len(applied_list),
        "unverified": len(unverified_list),
        "not_applied": len(notapplied_list),
        "inbox_confirmation_emails": len(inbox_confirmations),
        "date": today,
    }


def write_scratch_applied_md(recs):
    """Keep every submitted record in the dedupe source, not only email-confirmed ones."""
    lines = ["# APPLIED (dedupe source — auto-refreshed by tracker_reconcile.py)",
             f"# {datetime.date.today().isoformat()}", "# nothing below should be re-applied", ""]
    submitted = sorted((r for r in recs if applied(r)),
                       key=lambda r: (str(r.get("company", "")).lower(),
                                      str(r.get("title", "")).lower(),
                                      str(r.get("date", ""))))
    for r in submitted:
        mark = "x" if is_email_verified(r) else "~"
        record_id = f" [{r.get('record_id')}]" if r.get("record_id") else ""
        status = r.get("status") or "submitted"
        lines.append(f"- [{mark}] {r.get('company','')} — {(r.get('title') or '')[:60]} "
                     f"({r.get('date','')}){record_id} [{status}]")
    try:
        os.makedirs(os.path.dirname(APPLIED_MD), exist_ok=True)
        open(APPLIED_MD, "w").write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"⚠️  could not write {APPLIED_MD}: {e}")


def main():
    gmail_mode = "--gmail" in sys.argv
    d = load_progress()
    recs = collect_applications(d)
    inbox = []
    if gmail_mode:
        dump_script = os.path.join(HUB, "core", "gmail_read.py")
        inbox_txt = os.path.join(HUB, "logs", "gmail_inbox.txt")
        if "--fresh" in sys.argv or not os.path.exists(INBOX_TXT):
            print("📡 reading Gmail inbox via browser (CloakBrowser must be running)…")
            import subprocess
            subprocess.run([sys.executable, dump_script, "--dump", inbox_txt], cwd=HUB, timeout=180)
        inbox = read_inbox_confirmations()
        if not inbox:
            print("ℹ️  no confirmation keywords found in inbox — companies marked unverified will stay pending."
                  " Re-run with --fresh after inbox reload.")
    report, stats = build_report(recs, inbox, show_email_evidence=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(report)
    # Sync the dedupe source with every submitted record. Unverified records are
    # marked [~] so they are not accidentally re-applied while awaiting proof.
    write_scratch_applied_md(recs)
    print(f"📍 {OUT}")
    print(f"companies: {stats['total_companies']}  applied: {stats['applied']}  "
          f"unverified: {stats['unverified']}  not-applied/pending: {stats['not_applied']}"
          f"  gmail-confirmations:{stats['inbox_confirmation_emails']}")


if __name__ == "__main__":
    main()
