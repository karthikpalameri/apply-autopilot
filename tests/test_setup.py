"""Unit tests for setup.py helpers."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import setup  # noqa: E402


class TestSetup(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual("Senior_QA_Engineer", setup.slugify("Senior QA Engineer"))
        self.assertEqual("Jane", setup.slugify("Jane!!"))

    def test_derive_resume_filename(self):
        self.assertEqual(
            "Jane_Doe_Senior_QA_Automation_Engineer.pdf",
            setup.derive_resume_filename("Jane Doe", "Senior QA Automation Engineer"))

    def test_derive_single_name(self):
        self.assertEqual("Jane_SDET.pdf", setup.derive_resume_filename("Jane", "SDET"))


if __name__ == "__main__":
    unittest.main()
