import unittest
from pathlib import Path


class PrivateMemoryContractTests(unittest.TestCase):
    def test_distill_script_removed(self):
        distill_path = Path(__file__).resolve().parents[1] / "scripts" / "distill.py"
        self.assertFalse(distill_path.exists(), "scripts/distill.py should be removed")

    def test_no_distill_reference_in_docs(self):
        root = Path(__file__).resolve().parents[1]
        for rel in ("README.md", "SKILL.md", "agents/openai.yaml"):
            text = (root / rel).read_text(encoding="utf-8")
            self.assertNotIn("distill.py", text)
            self.assertNotIn("skill:ascension/distill", text)

    def test_private_memory_template_has_anchor_and_disclosure_fields(self):
        template = (Path(__file__).resolve().parents[1] / "templates" / "private_memory.md").read_text(encoding="utf-8")
        self.assertIn("Entry Type:", template)
        self.assertIn("Disclosure State:", template)
        self.assertIn("Evidence Anchors:", template)
        self.assertIn("Pattern/Private Thought:", template)


if __name__ == "__main__":
    unittest.main()
