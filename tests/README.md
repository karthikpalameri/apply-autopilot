# 🧪 Tests — organized validation for the whole repo

Run everything:

```bash
python3 tests/run_tests.py      # or:  python3 hub.py test
```

## Layout (one file per concern)

| File | Validates |
|---|---|
| `run_tests.py` | test runner — discovers `test_*.py`, prints pass/fail + % success rate |
| `test_skills.py` | skill graph: every node exists, frontmatter valid, links resolve |
| `test_code_compile.py` | every `.py` file compiles |
| `test_resume_parser.py` | resume parsing logic (email/phone/links/name/skills/education/years) |
| `test_onboarding.py` | profile artifact generation + profile.md writer |
| `test_setup.py` | setup helpers (slugify, resume filename derivation) |
| `test_installer.py` | installer manifest (pi packages/skills/extensions) + per-OS commands |
| `test_mcp_config.py` | MCP invariants: `.mcp.json` empty, pi MCP/web-search config shape |
| `test_eval.py` | readiness evaluator weights sum to 100% + every check runs |
| `test_searxng.py` | SearXNG setup.py config generation (env + settings.yml, no Docker) |
| `test_headed_browser.py` | browser ALWAYS headed (visible) — asserts no headless mode anywhere |

## Adding a test

1. Create `tests/test_<thing>.py` with `unittest.TestCase` classes.
2. Add `sys.path.insert(0, <repo root>)` at the top so it can import repo modules.
3. Run `python3 tests/run_tests.py`.

## Conventions

- **No external test dependencies** — stdlib `unittest` only, so it runs on any machine.
- Tests are **non-destructive** (no installs, no network, no browser launches, no writes
  outside `tempfile`).
- Keep them **fast + deterministic** so CI/agents can run them after every change.
