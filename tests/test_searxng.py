"""Tests for infra/searxng/setup.py (config generation — no Docker needed)."""
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def load_setup_module():
    path = os.path.join(ROOT, "infra", "searxng", "setup.py")
    spec = importlib.util.spec_from_file_location("searxng_setup_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


searxng = load_setup_module()


class TestSearxngSetup(unittest.TestCase):
    def test_write_settings_enables_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = searxng.write_settings(base=d)
            self.assertTrue(os.path.exists(p))
            txt = open(p, encoding="utf-8").read()
            self.assertIn("use_default_settings: true", txt)
            self.assertIn("secret_key:", txt)
            self.assertIn("- json", txt)
            self.assertIn("- html", txt)

    def test_write_env_has_secret(self):
        with tempfile.TemporaryDirectory() as d:
            p = searxng.write_env(base=d)
            self.assertTrue(os.path.exists(p))
            txt = open(p, encoding="utf-8").read()
            self.assertIn("SEARXNG_BASE_URL=http://127.0.0.1:8080", txt)
            self.assertRegex(txt, r"SEARXNG_SECRET=[0-9a-f]{48}")

    def test_constants(self):
        self.assertEqual("http://127.0.0.1:8080", searxng.BASE_URL)


if __name__ == "__main__":
    unittest.main()
