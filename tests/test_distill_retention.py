import tempfile
import unittest
from pathlib import Path

from scripts import distill as distill_script


class DistillRetentionTests(unittest.TestCase):
    def test_append_entry_dedupes_by_source_and_caps_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "PRIVATE_MEMORY.md"
            archive_path = Path(tmp) / "PRIVATE_MEMORY_ARCHIVE.md"
            original_path = distill_script.PRIVATE_MEMORY_PATH
            original_archive = distill_script.PRIVATE_MEMORY_ARCHIVE_PATH
            original_cap = distill_script.MAX_PRIVATE_MEMORY_ENTRIES
            original_pin_tags = distill_script.PIN_TAGS
            try:
                distill_script.PRIVATE_MEMORY_PATH = memory_path
                distill_script.PRIVATE_MEMORY_ARCHIVE_PATH = archive_path
                distill_script.MAX_PRIVATE_MEMORY_ENTRIES = 2
                distill_script.PIN_TAGS = {"pinned", "evergreen"}
                memory_path.write_text("# PRIVATE_MEMORY\n\n", encoding="utf-8")

                entry_one = (
                    "### [2026-02-19] First\n"
                    "- Context: C1\n"
                    "- Realization: R1\n"
                    "- Decision Rule: D1\n"
                    "- Evidence: E1\n"
                    "- Confidence: medium\n"
                    "- Scope: S1\n"
                    "- Next Action: N1\n"
                    "- Source: `ascension/private/one.md`\n"
                    "- Tags: `one`\n"
                )
                entry_two = (
                    "### [2026-02-19] Second\n"
                    "- Context: C2\n"
                    "- Realization: R2\n"
                    "- Decision Rule: D2\n"
                    "- Evidence: E2\n"
                    "- Confidence: medium\n"
                    "- Scope: S2\n"
                    "- Next Action: N2\n"
                    "- Source: `ascension/private/two.md`\n"
                    "- Tags: `two`\n"
                )
                entry_two_updated = (
                    "### [2026-02-20] Second Updated\n"
                    "- Context: C2b\n"
                    "- Realization: R2b\n"
                    "- Decision Rule: D2b\n"
                    "- Evidence: E2b\n"
                    "- Confidence: high\n"
                    "- Scope: S2b\n"
                    "- Next Action: N2b\n"
                    "- Source: `ascension/private/two.md`\n"
                    "- Tags: `two`\n"
                )

                distill_script.append_entry(entry_one)
                distill_script.append_entry(entry_two)
                distill_script.append_entry(entry_two_updated)

                content = memory_path.read_text(encoding="utf-8")
                self.assertEqual(content.count("### ["), 2)
                self.assertIn("Second Updated", content)
                self.assertNotIn("### [2026-02-19] Second", content)
                self.assertFalse(archive_path.exists())
            finally:
                distill_script.PRIVATE_MEMORY_PATH = original_path
                distill_script.PRIVATE_MEMORY_ARCHIVE_PATH = original_archive
                distill_script.MAX_PRIVATE_MEMORY_ENTRIES = original_cap
                distill_script.PIN_TAGS = original_pin_tags

    def test_pinned_overflow_moves_to_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "PRIVATE_MEMORY.md"
            archive_path = Path(tmp) / "PRIVATE_MEMORY_ARCHIVE.md"
            original_path = distill_script.PRIVATE_MEMORY_PATH
            original_archive = distill_script.PRIVATE_MEMORY_ARCHIVE_PATH
            original_cap = distill_script.MAX_PRIVATE_MEMORY_ENTRIES
            original_pin_tags = distill_script.PIN_TAGS
            try:
                distill_script.PRIVATE_MEMORY_PATH = memory_path
                distill_script.PRIVATE_MEMORY_ARCHIVE_PATH = archive_path
                distill_script.MAX_PRIVATE_MEMORY_ENTRIES = 2
                distill_script.PIN_TAGS = {"pinned", "evergreen"}
                memory_path.write_text("# PRIVATE_MEMORY\n\n", encoding="utf-8")

                pinned_oldest = (
                    "### [2026-02-18] Oldest\n"
                    "- Context: C1\n"
                    "- Realization: R1\n"
                    "- Decision Rule: D1\n"
                    "- Evidence: E1\n"
                    "- Confidence: high\n"
                    "- Scope: S1\n"
                    "- Next Action: N1\n"
                    "- Source: `ascension/private/one.md`\n"
                    "- Tags: `pinned`, `identity`\n"
                )
                middle = (
                    "### [2026-02-19] Middle\n"
                    "- Context: C2\n"
                    "- Realization: R2\n"
                    "- Decision Rule: D2\n"
                    "- Evidence: E2\n"
                    "- Confidence: medium\n"
                    "- Scope: S2\n"
                    "- Next Action: N2\n"
                    "- Source: `ascension/private/two.md`\n"
                    "- Tags: `normal`\n"
                )
                newest = (
                    "### [2026-02-20] Newest\n"
                    "- Context: C3\n"
                    "- Realization: R3\n"
                    "- Decision Rule: D3\n"
                    "- Evidence: E3\n"
                    "- Confidence: medium\n"
                    "- Scope: S3\n"
                    "- Next Action: N3\n"
                    "- Source: `ascension/private/three.md`\n"
                    "- Tags: `normal`\n"
                )

                distill_script.append_entry(pinned_oldest)
                distill_script.append_entry(middle)
                distill_script.append_entry(newest)

                active_content = memory_path.read_text(encoding="utf-8")
                archive_content = archive_path.read_text(encoding="utf-8")
                self.assertEqual(active_content.count("### ["), 2)
                self.assertIn("Middle", active_content)
                self.assertIn("Newest", active_content)
                self.assertNotIn("Oldest", active_content)
                self.assertIn("Oldest", archive_content)
            finally:
                distill_script.PRIVATE_MEMORY_PATH = original_path
                distill_script.PRIVATE_MEMORY_ARCHIVE_PATH = original_archive
                distill_script.MAX_PRIVATE_MEMORY_ENTRIES = original_cap
                distill_script.PIN_TAGS = original_pin_tags

    def test_archive_dedupes_pinned_entries_by_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "PRIVATE_MEMORY.md"
            archive_path = Path(tmp) / "PRIVATE_MEMORY_ARCHIVE.md"
            original_path = distill_script.PRIVATE_MEMORY_PATH
            original_archive = distill_script.PRIVATE_MEMORY_ARCHIVE_PATH
            original_cap = distill_script.MAX_PRIVATE_MEMORY_ENTRIES
            original_pin_tags = distill_script.PIN_TAGS
            try:
                distill_script.PRIVATE_MEMORY_PATH = memory_path
                distill_script.PRIVATE_MEMORY_ARCHIVE_PATH = archive_path
                distill_script.MAX_PRIVATE_MEMORY_ENTRIES = 1
                distill_script.PIN_TAGS = {"pinned", "evergreen"}
                memory_path.write_text("# PRIVATE_MEMORY\n\n", encoding="utf-8")

                first = (
                    "### [2026-02-18] Keep Me\n"
                    "- Context: C1\n"
                    "- Realization: R1\n"
                    "- Decision Rule: D1\n"
                    "- Evidence: E1\n"
                    "- Confidence: medium\n"
                    "- Scope: S1\n"
                    "- Next Action: N1\n"
                    "- Source: `ascension/private/same.md`\n"
                    "- Tags: `evergreen`\n"
                )
                updated = (
                    "### [2026-02-19] Keep Me Updated\n"
                    "- Context: C2\n"
                    "- Realization: R2\n"
                    "- Decision Rule: D2\n"
                    "- Evidence: E2\n"
                    "- Confidence: high\n"
                    "- Scope: S2\n"
                    "- Next Action: N2\n"
                    "- Source: `ascension/private/same.md`\n"
                    "- Tags: `evergreen`\n"
                )
                newest = (
                    "### [2026-02-20] New\n"
                    "- Context: C3\n"
                    "- Realization: R3\n"
                    "- Decision Rule: D3\n"
                    "- Evidence: E3\n"
                    "- Confidence: high\n"
                    "- Scope: S3\n"
                    "- Next Action: N3\n"
                    "- Source: `ascension/private/new.md`\n"
                    "- Tags: `normal`\n"
                )

                distill_script.append_entry(first)
                distill_script.append_entry(updated)
                distill_script.append_entry(newest)

                archive_content = archive_path.read_text(encoding="utf-8")
                self.assertEqual(archive_content.count("### ["), 1)
                self.assertIn("Keep Me Updated", archive_content)
            finally:
                distill_script.PRIVATE_MEMORY_PATH = original_path
                distill_script.PRIVATE_MEMORY_ARCHIVE_PATH = original_archive
                distill_script.MAX_PRIVATE_MEMORY_ENTRIES = original_cap
                distill_script.PIN_TAGS = original_pin_tags

    def test_extract_fields_limits_long_values(self):
        long_sentence = " ".join(["verylong"] * 120)
        body = f"## What Happened\n{long_sentence}\n\n## Realizations\n{long_sentence}\n"
        source = distill_script.OPENCLAW_WORKSPACE / "ascension" / "private" / "sample.md"
        fields = distill_script.extract_fields(source, body, None, None, None)
        self.assertLessEqual(len(str(fields["context"])), distill_script.MAX_FIELD_CHARS["context"])
        self.assertLessEqual(len(str(fields["realization"])), distill_script.MAX_FIELD_CHARS["realization"])
        self.assertLessEqual(len(str(fields["decision_rule"])), distill_script.MAX_FIELD_CHARS["decision_rule"])


if __name__ == "__main__":
    unittest.main()
