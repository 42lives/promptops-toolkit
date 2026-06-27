from __future__ import annotations

import re
import json
from pathlib import Path

VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
SECRET_PATTERN = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,})\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def lint_prompts(path: Path) -> dict[str, object]:
    root = path.expanduser().resolve()
    files = sorted(root.glob("*.md")) if root.is_dir() else [root]
    results = [_lint_file(file_path) for file_path in files if file_path.exists()]
    total_findings = sum(len(result["findings"]) for result in results)
    return {"files": results, "summary": {"files": len(results), "findings": total_findings}}


def build_inventory(path: Path) -> str:
    report = lint_prompts(path)
    lines = ["# Prompt Inventory", ""]
    for result in report["files"]:
        variables = ", ".join(result["variables"]) or "none"
        status = "ready" if not result["findings"] else "needs review"
        lines.extend([f"## {result['path']}", "", f"- Status: {status}", f"- Variables: {variables}", ""])
    if not report["files"]:
        lines.append("No prompt files found.")
    return "\n".join(lines).rstrip() + "\n"


def build_review_pack(path: Path, output_format: str = "markdown") -> str:
    report = lint_prompts(path)
    severity_counts = count_severities(report)
    review = {
        "summary": {
            "files": report["summary"]["files"],
            "findings": report["summary"]["findings"],
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "status": "ready" if report["summary"]["findings"] == 0 else "needs review",
        },
        "files": report["files"],
        "checklist": [
            "Confirm system, developer, and user sections are present.",
            "Confirm every template variable is declared.",
            "Remove secrets, real emails, customer names, account IDs, and private project details.",
            "Review prompt instructions before copying into ChatGPT, Codex, Claude, Cursor, or another AI tool.",
            "Keep reusable prompts in version control only after privacy review.",
        ],
        "privacy_boundary": "This review is local-first and does not send prompt text to external services.",
    }
    if output_format == "json":
        return json.dumps(review, indent=2, ensure_ascii=False) + "\n"
    return render_review_pack_markdown(review)


def count_severities(report: dict[str, object]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for result in report["files"]:
        for finding in result["findings"]:
            severity = finding["severity"]
            if severity in counts:
                counts[severity] += 1
    return counts


def render_review_pack_markdown(review: dict[str, object]) -> str:
    summary = review["summary"]
    checklist = review["checklist"]
    lines = [
        "# Prompt Review Pack",
        "",
        f"Status: {summary['status']}",
        f"Files: {summary['files']}",
        f"Findings: {summary['findings']}",
        f"High: {summary['high']}  Medium: {summary['medium']}  Low: {summary['low']}",
        "",
        "## Files",
        "",
    ]
    for result in review["files"]:
        status = "ready" if not result["findings"] else "needs review"
        variables = ", ".join(result["variables"]) or "none"
        lines.extend([f"### {result['path']}", "", f"- Status: {status}", f"- Variables: {variables}"])
        if result["findings"]:
            lines.append("- Findings:")
            for finding in result["findings"]:
                lines.append(f"  - [{finding['severity']}] {finding['message']}")
        lines.append("")
    lines.extend(["## Review Checklist", ""])
    for item in checklist:
        lines.append(f"- [ ] {item}")
    lines.extend(["", "## Privacy Boundary", "", str(review["privacy_boundary"])])
    return "\n".join(lines).rstrip() + "\n"


def render_lint(report: dict[str, object]) -> str:
    lines = [
        "Prompt Lint Report",
        f"Files: {report['summary']['files']}  Findings: {report['summary']['findings']}",
        "",
    ]
    for result in report["files"]:
        lines.append(f"{result['path']}")
        if not result["findings"]:
            lines.append("  PASS")
        for finding in result["findings"]:
            lines.append(f"  [{finding['severity'].upper()}] {finding['message']}")
    return "\n".join(lines) + "\n"


def _lint_file(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    declared = _declared_variables(text)
    used = sorted(set(VARIABLE_PATTERN.findall(text)))
    findings = []

    for role in ["## system", "## developer", "## user"]:
        if role not in lower:
            findings.append({"severity": "medium", "message": f"Missing role section: {role.replace('## ', '')}"})

    for variable in used:
        if variable not in declared:
            findings.append({"severity": "low", "message": f"Variable {{{variable}}} is used but not declared"})

    if SECRET_PATTERN.search(text):
        findings.append({"severity": "high", "message": "Secret-like token found"})
    if EMAIL_PATTERN.search(text):
        findings.append({"severity": "medium", "message": "Email-like personal data found"})

    return {"path": str(path), "variables": used, "findings": findings}


def _declared_variables(text: str) -> set[str]:
    for line in text.splitlines():
        if line.lower().startswith("variables:"):
            raw = line.split(":", 1)[1]
            return {part.strip() for part in raw.split(",") if part.strip()}
    return set()
