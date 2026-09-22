from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from opencode_bridge import BridgeError, OpenCodeBridge


class OpenCodeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.TemporaryDirectory()
        self.project = tempfile.TemporaryDirectory()
        self.addCleanup(self.data.cleanup)
        self.addCleanup(self.project.cleanup)
        self.bridge = OpenCodeBridge(self.data.name)

    def test_configuration_is_private_and_bounded(self):
        state = self.bridge.save_config(self.project.name, self.bridge.config()["models"][0])
        self.assertEqual(state["project_dir"], self.project.name)
        config_path = Path(self.data.name) / "config.json"
        self.assertTrue(config_path.is_file())
        self.assertEqual(config_path.stat().st_mode & 0o777, 0o600)

    def test_rejects_missing_project_and_unknown_model(self):
        with self.assertRaisesRegex(BridgeError, "existing project"):
            self.bridge.save_config("/definitely/not/a/project")
        with self.assertRaisesRegex(BridgeError, "available OpenCode model"):
            self.bridge.save_config(self.project.name, "paid/unknown-model")

    def test_artifact_must_stay_inside_project(self):
        artifact = Path(self.project.name) / "result.txt"
        artifact.write_text("done", encoding="utf-8")
        run = {
            "id": 1,
            "project_dir": self.project.name,
            "artifacts": [{"path": str(artifact)}],
        }
        self.bridge.history = [run]
        self.assertEqual(self.bridge.artifact(1, 0), artifact.resolve())

        outside = Path(self.data.name) / "private.txt"
        outside.write_text("private", encoding="utf-8")
        run["artifacts"] = [{"path": str(outside)}]
        with self.assertRaisesRegex(BridgeError, "Artifact not found"):
            self.bridge.artifact(1, 0)

    @patch("opencode_bridge.shutil.which", return_value="/usr/bin/opencode")
    @patch("opencode_bridge.Path.is_file", return_value=True)
    @patch("opencode_bridge.os.access", return_value=True)
    def test_status_and_start_tools_are_separately_gated(self, _access, _file, _which):
        tools = {tool.name: tool for tool in self.bridge.tool_specs()}
        self.assertTrue(tools["opencode_start_run"].available_when("Use OpenCode to fix it"))
        self.assertTrue(tools["opencode_run_status"].required_when("What is the OpenCode progress?"))
        self.assertFalse(tools["opencode_start_run"].required_when("What is the OpenCode progress?"))


if __name__ == "__main__":
    unittest.main()
