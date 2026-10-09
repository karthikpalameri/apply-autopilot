"""Unit tests for onboarding.py logic (non-interactive parts)."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import onboarding as ob  # noqa: E402


class TestOnboarding(unittest.TestCase):
    def test_generate_artifacts(self):
        cfg = {"full_name": "Jane Doe", "email": "jane@example.com", "phone": "+91 00000 00000",
               "location": "Bengaluru", "current_role": "Senior QA Automation Engineer",
               "current_company": "Acme", "years_exp": 8}
        profile = {"skills": {"languages": ["Java", "Python"],
                              "automation_frameworks": ["Selenium", "Playwright"],
                              "api_testing": ["Postman"], "cicd": ["Jenkins"],
                              "cloud": ["AWS"], "databases": ["MySQL"],
                              "tools_other": ["Agile"], "domains": ["Fintech"]},
                   "achievements": ["reduced regression time 40%"],
                   "certifications": ["ISTQB"], "years_exp": 8}
        ob.generate_artifacts(cfg, profile)
        self.assertIn("Senior QA Automation Engineer", profile["headline"])
        self.assertTrue(profile["key_skills"])
        self.assertLessEqual(len(profile["key_skills"]), 249)
        self.assertIn("application", profile["cold_email"]["subject"].lower())
        self.assertIn("Jane Doe", profile["cold_email"]["body"])

    def test_write_profile_md(self):
        cfg = {"full_name": "Jane Doe", "email": "jane@example.com", "phone": "+91",
               "location": "Bengaluru", "current_role": "QA Engineer"}
        profile = {"headline": "QA Engineer", "summary": "s", "key_skills": "Java",
                   "strengths": "s", "weakness": "w", "why_leave": "l", "why_hire": "h",
                   "salary_answer": "<expected CTC>", "achievements": ["a"],
                   "certifications": ["ISTQB"], "skills": {"languages": ["Java"]},
                   "cold_email": {"subject": "s", "body": "b"}}
        with tempfile.TemporaryDirectory() as d:
            ob.PROFILE_MD = os.path.join(d, "profile.md")
            ob.write_profile_md(cfg, profile)
            self.assertTrue(os.path.exists(ob.PROFILE_MD))
            txt = open(ob.PROFILE_MD, encoding="utf-8").read()
            self.assertIn("QA Engineer", txt)
            self.assertIn("Java", txt)

    def test_flat_review_items(self):
        data = {"full_name": "Jane Doe", "email": "jane@example.com", "phone": "+91",
                "location": "Bengaluru", "current_role": "QA", "years_exp": 8,
                "linkedin_url": "x", "github": "y", "summary": "s",
                "education": {"degree": "B.E", "school": "U", "year": "2017"}}
        items = ob._flat_review_items(data)
        keys = [k for k, _, _ in items]
        self.assertIn("full_name", keys)
        self.assertIn("degree", keys)
        self.assertIn("edu_year", keys)


if __name__ == "__main__":
    unittest.main()
