"""Tests for the skills graph: frontmatter validity + resolvable links."""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PATH_RE = re.compile(r"(?:`|^|\s)((?:skills|core|config|apply|find|docs|infra|runtime)/[A-Za-z0-9_./\-]+\.(?:py|md|json|sh|yml|yaml|example))\b", re.M)

RUNTIME_FILES = {
    "config/user.json", "config/profile.json", "config/profile.md",
    "config/progress.json", "config/applied_vs_not_applied.md",
    "config/product_companies_tracker.md", "config/mcp_session.json",
    "config/resume.md5", "config/targets.json",
}

NODES = ["apply", "email", "find", "learn", "ops", "resume", "searxng", "track", "verify"]


def is_runtime_file(p):
    return p in RUNTIME_FILES or (p.startswith("config/li_") and p.endswith(".json"))


class TestSkills(unittest.TestCase):
    def test_all_nodes_present(self):
        for n in NODES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, "skills", n, "SKILL.md")),
                            f"missing skills/{n}/SKILL.md")

    def test_frontmatter(self):
        for root, dirs, files in os.walk(os.path.join(ROOT, "skills")):
            for f in files:
                if f != "SKILL.md":
                    continue
                p = os.path.join(root, f)
                rel = os.path.relpath(p, ROOT)
                txt = open(p, encoding="utf-8").read()
                self.assertTrue(txt.startswith("---"), f"{rel} missing frontmatter")
                fm = txt.split("---", 2)[1] if txt.count("---") >= 2 else ""
                self.assertIn("name:", fm, f"{rel} missing name:")
                self.assertIn("description:", fm, f"{rel} missing description:")
                if rel != "skills/SKILL.md":  # master is the graph root
                    self.assertIn("parent:", fm, f"{rel} missing parent:")

    def test_links_resolve(self):
        broken = []
        for root, dirs, files in os.walk(os.path.join(ROOT, "skills")):
            for f in files:
                if not f.endswith(".md"):
                    continue
                p = os.path.join(root, f)
                rel = os.path.relpath(p, ROOT)
                txt = open(p, encoding="utf-8").read()
                for m in PATH_RE.finditer(txt):
                    link = m.group(1)
                    if is_runtime_file(link):
                        continue
                    if not os.path.exists(os.path.join(ROOT, link)):
                        broken.append(f"{rel} -> {link}")
        self.assertEqual([], broken, "broken skill links:\n  " + "\n  ".join(broken))


if __name__ == "__main__":
    unittest.main()
