"""Tests for the migrated engine's deterministic, browser-free logic.

Covers the single-owner modules that the old repo had hand-rolled in six places:
status vocabulary, company/role dedupe identity, the typed decision layer, the
bounded `until()` poller, and OCR availability. Nothing here needs a browser.
"""
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import dedupe  # noqa: E402
from core import applied_ledger, ocr, ui  # noqa: E402
from core.decide import AuthPhase, CandidateClass, FieldKind, Gate  # noqa: E402


class TestStatusVocabulary(unittest.TestCase):
    def test_submitted_is_subset_of_applied_is_subset_of_terminal(self):
        # Enforced at import time too; this is the behavioural contract that
        # preflight/tracker used to diverge on.
        self.assertTrue(dedupe.SUBMITTED_STATUSES <= dedupe.APPLIED_STATUSES)
        self.assertTrue(dedupe.APPLIED_STATUSES <= dedupe.TERMINAL_STATUSES)

    def test_predicates_are_case_and_whitespace_insensitive(self):
        self.assertTrue(dedupe.is_submitted("  Confirmed-ATS "))
        self.assertTrue(dedupe.is_applied_status("verified"))
        self.assertTrue(dedupe.is_terminal("waiting-user-captcha"))
        self.assertFalse(dedupe.is_submitted("blocked"))
        self.assertFalse(dedupe.is_terminal("not-a-status"))

    def test_blockers_are_terminal_but_not_applied(self):
        # A captcha/account wall must stop retries but must NOT count as applied.
        for s in ("blocked", "waiting-user-captcha", "waiting-user-credentials"):
            self.assertTrue(dedupe.is_terminal(s))
            self.assertFalse(dedupe.is_applied_status(s))


class TestQATitle(unittest.TestCase):
    def test_qa_titles_pass(self):
        for t in ("Senior QA Automation Engineer", "SDET", "Software Engineer in Test",
                  "Quality Engineer", "Test Automation Engineer"):
            self.assertTrue(dedupe.is_qa_title(t), t)

    def test_non_qa_titles_fail(self):
        for t in ("Frontend Engineer", "DevOps Engineer", "Data Scientist",
                  "Recruiter", "Security Engineer", "Design Verification Engineer"):
            self.assertFalse(dedupe.is_qa_title(t), t)


class TestCompanyIdentity(unittest.TestCase):
    def test_co_key_strips_suffix_words_and_resolves_aliases(self):
        self.assertEqual(applied_ledger.co_key("Bidgely, Inc"), applied_ledger.co_key("Bidgely"))
        self.assertEqual("hewlett packard enterprise", applied_ledger.co_key("HPE"))
        self.assertEqual("hewlett packard enterprise", applied_ledger.co_key("hp"))

    def test_company_matches_equal_and_subset_only(self):
        m = lambda a, b: applied_ledger.company_matches(  # noqa: E731
            applied_ledger.co_key(a), applied_ledger.co_key(b))
        self.assertTrue(m("ai squared", "AISquared"))
        self.assertTrue(m("amazon", "amazon web services"))
        # any-token-overlap used to make these false positives
        self.assertFalse(m("qualys", "rsa security"))
        self.assertFalse(m("dextr ai", "zilo ai"))


class TestRoleIdentity(unittest.TestCase):
    def test_role_key_collapses_sdet_spellings(self):
        a = applied_ledger.role_key("Software Development Engineer in Test")
        b = applied_ledger.role_key("SDET")
        self.assertEqual(a, b)

    def test_roles_match_prefix_and_overlap(self):
        self.assertTrue(applied_ledger.roles_match("staff sdet", "staff sdet database automation"))
        self.assertTrue(applied_ledger.roles_match("qa automation", "qa automation engineer"))


class TestDecisionLayer(unittest.TestCase):
    def test_enum_values_are_the_single_vocabulary(self):
        self.assertEqual("ready", CandidateClass.READY)
        self.assertEqual("captcha", Gate.CAPTCHA)
        self.assertEqual("account-wall", Gate.ACCOUNT_WALL)
        self.assertEqual("upload", FieldKind.UPLOAD)
        self.assertEqual("wait-code", AuthPhase.WAIT_CODE)


class TestBoundedPoll(unittest.TestCase):
    def test_until_returns_first_truthy_quickly(self):
        calls = {"n": 0}

        def cond():
            calls["n"] += 1
            return calls["n"] >= 3

        t0 = time.monotonic()
        result = ui.until(cond, timeout=2.0, interval=0.01, what="test")
        elapsed = time.monotonic() - t0
        self.assertTrue(result)
        self.assertEqual(3, calls["n"])
        self.assertLess(elapsed, 1.0, "should return the moment it is ready, not sleep")

    def test_until_times_out_and_returns_falsy(self):
        t0 = time.monotonic()
        result = ui.until(lambda: False, timeout=0.05, interval=0.01, what="never")
        elapsed = time.monotonic() - t0
        self.assertFalse(result)
        self.assertGreaterEqual(elapsed, 0.05)


class TestOcrAvailability(unittest.TestCase):
    def test_available_returns_bool_and_read_degrades_cleanly(self):
        self.assertIsInstance(ocr.available(), bool)
        if not ocr.available():
            # read() must return "" and never raise when tesseract is absent
            self.assertEqual("", ocr.read("/nonexistent.png"))


if __name__ == "__main__":
    unittest.main()
