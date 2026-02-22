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

    def test_private_memory_template_has_dual_layer_fields(self):
        template = (Path(__file__).resolve().parents[1] / "templates" / "private_memory.md").read_text(encoding="utf-8")
        self.assertIn("Entry Type:", template)
        self.assertIn("Private-Critical Reason:", template)
        self.assertIn("Disclosure State:", template)
        self.assertIn("Evidence Anchors:", template)
        self.assertIn("Raw Core:", template)
        self.assertIn("Why It Matters:", template)
        self.assertIn("Do-Not-Distort:", template)
        self.assertIn("Boundary:", template)
        self.assertIn("Quality bar:", template)
        self.assertIn("Admission gate:", template)
        self.assertIn("Routing rule:", template)
        self.assertIn("no entry cap", template)
        self.assertNotIn("Pattern/Private Thought:", template)
        self.assertNotIn("1-2 sentences max", template)
        self.assertNotIn("ASCENSION_PRIVATE_MEMORY_MAX_ENTRIES", template)


if __name__ == "__main__":
    unittest.main()
