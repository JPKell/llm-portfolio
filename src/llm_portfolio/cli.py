"""Command-line interface for portfolio evidence tooling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .audit import audit_tree
from .bundle import build_bundle
from .evidence import load_json, validate_claim_index
from .lineage import validate_lineage
from .regression import evaluate_rules


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="llm-portfolio")
    groups = parser.add_subparsers(dest="group", required=True)

    lineage_group = groups.add_parser("lineage")
    lineage_commands = lineage_group.add_subparsers(dest="command", required=True)
    lineage_validate = lineage_commands.add_parser("validate")
    lineage_validate.add_argument("document")
    lineage_validate.add_argument("--root")
    lineage_validate.add_argument("--verify-files", action="store_true")

    claims_group = groups.add_parser("claims")
    claims_commands = claims_group.add_subparsers(dest="command", required=True)
    claims_validate = claims_commands.add_parser("validate")
    claims_validate.add_argument("document")
    claims_validate.add_argument("--root")
    claims_validate.add_argument("--verify-files", action="store_true")

    regression_group = groups.add_parser("regression")
    regression_commands = regression_group.add_subparsers(dest="command", required=True)
    regression_evaluate = regression_commands.add_parser("evaluate")
    regression_evaluate.add_argument("metrics")
    regression_evaluate.add_argument("rules")

    bundle_group = groups.add_parser("bundle")
    bundle_commands = bundle_group.add_subparsers(dest="command", required=True)
    bundle_build = bundle_commands.add_parser("build")
    bundle_build.add_argument("source_root")
    bundle_build.add_argument("specification")
    bundle_build.add_argument("destination")

    release_group = groups.add_parser("release")
    release_commands = release_group.add_subparsers(dest="command", required=True)
    release_audit = release_commands.add_parser("audit")
    release_audit.add_argument("root")

    args = parser.parse_args(argv)
    if args.group == "lineage":
        errors = validate_lineage(load_json(args.document), root=args.root, verify_files=args.verify_files)
        _print({"passed": not errors, "errors": errors})
        return 0 if not errors else 1
    if args.group == "claims":
        errors = validate_claim_index(load_json(args.document), root=args.root, verify_files=args.verify_files)
        _print({"passed": not errors, "errors": errors})
        return 0 if not errors else 1
    if args.group == "regression":
        result = evaluate_rules(load_json(args.metrics), load_json(args.rules))
        _print(result)
        return 0 if result["passed"] else 1
    if args.group == "bundle":
        result = build_bundle(args.source_root, load_json(args.specification), args.destination)
        _print(result)
        return 0
    if args.group == "release":
        result = audit_tree(args.root)
        _print(result)
        return 0 if result["passed"] else 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
