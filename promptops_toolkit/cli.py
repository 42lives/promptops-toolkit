from __future__ import annotations

import argparse
from pathlib import Path

from .checks import build_inventory, build_review_pack, lint_prompts, render_lint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="promptops-toolkit", description="Local-first prompt workflow checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint = subparsers.add_parser("lint", help="Lint prompt markdown files.")
    lint.add_argument("path", type=Path)

    inventory = subparsers.add_parser("inventory", help="Generate a prompt inventory.")
    inventory.add_argument("path", type=Path)

    review_pack = subparsers.add_parser("review-pack", help="Generate a prompt review package.")
    review_pack.add_argument("path", type=Path)
    review_pack.add_argument("--format", choices=["markdown", "json"], default="markdown")

    args = parser.parse_args(argv)

    if args.command == "lint":
        report = lint_prompts(args.path)
        print(render_lint(report))
        return 1 if report["summary"]["findings"] else 0

    if args.command == "inventory":
        print(build_inventory(args.path))
        return 0

    if args.command == "review-pack":
        print(build_review_pack(args.path, args.format))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
