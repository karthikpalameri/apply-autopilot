# Changelog

All notable changes to **Apply Autopilot** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.0.1] — 2026-10-09

First public release. A generic, cross-platform (macOS / Linux / Windows)
job-application automation repo that ships with **zero personal data**.

### Added
- **Guided onboarding** (`onboarding.py`): resume-first flow → ABCD confirm/change/skip
  review → skill grill → interview grill → Gmail consent → environment check.
- **Quick setup** (`setup.py`): identity / resume / credentials wizard that writes the
  git-ignored `config/user.json` (`chmod 600`).
- **Cross-platform installer** (`installer.py`): detects the OS package manager
  (`brew` / `apt` / `winget`), shows missing dependencies with exact commands, asks for
  consent, then installs Python + npm + pi + SearXNG.
- **Browser automation stack**: `runtime/server.py` ctl bridge (`:9000`) +
  cloakbrowser MCP (`:3000`), **always headed** (visible), never headless.
- **Skills graph** (`skills/`): `apply`, `find`, `verify`, `email`, `track`, `learn`,
  `ops`, `resume`, `searxng` + master `SKILL.md`, `REFERENCE.md`, `RELIABILITY.md`,
  per-ATS recipes, and generic `LESSONS/` templates.
- **Private web search**: local SearXNG with JSON API (`infra/searxng/setup.py`).
- **Readiness evaluator** (`eval.py`): weighted test cases → % success rate + fixes.
- **Repo validator** (`validate.py`): compiles every `.py` + verifies skill links.
- **Test suite** (`tests/`): 46 stdlib-`unittest` tests across skills, code, parsing,
  onboarding, installer, MCP config, eval weights, SearXNG, headed-browser, the
  first-run guard, and cross-platform console safety.
- **pi integration**: packages manifest (`pi-mcp-adapter`, `pi-web-access`,
  `context-mode`) + `ctx-*` skills + MCP/web-search config generation.
- **First-run guard** (`hub.py`): a fresh clone detects the missing `config/user.json`
  and offers to launch onboarding.
- **CI** (`.github/workflows/ci.yml`): matrix over macOS / Linux / Windows × Python
  3.10–3.13 running `validate.py` + the test suite, plus a privacy scan that fails the
  build if any personal data or personal config is tracked.
- **Cross-platform hygiene**: `core/console.py` forces UTF-8 stdio (so emoji output
  never crashes the Windows `cp1252` console); `.gitattributes` normalizes line endings
  (CRLF for `*.bat`, LF elsewhere); `PYTHONUTF8=1` exported by the wrappers + CI.
- **Docs**: `README.md`, `AGENTS.md`, `PRIVACY.md`, `docs/INSTALL.md`,
  `docs/DEPENDENCIES.md`, MIT `LICENSE`.

### Security
- All personal identifiers removed from both the working tree **and** the entire git
  history (`git filter-repo` — blobs, filenames, and commit messages).
- No secrets, passwords, recruiter emails, CTC figures, addresses, or employer names
  are present anywhere in the repository.

[0.0.1]: https://github.com/karthikpalameri/apply-autopilot/releases/tag/v0.0.1
