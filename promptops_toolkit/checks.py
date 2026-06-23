from __future__ import annotations

import re
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
