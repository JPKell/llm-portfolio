"""Claim-to-evidence validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .hashing import resolve_inside, sha256_file, valid_sha256

CLAIM_STATUSES = {"observed", "demonstration", "planned", "unsupported", "inconclusive", "retracted"}


def load_json(path: str | Path) -> Any:
    """Load UTF-8 JSON from path."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_claim_index(document: Any, *, root: str | Path | None = None, verify_files: bool = False) -> list[str]:
    """Validate claim statuses, evidence references, and optional hashes."""
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["claim index must be an object"]
    if document.get("schema") != "llm-portfolio-claims-v1":
        errors.append("schema must be llm-portfolio-claims-v1")
    claims = document.get("claims")
    if not isinstance(claims, list):
        return errors + ["claims must be a list"]
    root_path = Path(root).resolve() if root is not None else None
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        label = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} must be an object")
            continue
        claim_id = claim.get("id")
        status = claim.get("status")
        evidence = claim.get("evidence", [])
        if not isinstance(claim_id, str) or not claim_id:
            errors.append(f"{label}.id is required")
        elif claim_id in seen:
            errors.append(f"duplicate claim id: {claim_id}")
        else:
            seen.add(claim_id)
        if status not in CLAIM_STATUSES:
            errors.append(f"{label}.status must be one of {sorted(CLAIM_STATUSES)}")
        if not isinstance(claim.get("statement"), str) or not claim.get("statement"):
            errors.append(f"{label}.statement is required")
        if not isinstance(evidence, list):
            errors.append(f"{label}.evidence must be a list")
            evidence = []
        if status in {"observed", "demonstration", "inconclusive", "retracted"} and not evidence:
            errors.append(f"{label}.evidence is required for status {status}")
        if status in {"unsupported", "retracted", "inconclusive"} and not claim.get("reason"):
            errors.append(f"{label}.reason is required for status {status}")
        for evidence_index, reference in enumerate(evidence):
            ref_label = f"{label}.evidence[{evidence_index}]"
            if not isinstance(reference, dict):
                errors.append(f"{ref_label} must be an object")
                continue
            path = reference.get("path")
            digest = reference.get("sha256")
            if not isinstance(path, str) or not path:
                errors.append(f"{ref_label}.path is required")
                continue
            if not valid_sha256(digest):
                errors.append(f"{ref_label}.sha256 must be a 64-character hex digest")
                continue
            if verify_files and root_path is not None:
                try:
                    resolved = resolve_inside(root_path, path)
                except ValueError as exc:
                    errors.append(f"{ref_label}: {exc}")
                    continue
                if not resolved.is_file():
                    errors.append(f"{ref_label} file does not exist: {path}")
                elif sha256_file(resolved) != digest.lower():
                    errors.append(f"{ref_label} hash mismatch: {path}")
    return errors
