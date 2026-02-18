import json
import unittest
from pathlib import Path


class SkillManifestTests(unittest.TestCase):
    def test_skill_manifest_has_openclaw_telegram_wiring(self):
        manifest_path = Path(__file__).resolve().parents[1] / "skill.json"
        self.assertTrue(manifest_path.exists(), "skill.json must exist at repository root")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("name"), "ascension")

        telegram_commands = manifest.get("telegramCommands")
        self.assertIsInstance(telegram_commands, list)
        self.assertGreaterEqual(len(telegram_commands), 1)

        command = telegram_commands[0]
        self.assertEqual(command.get("command"), "ascension")
        self.assertEqual(command.get("handler"), "scripts/telegram_delivery.py")
        self.assertEqual(command.get("args"), ["menu", "--format", "json"])

        callback_handlers = manifest.get("callbackHandlers")
        self.assertIsInstance(callback_handlers, list)
        self.assertGreaterEqual(len(callback_handlers), 1)

        callback = callback_handlers[0]
        self.assertEqual(callback.get("prefix"), "ascension:")
        self.assertEqual(callback.get("handler"), "scripts/telegram_delivery.py")
        self.assertEqual(
            callback.get("args"),
            ["callback", "--data", "{callback_data}", "--format", "json"],
        )


if __name__ == "__main__":
    unittest.main()
