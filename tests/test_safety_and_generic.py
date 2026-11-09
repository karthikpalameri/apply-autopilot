"""Fail-closed CAPTCHA handling and generic-repository privacy invariants."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.captcha_guard import page_has_captcha, text_has_captcha  # noqa: E402


class TestCaptchaGuard(unittest.TestCase):
    def test_detects_challenge_language(self):
        self.assertTrue(text_has_captcha("Please verify you are human"))
        self.assertTrue(text_has_captcha("reCAPTCHA"))
        self.assertTrue(text_has_captcha("h-captcha"))
        self.assertFalse(text_has_captcha("Application details"))

    def test_dom_probe_must_explicitly_return_clear(self):
        self.assertFalse(page_has_captcha(lambda _js: "CLEAR"))
        self.assertTrue(page_has_captcha(lambda _js: "CAPTCHA"))
        self.assertTrue(page_has_captcha(lambda _js: ""))

    def test_probe_errors_fail_closed(self):
        def failed_probe(_js):
            raise RuntimeError("browser unavailable")

        self.assertTrue(page_has_captcha(failed_probe))

    def test_greenhouse_driver_parses_url_and_maps_resume(self):
        from apply import gh_apply

        self.assertEqual(
            ("acme", "123"),
            gh_apply.parse_url("https://job-boards.greenhouse.io/acme/jobs/123"),
        )
        resume_q = {"label": "Resume/CV", "fields": [{"type": "input_file"}]}
        self.assertEqual("resume", gh_apply.map_answer(resume_q)[0])
        cover_q = {"label": "Cover letter", "fields": [{"type": "input_file"}]}
        self.assertEqual((None, None), gh_apply.map_answer(cover_q))

    def test_active_apply_drivers_fail_closed_on_captcha(self):
        guards = {
            "apply/fill_gh_fast.py": "page_has_captcha",
            "apply/ih_sweep.py": "captcha|recaptcha|hcaptcha",
            "apply/li_drive.py": "captcha|recaptcha|hcaptcha",
            "apply/li_listed_apply.py": "captcha|recaptcha|hcaptcha",
        }
        for rel, guard in guards.items():
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                self.assertIn(guard, f.read(), f"{rel} must stop at CAPTCHA")
        # gh_apply.py is dry-run by default: real submission is an explicit --submit opt-in
        with open(os.path.join(ROOT, "apply/gh_apply.py"), encoding="utf-8") as f:
            self.assertIn("--submit", f.read(), "gh_apply must default to dry-run")

    def test_repo_has_no_known_personal_residue_or_captcha_api(self):
        files = [
            "CHANGELOG.md", "config/user.json.example", "config/answers.py", "setup.py",
            "skills/REFERENCE.md", "skills/apply/SKILL.md", "README.md", "AGENTS.md",
        ]
        chunks = []
        for rel in files:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                chunks.append(f.read().lower())
        content = "\n".join(chunks)
        for marker in ("cigna", "karthikpalameri", "capsolver_api_key"):
            self.assertNotIn(marker, content)

        for rel in ("apply/fill_gh_fast.py", "archive/scripts/ashby_apply.py",
                    "archive/scripts/gh_spa_embed_apply.py"):
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                code = f.read().lower()
            self.assertNotIn("solve_recaptcha", code, f"{rel} must not solve CAPTCHA")
            self.assertNotIn("solve_hcaptcha", code, f"{rel} must not solve CAPTCHA")


if __name__ == "__main__":
    unittest.main()
