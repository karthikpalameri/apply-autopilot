"""Unit tests for resume_parser.py (parsing logic)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import resume_parser as rp  # noqa: E402

SAMPLE = """JANE DOE
Senior QA Automation Engineer
Bengaluru, Karnataka, India | +91 98765 43210 | jane.doe@example.com
linkedin.com/in/janedoe | github.com/janedoe

SUMMARY
Senior QA Automation Engineer with 8+ years experience in Selenium, Playwright, Java, Python, API testing, CI/CD.

EXPERIENCE
Acme Corp — Senior QA Engineer (2021 - Present)
- Automated 300+ test cases using Selenium and Playwright, reduced regression time by 40%

EDUCATION
B.E. Computer Science, Example University, 2017

SKILLS
Java, Python, Selenium, Playwright, Postman, Jenkins, AWS, MySQL, Agile
"""


class TestResumeParser(unittest.TestCase):
    def setUp(self):
        self.d = rp.parse_text(SAMPLE)

    def test_email(self):
        self.assertEqual("jane.doe@example.com", self.d["email"])

    def test_phone(self):
        self.assertEqual("+91 98765 43210", self.d["phone"])

    def test_links(self):
        self.assertEqual("linkedin.com/in/janedoe", self.d["linkedin_url"])
        self.assertEqual("github.com/janedoe", self.d["github"])

    def test_name_allcaps_header(self):
        self.assertEqual("Jane Doe", self.d["full_name"])

    def test_location(self):
        self.assertEqual("Bengaluru", self.d["location"])

    def test_role(self):
        self.assertIn("QA", self.d["current_role"])

    def test_years(self):
        self.assertEqual(8, self.d["years_exp"])

    def test_education(self):
        self.assertEqual("B.E", self.d["education"]["degree"])
        self.assertEqual("2017", self.d["education"]["year"])

    def test_skills_detected(self):
        langs = self.d["skills"]["languages"]
        self.assertIn("Java", langs)
        self.assertIn("Python", langs)
        self.assertIn("Selenium", self.d["skills"]["automation_frameworks"])
        self.assertIn("Postman", self.d["skills"]["api_testing"])
        self.assertIn("Jenkins", self.d["skills"]["cicd"])
        self.assertIn("AWS", self.d["skills"]["cloud"])

    def test_achievements(self):
        self.assertTrue(any("40%" in a for a in self.d["achievements"]))

    def test_name_from_filename(self):
        self.assertEqual("Jane Doe", rp._name_from_filename("/tmp/Jane_Doe_Resume.pdf"))


if __name__ == "__main__":
    unittest.main()
