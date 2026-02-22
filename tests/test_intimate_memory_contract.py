import unittest
from pathlib import Path


class IntimateMemoryContractTests(unittest.TestCase):
    def test_intimate_memory_template_has_dual_layer_fields(self):
        template = (Path(__file__).resolve().parents[1] / "templates" / "intimate_memory.md").read_text(encoding="utf-8")
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
        self.assertIn("intimate", template)
        self.assertNotIn("Entry Type:", template)
        self.assertIn("no entry cap", template)
        self.assertNotIn("Pattern/Private Thought:", template)
        self.assertNotIn("1-2 sentences max", template)


if __name__ == "__main__":
    unittest.main()
