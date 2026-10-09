"""Unit tests for installer.py logic (no actual installs)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import installer  # noqa: E402


class TestInstaller(unittest.TestCase):
    def test_pi_manifest(self):
        self.assertEqual(["npm:pi-mcp-adapter", "npm:pi-web-access", "npm:context-mode"],
                         installer.PI_PACKAGES)
        self.assertIn("ctx-search", installer.PI_SKILLS)
        self.assertIn("context-mode", installer.PI_SKILLS)
        self.assertEqual(8, len(installer.PI_SKILLS))
        self.assertIn("context-mode:build/adapters/pi/extension.js", installer.PI_EXTENSIONS)
        self.assertIn("pi-mcp-adapter", installer.PI_EXTENSIONS)
        self.assertIn("pi-web-access:dist", installer.PI_EXTENSIONS)

    def test_install_commands_shape(self):
        for tool in ("node", "git", "tesseract", "docker", "pi"):
            cmds = installer.install_commands(tool)
            # 'pi' always has a command; system tools depend on OS + package manager
            if tool == "pi":
                self.assertIsNotNone(cmds)
            if cmds is not None:
                self.assertIsInstance(cmds, list)
                for c in cmds:
                    self.assertIsInstance(c, list)
                    self.assertTrue(all(isinstance(x, str) for x in c))

    def test_pkg_manager_detected(self):
        # on any supported OS, pkg_manager() returns a string or None (never throws)
        pm = installer.pkg_manager()
        self.assertIn(pm, (None, "brew", "apt-get", "dnf", "pacman", "zypper",
                           "winget", "choco", "scoop"))


if __name__ == "__main__":
    unittest.main()
