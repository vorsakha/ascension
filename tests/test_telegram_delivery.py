import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import telegram_delivery as td


class TelegramDeliveryTests(unittest.TestCase):
    def create_post(self, root: Path, name: str, topic: str, body: str, ts: int) -> Path:
        path = root / f"{name}.{topic}.md"
        path.write_text(body, encoding="utf-8")
        path.touch()
        path.chmod(0o644)
        path_stat = path.stat()
        # Preserve atime while setting deterministic mtime.
        path_atime = path_stat.st_atime
        path_mtime = ts
        import os

        os.utime(path, (path_atime, path_mtime))
        return path

    def test_topic_callback_opens_paginated_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_ts = 1_700_000_000
            for i in range(7):
                self.create_post(
                    root,
                    f"post-{i+1}",
                    "ascension_journal",
                    f"Body {i+1}",
                    base_ts + i,
                )

            items = td.collect_items(root)
            action = td.resolve_callback_action("ascension:topic:journal")
            self.assertEqual(action, ("list", "ascension_journal", 1))

            payload = td.topic_list_payload(items, "ascension_journal", page=1)
            self.assertIn("Page 1/2", payload["text"])
            rows = payload["reply_markup"]["inline_keyboard"]
            self.assertEqual(len(rows[0:6]), 6)
            self.assertIn("ascension:list:ascension_journal:2", str(rows))

    def test_second_page_has_remaining_posts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_ts = 1_700_001_000
            for i in range(7):
                self.create_post(root, f"item-{i+1}", "music_log", f"Music {i+1}", base_ts + i)

            items = td.collect_items(root)
            payload = td.topic_list_payload(items, "music_log", page=2)
            self.assertIn("Page 2/2", payload["text"])
            self.assertIn("1.", payload["text"])
            rows = payload["reply_markup"]["inline_keyboard"]
            self.assertEqual(rows[0][0]["text"].split(".")[0], "1")

    def test_post_payload_returns_full_content_for_selected_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_post(root, "alpha", "ascension_x", "Line A\nLine B", 1_700_002_000)
            self.create_post(root, "beta", "ascension_x", "Line C\nLine D", 1_700_002_100)

            items = td.collect_items(root)
            selected = next(item for item in items if item.title == "Alpha")
            payload = td.post_payload(items, selected.post_id, return_page=1)

            self.assertIn("Title: Alpha", payload["text"])
            self.assertIn("Line A", payload["text"])
            self.assertIn("ascension:list:ascension_x:1", str(payload["reply_markup"]))

    def test_long_post_splits_into_messages_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            long_body = "x" * 9000
            self.create_post(root, "long", "ascension_journal", long_body, 1_700_003_000)
            items = td.collect_items(root)

            payload = td.post_payload(items, items[0].post_id, return_page=1)
            self.assertIn("messages", payload)
            self.assertGreater(len(payload["messages"]), 1)
            self.assertIn("reply_markup", payload["messages"][-1])

    def test_invalid_callback_returns_none(self):
        self.assertIsNone(td.resolve_callback_action("ascension:unknown"))
        self.assertIsNone(td.resolve_callback_action("ascension:list:music:not-a-number"))


if __name__ == "__main__":
    unittest.main()
