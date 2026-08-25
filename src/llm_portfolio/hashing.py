"""Safe relative-path resolution and SHA-256 helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 hex digest for a regular file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError(f"not a regular file: {file_path}")
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_inside(root: str | Path, relative: str | Path, *, reject_symlink: bool = True) -> Path:
    """Resolve a relative path below root and reject traversal or symlinks."""
    root_path = Path(root).resolve()
    requested = Path(relative)
    if requested.is_absolute():
        raise ValueError(f"absolute path is not allowed: {requested}")
    candidate = root_path / requested
    if reject_symlink and candidate.is_symlink():
        raise ValueError(f"symlink is not allowed: {requested}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root_path):
        raise ValueError(f"path escapes root: {requested}")
    return resolved


def valid_sha256(value: object) -> bool:
    """Return True for a lowercase or uppercase 64-character hex digest."""
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)
