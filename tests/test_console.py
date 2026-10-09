"""Tests for cross-platform console safety (Windows cp1252 UTF-8 guard)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.console import enable_utf8, propagate_utf8_env  # noqa: E402


class TestConsole(unittest.TestCase):
    def test_enable_utf8_does_not_raise(self):
        enable_utf8()  # must never raise, on any platform

    def test_propagate_sets_env(self):
        os.environ.pop("PYTHONUTF8", None)
        propagate_utf8_env()
        self.assertEqual("1", os.environ.get("PYTHONUTF8"))

    def test_entry_points_wire_utf8(self):
        # entry points run directly (incl. by CI) must enable UTF-8 output
        for rel in ("validate.py", "hub.py", "tests/run_tests.py", "infra/searxng/setup.py"):
            txt = open(os.path.join(ROOT, rel), encoding="utf-8").read()
            self.assertTrue(
                ("enable_utf8" in txt) or ("reconfigure" in txt),
                f"{rel} is not Windows-console-safe",
            )


if __name__ == "__main__":
    unittest.main()
