"""Fail-closed CAPTCHA handling and generic-repository privacy invariants."""
import os
import sys
import unittest
from unittest.mock import patch

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

    def test_greenhouse_driver_refuses_submit_on_captcha(self):
        from apply import gh_apply

        with patch("core.resume_secure.PICK"), \
             patch("core.resume_secure.BEFORE_UPLOAD", return_value="/tmp/resume.pdf"), \
             patch("core.resume_secure.POST"), \
             patch.object(gh_apply, "fetch_questions", return_value={"questions": []}), \
             patch.object(gh_apply, "_ctl") as ctl, \
             patch.object(gh_apply, "_ev", side_effect=["0", "CAPTCHA"]) as evaluate, \
             patch.object(gh_apply.time, "sleep"):
            result = gh_apply.apply("board", "123", "https://example.invalid/job")

        self.assertFalse(result)
        self.assertEqual(2, evaluate.call_count)
        self.assertFalse(any("b.click()" in str(call) for call in evaluate.call_args_list))
        self.assertFalse(any("submit" in str(call).lower() for call in ctl.call_args_list))

    def test_active_apply_drivers_have_captcha_guard(self):
        expected = {
            "apply/gh_apply.py": "page_has_captcha",
            "apply/fill_gh_fast.py": "page_has_captcha",
            "apply/ih_sweep.py": "page_has_captcha",
            "apply/li_drive.py": "page_has_captcha",
            "apply/li_listed_apply.py": "page_has_captcha",
        }
        for rel, guard in expected.items():
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                self.assertIn(guard, f.read(), f"{rel} must stop at CAPTCHA")

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
