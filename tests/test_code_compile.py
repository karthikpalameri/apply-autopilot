"""Tests: every .py file in the repo compiles."""
import os
import py_compile
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "logs", "temp",
             "runtime/mcp-session", "runtime/session", "runtime/lseg-mcp-probe"}


class TestCodeCompile(unittest.TestCase):
    def test_all_py_compile(self):
        failures = []
        for root, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith("__pycache__")]
            for f in files:
                if f.endswith(".py"):
                    p = os.path.join(root, f)
                    try:
                        py_compile.compile(p, doraise=True)
                    except Exception as e:
                        failures.append(f"{os.path.relpath(p, ROOT)}: {e}")
        self.assertEqual([], failures, "compile failures:\n  " + "\n  ".join(failures))


if __name__ == "__main__":
    unittest.main()
