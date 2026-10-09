# 🔒 Privacy & sanitization notes

This repository is a **generic, shareable** version of a personal job-application
automation project. Before it was published, all personally-identifying information
was stripped and the project was made config-driven.

## What was removed / replaced

| Category | Action |
|---|---|
| Name / identity | Replaced with `Jane Doe` placeholders; real values now come from `config/user.json` |
| Email addresses | Replaced with `jane.doe@example.com` |
| Phone numbers | Replaced with `+91 00000 00000` / `0000000000` |
| Passwords (all of them) | **Deleted** — replaced with `ChangeMe_Strong!123` placeholders or env vars |
| Resume PDF(s) + backups | **Not copied** — you bring your own via `python3 setup.py` |
| Resume MD5 hash | **Regenerated** from *your* resume during setup |
| LinkedIn URL / GitHub | Replaced with `linkedin.com/in/janedoe` |
| Home-directory paths | Replaced with `<HUB_ROOT>` / dynamic `os.path` resolution |
| Application history (`progress.json`, trackers) | **Not copied** — each user builds their own |
| Browser profiles (cookies/logins) | **Not copied** (`runtime/mcp-session`, `runtime/session`, `runtime/lseg-mcp-probe`) |
| Browser scratch snippets (`temp/`) | **Not copied** (full of form-specific PII + passwords) |
| SearXNG instance secret | **Not copied** — `infra/searxng/core-config/` is git-ignored & regenerated |
| pi session logs | **Not copied** |

## Single source of truth (DRY)

`config/user.json` → `config/answers.py` (`A` dict) → every script.
Create yours with `python3 hub.py setup`. It is git-ignored and `chmod 600`.

## Before you push a fork

1. Confirm `config/user.json` is git-ignored (`git status` must not list it).
2. Never `git add` files under `config/` containing your data, `runtime/*` profiles,
   `logs/`, `temp/`, or `scratch/`.
3. Run `python3 hub.py doctor` to see what's configured locally.
4. If you ever capture a fresh browser profile or resume, keep it out of git
   (the `.gitignore` already covers the common paths — double-check unusual names).

## If you find something sensitive

Open an issue (without pasting the secret) or submit a PR removing it. Do **not**
paste credentials into issues/PRs.
