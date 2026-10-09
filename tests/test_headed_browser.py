"""Tests: the browser stack must ALWAYS run HEADED (visible), never headless."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestHeadedBrowser(unittest.TestCase):
    def test_server_is_headed(self):
        txt = open(os.path.join(ROOT, "runtime", "server.py"), encoding="utf-8").read()
        self.assertIn("headless=False", txt)
        self.assertNotIn("headless=True", txt)

    def test_hub_start_is_headed(self):
        txt = open(os.path.join(ROOT, "hub.py"), encoding="utf-8").read()
        self.assertIn("PLAYWRIGHT_MCP_HEADLESS", txt)
        self.assertIn('"false"', txt)  # PLAYWRIGHT_MCP_HEADLESS=false

    def test_installer_mcp_config_is_headed(self):
        txt = open(os.path.join(ROOT, "installer.py"), encoding="utf-8").read()
        self.assertIn("--headed", txt)

    def test_pi_mcp_example_is_headed(self):
        txt = open(os.path.join(ROOT, "config", "pi-mcp.json.example"), encoding="utf-8").read()
        self.assertIn("--headed", txt)

    def test_no_headless_anywhere(self):
        for root, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", "node_modules", "tests")]
            for f in files:
                if f.endswith((".py", ".md", ".json", ".sh", ".yml", ".yaml")):
                    p = os.path.join(root, f)
                    txt = open(p, encoding="utf-8", errors="replace").read()
                    # the ONLY accepted headless mention is the MCP env var set to false
                    self.assertNotIn("headless=True", txt, f"{p} has headless=True")
                    self.assertNotIn("headless: true", txt, f"{p} has headless: true")


if __name__ == "__main__":
    unittest.main()
