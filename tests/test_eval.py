"""Tests for eval.py — the readiness evaluator must sum to 100% and be well-formed."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import eval as evaluator  # noqa: E402


class TestEval(unittest.TestCase):
    def test_weights_sum_to_100(self):
        cases = evaluator.build_cases()
        self.assertEqual(100, sum(c[2] for c in cases),
                         "readiness weights must total 100%")

    def test_case_shape(self):
        for c in evaluator.build_cases():
            self.assertEqual(5, len(c), f"case tuple wrong shape: {c[0]}")
            cid, label, weight, fn, fix = c
            self.assertTrue(cid)
            self.assertTrue(label)
            self.assertGreater(weight, 0)
            self.assertTrue(callable(fn))
            self.assertTrue(fix)

    def test_cases_run_without_crashing(self):
        # every check function must return a (bool, str) without raising
        for c in evaluator.build_cases():
            ok, detail = c[3]()
            self.assertIsInstance(ok, bool, c[0])
            self.assertIsInstance(detail, str, c[0])


if __name__ == "__main__":
    unittest.main()
