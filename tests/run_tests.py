#!/usr/bin/env python3
"""tests/run_tests.py — run the whole test suite and print a success-rate summary.

Run:  python3 tests/run_tests.py        (or:  python3 hub.py test)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

loader = unittest.TestLoader()
suite = loader.discover(HERE, pattern="test_*.py")
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

total = result.testsRun
failed = len(result.failures) + len(result.errors)
passed = total - failed
pct = round(100.0 * passed / total) if total else 0

print("\n" + "=" * 68)
print(f"  TEST SUITE: {passed}/{total} passed · {failed} failed · SUCCESS RATE = {pct}%")
print("=" * 68)
sys.exit(1 if failed else 0)
