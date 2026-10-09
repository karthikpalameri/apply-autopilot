"""Tests for MCP configuration invariants."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestMcpConfig(unittest.TestCase):
    def test_dot_mcp_json_is_empty(self):
        p = os.path.join(ROOT, ".mcp.json")
        self.assertTrue(os.path.exists(p))
        d = json.load(open(p))
        self.assertEqual({}, d.get("mcpServers"), "project .mcp.json must stay empty")

    def test_pi_mcp_example_shape(self):
        p = os.path.join(ROOT, "config", "pi-mcp.json.example")
        d = json.load(open(p))
        cb = d["mcpServers"]["cloak-browser"]
        self.assertEqual("cloak-browser-mcp", cb["command"])
        self.assertIn("--headed", cb["args"], "must run headed, never headless")
        self.assertTrue(any("--profile-dir" == a for a in cb["args"]))

    def test_pi_web_search_example(self):
        p = os.path.join(ROOT, "config", "pi-web-search.json.example")
        d = json.load(open(p))
        self.assertIn("searxngBaseUrl", d)
        self.assertEqual("http://127.0.0.1:8080", d["searxngBaseUrl"])


if __name__ == "__main__":
    unittest.main()
