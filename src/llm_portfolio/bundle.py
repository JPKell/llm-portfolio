"""Build a content-addressed reproduction bundle from an allowlisted file set."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

from .hashing import resolve_inside, sha256_file


def build_bundle(
    source_root: str | Path,
    specification: Any,
    destination: str | Path,
    *,
    max_file_bytes: int = 10 * 1024 * 1024,
) -> dict[str, Any]:
    """Copy explicitly included regular files and write hashes/manifest."""
    root = Path(source_root).resolve()
    output = Path(destination).resolve()
    if not isinstance(specification, dict) or specification.get("schema") != "llm-portfolio-bundle-v1":
        raise ValueError("invalid bundle specification schema")
    includes = specification.get("include")
    if not isinstance(includes, list) or not includes or not all(isinstance(item, str) for item in includes):
        raise ValueError("include must be a nonempty string list")
    if output == root or output.is_relative_to(root):
        raise ValueError("destination must be outside source root")
    if output.exists() and any(output.iterdir()):
        raise ValueError("destination must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for relative in sorted(set(includes)):
        source = resolve_inside(root, relative)
        if not source.is_file():
            raise ValueError(f"included path is not a regular file: {relative}")
        size = source.stat().st_size
        if size > max_file_bytes:
            raise ValueError(f"included file exceeds size limit: {relative}")
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        records.append({"path": relative, "bytes": size, "sha256": sha256_file(target)})
    manifest = {
        "schema": "llm-portfolio-bundle-manifest-v1",
        "bundle_id": specification.get("bundle_id"),
        "files": records,
    }
    manifest_path = output / "bundle-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksums = "".join(f"{item['sha256']}  {item['path']}\n" for item in records)
    (output / "checksums.sha256").write_text(checksums, encoding="utf-8")
    return manifest
