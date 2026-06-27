import tempfile
import unittest
from pathlib import Path

from promptops_toolkit.checks import build_inventory, build_review_pack, lint_prompts


class PromptChecksTest(unittest.TestCase):
    def test_clean_prompt_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt = Path(tmpdir) / "demo.md"
            prompt.write_text(
                "variables: topic\n\n## System\nA\n\n## Developer\nB\n\n## User\nWrite about {topic}.\n",
                encoding="utf-8",
            )
            report = lint_prompts(prompt)

        self.assertEqual(report["summary"]["findings"], 0)

    def test_missing_sections_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt = Path(tmpdir) / "demo.md"
            prompt.write_text("## User\nWrite about {topic}.\n", encoding="utf-8")
            report = lint_prompts(prompt)

        self.assertGreater(report["summary"]["findings"], 0)

    def test_inventory_lists_prompt(self) -> None:
        inventory = build_inventory(Path("prompts"))

        self.assertIn("blog-outline.md", inventory)

    def test_review_pack_summarizes_findings_and_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt = Path(tmpdir) / "unsafe.md"
            prompt.write_text(
                "## User\nEmail test@example.com about {topic}.\n",
                encoding="utf-8",
            )
            markdown = build_review_pack(prompt)
            json_output = build_review_pack(prompt, "json")

        self.assertIn("# Prompt Review Pack", markdown)
        self.assertIn("Status: needs review", markdown)
        self.assertIn("Email-like personal data found", markdown)
        self.assertIn("Review Checklist", markdown)
        self.assertIn('"status": "needs review"', json_output)


if __name__ == "__main__":
    unittest.main()
