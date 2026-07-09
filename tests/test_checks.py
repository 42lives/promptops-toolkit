import tempfile
import unittest
import json
from pathlib import Path

from promptops_toolkit.checks import build_inventory, build_review_pack, lint_prompts
from promptops_toolkit.cli import main


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

    def test_lint_report_is_json_serializable(self) -> None:
        report = lint_prompts(Path("prompts"))
        encoded = json.dumps(report)

        self.assertIn("blog-outline.md", encoded)

    def test_lint_json_cli_returns_success_for_clean_prompts(self) -> None:
        self.assertEqual(main(["lint", "prompts", "--format", "json"]), 0)

    def test_safe_prompt_fixtures_pass_lint(self) -> None:
        report = lint_prompts(Path("examples/safe-prompts"))

        self.assertGreaterEqual(report["summary"]["files"], 1)
        self.assertEqual(report["summary"]["findings"], 0)

    def test_review_prompt_fixtures_show_private_data_findings(self) -> None:
        report = lint_prompts(Path("examples/review-prompts"))
        markdown = build_review_pack(Path("examples/review-prompts"))

        self.assertGreater(report["summary"]["findings"], 0)
        self.assertIn("Email-like personal data found", markdown)
        self.assertIn("Missing role section", markdown)


if __name__ == "__main__":
    unittest.main()
