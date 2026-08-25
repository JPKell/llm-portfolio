"""Validate immutable artifact/transformation lineage documents."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from .hashing import resolve_inside, sha256_file, valid_sha256

NODE_STATUSES = {"planned", "completed", "unsupported"}
EDGE_STATUSES = {"planned", "completed", "unsupported"}


def _verify_reference(reference: Any, root: Path, label: str, errors: list[str]) -> None:
    if not isinstance(reference, dict):
        errors.append(f"{label} must be an object")
        return
    path = reference.get("path")
    digest = reference.get("sha256")
    if not isinstance(path, str) or not path:
        errors.append(f"{label}.path is required")
        return
    if not valid_sha256(digest):
        errors.append(f"{label}.sha256 must be a 64-character hex digest")
        return
    try:
        resolved = resolve_inside(root, path)
    except ValueError as exc:
        errors.append(f"{label}: {exc}")
        return
    if not resolved.is_file():
        errors.append(f"{label} file does not exist: {path}")
    elif sha256_file(resolved) != digest.lower():
        errors.append(f"{label} hash mismatch: {path}")


def validate_lineage(document: Any, *, root: str | Path | None = None, verify_files: bool = False) -> list[str]:
    """Return validation errors; an empty list means the document is valid."""
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["lineage document must be an object"]
    if document.get("schema") != "llm-portfolio-lineage-v1":
        errors.append("schema must be llm-portfolio-lineage-v1")
    nodes = document.get("nodes")
    edges = document.get("edges")
    if not isinstance(nodes, list) or not nodes:
        return errors + ["nodes must be a nonempty list"]
    if not isinstance(edges, list):
        return errors + ["edges must be a list"]

    root_path = Path(root).resolve() if root is not None else None
    node_ids: set[str] = set()
    statuses: dict[str, str] = {}
    incoming: dict[str, int] = defaultdict(int)
    adjacency: dict[str, set[str]] = defaultdict(set)

    for index, node in enumerate(nodes):
        label = f"nodes[{index}]"
        if not isinstance(node, dict):
            errors.append(f"{label} must be an object")
            continue
        node_id = node.get("id")
        status = node.get("status")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"{label}.id is required")
            continue
        if node_id in node_ids:
            errors.append(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
        statuses[node_id] = status
        if not isinstance(node.get("kind"), str) or not node.get("kind"):
            errors.append(f"{label}.kind is required")
        if status not in NODE_STATUSES:
            errors.append(f"{label}.status must be one of {sorted(NODE_STATUSES)}")
        if status == "unsupported" and not node.get("reason"):
            errors.append(f"{label}.reason is required when unsupported")
        if status == "completed":
            artifact = node.get("artifact")
            if not isinstance(artifact, dict) or not valid_sha256(artifact.get("sha256")):
                errors.append(f"{label}.artifact with SHA-256 is required when completed")
            elif verify_files and root_path is not None:
                _verify_reference(artifact, root_path, f"{label}.artifact", errors)

    edge_ids: set[str] = set()
    for index, edge in enumerate(edges):
        label = f"edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{label} must be an object")
            continue
        edge_id = edge.get("id")
        inputs = edge.get("inputs")
        output = edge.get("output")
        status = edge.get("status")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append(f"{label}.id is required")
        elif edge_id in edge_ids:
            errors.append(f"duplicate edge id: {edge_id}")
        else:
            edge_ids.add(edge_id)
        if not isinstance(inputs, list) or not inputs or not all(isinstance(item, str) for item in inputs):
            errors.append(f"{label}.inputs must be a nonempty string list")
            inputs = []
        if not isinstance(output, str) or not output:
            errors.append(f"{label}.output is required")
            output = ""
        if not isinstance(edge.get("operation"), str) or not edge.get("operation"):
            errors.append(f"{label}.operation is required")
        if status not in EDGE_STATUSES:
            errors.append(f"{label}.status must be one of {sorted(EDGE_STATUSES)}")
        if status == "unsupported" and not edge.get("reason"):
            errors.append(f"{label}.reason is required when unsupported")
        for source in inputs:
            if source not in node_ids:
                errors.append(f"{label} references missing input node: {source}")
            if output:
                adjacency[source].add(output)
        if output and output not in node_ids:
            errors.append(f"{label} references missing output node: {output}")
        elif output:
            incoming[output] += 1
            if incoming[output] > 1:
                errors.append(f"node has more than one producing edge: {output}")
        if status == "completed":
            tool = edge.get("tool")
            if not isinstance(tool, dict) or not tool.get("name") or not tool.get("revision"):
                errors.append(f"{label}.tool name and revision are required when completed")
            config = edge.get("config")
            if not isinstance(config, dict) or not valid_sha256(config.get("sha256")):
                errors.append(f"{label}.config with SHA-256 is required when completed")
            elif verify_files and root_path is not None:
                _verify_reference(config, root_path, f"{label}.config", errors)
            evidence = edge.get("evidence", [])
            if not isinstance(evidence, list):
                errors.append(f"{label}.evidence must be a list")
            elif verify_files and root_path is not None:
                for evidence_index, reference in enumerate(evidence):
                    _verify_reference(reference, root_path, f"{label}.evidence[{evidence_index}]", errors)

    indegree = {node_id: 0 for node_id in node_ids}
    for source, targets in adjacency.items():
        for target in targets:
            if source in node_ids and target in node_ids:
                indegree[target] += 1
    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for target in sorted(adjacency.get(current, ())):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(node_ids):
        errors.append("lineage graph contains a cycle")

    for node_id, status in statuses.items():
        if status == "completed" and incoming[node_id] == 0:
            # Completed roots are allowed only when explicitly declared.
            node = next(item for item in nodes if isinstance(item, dict) and item.get("id") == node_id)
            if not node.get("root", False):
                errors.append(f"completed node has no producing edge and is not declared root: {node_id}")
    return errors
