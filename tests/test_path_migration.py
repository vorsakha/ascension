import unittest
from unittest.mock import patch
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import publish as publish_script
from scripts import new_post as new_post_script
from scripts import telegram_delivery as telegram_script


class PathMigrationTests(unittest.TestCase):
    def test_module_constants_follow_resolved_workspace(self):
        workspace = new_post_script.resolve_workspace_root()
        self.assertEqual(new_post_script.OPENCLAW_WORKSPACE, new_post_script.resolve_workspace_root())
        self.assertEqual(new_post_script.ASCENSION_CONTENT_ROOT, workspace / "ascension")
        self.assertEqual(telegram_script.DEFAULT_PUBLIC_ROOT, workspace / "ascension" / "public")

    def test_workspace_priority_ascension_then_openclaw(self):
        with patch.dict(os.environ, {"ASCENSION_WORKSPACE": "/tmp/ascension_ws", "OPENCLAW_WORKSPACE": "/tmp/openclaw_ws"}, clear=False):
            self.assertEqual(new_post_script.resolve_workspace_root(), Path("/tmp/ascension_ws").resolve())
            self.assertEqual(publish_script.resolve_workspace_root(), Path("/tmp/ascension_ws").resolve())
            self.assertEqual(telegram_script.resolve_workspace_root(), Path("/tmp/ascension_ws").resolve())

    def test_workspace_falls_back_to_openclaw_env(self):
        with patch.dict(os.environ, {"OPENCLAW_WORKSPACE": "/tmp/openclaw_ws"}, clear=True):
            self.assertEqual(new_post_script.resolve_workspace_root(), Path("/tmp/openclaw_ws").resolve())
            self.assertEqual(publish_script.resolve_workspace_root(), Path("/tmp/openclaw_ws").resolve())
            self.assertEqual(telegram_script.resolve_workspace_root(), Path("/tmp/openclaw_ws").resolve())

    def test_publish_content_paths_fail_public_root_check(self):
        resolved = publish_script.resolve_input_path("content/public/example.md", kind="public")
        with self.assertRaises(SystemExit) as exc:
            publish_script.ensure_under(resolved, publish_script.PUBLIC_ROOT, "public_file")
        self.assertIn("public_file must be under", str(exc.exception))

    def test_publish_shortcuts_map_to_openclaw_tree(self):
        private_path = publish_script.resolve_input_path("private/a.md", kind="private")
        public_path = publish_script.resolve_input_path("public/b.md", kind="public")
        self.assertEqual(private_path, publish_script.PRIVATE_ROOT / "a.md")
        self.assertEqual(public_path, publish_script.PUBLIC_ROOT / "b.md")


if __name__ == "__main__":
    unittest.main()
