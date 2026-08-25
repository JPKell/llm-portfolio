"""Conservative public-release audit for the portfolio tree."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

BLOCKED_SUFFIXES = {".safetensors", ".gguf", ".pt", ".pth", ".ckpt", ".onnx", ".pem", ".key"}
REQUIRED_FILES = {"README.md", "LICENSE", "SECURITY.md", "CITATION.cff", "THIRD_PARTY.md", "pyproject.toml", ".gitignore"}
TEXT_SUFFIXES = {"", ".md", ".txt", ".json", ".jsonl", ".toml", ".yaml", ".yml", ".py", ".cff"}


def _patterns() -> list[tuple[str, re.Pattern[str]]]:
    return [
        ("aws-access-key", re.compile("AK" + "IA[0-9A-Z]{16}")),
        ("github-token", re.compile("gh" + "[pousr]_[A-Za-z0-9]{20,}")),
        ("huggingface-token", re.compile("hf" + "_[A-Za-z0-9]{20,}")),
        ("private-key", re.compile("-----BEGIN " + "(?:RSA |OPENSSH |EC )?PRIVATE KEY-----")),
        ("private-home-path", re.compile("/ho" + "me/[A-Za-z0-9._-]+/")),
        ("private-mount-path", re.compile("/m" + "nt/(?:ssd|nvme|hdd)/")),
        ("unresolved-placeholder", re.compile("QUALIFICATION" + "_REQUIRED")),
    ]


def audit_tree(root: str | Path, *, max_file_bytes: int = 10 * 1024 * 1024) -> dict[str, Any]:
    """Return release-blocking and warning findings without modifying the tree."""
    base = Path(root).resolve()
    findings: list[dict[str, str]] = []
    for required in sorted(REQUIRED_FILES):
        if not (base / required).is_file():
            findings.append({"severity": "block", "kind": "missing-required-file", "path": required})
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(base).as_posix()
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            findings.append({"severity": "block", "kind": "symlink", "path": relative})
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            findings.append({"severity": "block", "kind": "blocked-artifact-type", "path": relative})
        if path.stat().st_size > max_file_bytes:
            findings.append({"severity": "block", "kind": "oversized-file", "path": relative})
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for kind, pattern in _patterns():
            if pattern.search(body):
                findings.append({"severity": "block", "kind": kind, "path": relative})
    ignore_path = base / ".gitignore"
    if ignore_path.is_file():
        ignore = ignore_path.read_text(encoding="utf-8")
        for pattern in ("*.safetensors", "*.gguf", ".env"):
            if pattern not in ignore:
                findings.append({"severity": "warn", "kind": "gitignore-gap", "path": pattern})
    return {
        "schema": "llm-portfolio-release-audit-v1",
        "passed": not any(item["severity"] == "block" for item in findings),
        "findings": findings,
    }
