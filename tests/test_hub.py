"""Tests for hub.py — the command center + first-run onboarding guard."""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import hub  # noqa: E402


class TestHub(unittest.TestCase):
    def test_is_first_run_returns_bool(self):
        self.assertIsInstance(hub.is_first_run(), bool)

    def test_welcome_mentions_privacy(self):
        self.assertIn("config/user.json", hub.FIRST_RUN_WELCOME)
        self.assertIn("ZERO personal data", hub.FIRST_RUN_WELCOME)

    def test_command_requires_identity(self):
        # with no config, a command needing identity must NOT run the command
        with mock.patch.object(hub, "is_first_run", return_value=True), \
             mock.patch.object(hub, "cmd_start", side_effect=AssertionError("must not run")):
            with redirect_stdout(io.StringIO()):
                code = hub.maybe_prompt_first_run(command="start")
            self.assertEqual(1, code)

    def test_no_prompt_when_configured(self):
        with mock.patch.object(hub, "is_first_run", return_value=False):
            self.assertIsNone(hub.maybe_prompt_first_run())

    def test_prompt_runs_onboard_on_yes(self):
        with mock.patch.object(hub, "is_first_run", return_value=True), \
             mock.patch.object(hub, "cmd_onboard", return_value=0) as m, \
             mock.patch("builtins.input", return_value="y"):
            with redirect_stdout(io.StringIO()):
                hub.maybe_prompt_first_run()
            m.assert_called_once()


if __name__ == "__main__":
    unittest.main()
