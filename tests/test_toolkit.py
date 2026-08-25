from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from llm_portfolio.audit import REQUIRED_FILES, audit_tree
from llm_portfolio.bundle import build_bundle
from llm_portfolio.evidence import validate_claim_index
from llm_portfolio.hashing import sha256_file
from llm_portfolio.lineage import validate_lineage
from llm_portfolio.regression import evaluate_rules
from llm_portfolio.statistics import bootstrap_mean_interval, paired_differences, summarize


class LineageTests(unittest.TestCase):
    def _valid(self, root: Path) -> dict:
        (root / "base.txt").write_text("base\n", encoding="utf-8")
        (root / "child.txt").write_text("child\n", encoding="utf-8")
        (root / "config.json").write_text("{}\n", encoding="utf-8")
        return {
            "schema": "llm-portfolio-lineage-v1",
            "nodes": [
                {"id": "base", "kind": "model", "status": "completed", "root": True,
                 "artifact": {"path": "base.txt", "sha256": sha256_file(root / "base.txt")}},
                {"id": "child", "kind": "adapter", "status": "completed",
                 "artifact": {"path": "child.txt", "sha256": sha256_file(root / "child.txt")}},
            ],
            "edges": [
                {"id": "train", "inputs": ["base"], "output": "child", "operation": "fixture",
                 "status": "completed", "tool": {"name": "fixture", "revision": "1"},
                 "config": {"path": "config.json", "sha256": sha256_file(root / "config.json")},
                 "evidence": []}
            ],
        }

    def test_valid_completed_lineage_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(validate_lineage(self._valid(root), root=root, verify_files=True), [])

    def test_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = self._valid(root)
            (root / "child.txt").write_text("changed\n", encoding="utf-8")
            self.assertTrue(any("hash mismatch" in error for error in validate_lineage(document, root=root, verify_files=True)))

    def test_cycle_fails(self):
        document = {
            "schema": "llm-portfolio-lineage-v1",
            "nodes": [
                {"id": "a", "kind": "model", "status": "planned"},
                {"id": "b", "kind": "model", "status": "planned"},
            ],
            "edges": [
                {"id": "ab", "inputs": ["a"], "output": "b", "operation": "x", "status": "planned"},
                {"id": "ba", "inputs": ["b"], "output": "a", "operation": "x", "status": "planned"},
            ],
        }
        self.assertIn("lineage graph contains a cycle", validate_lineage(document))

    def test_missing_parent_fails(self):
        document = {
            "schema": "llm-portfolio-lineage-v1",
            "nodes": [{"id": "child", "kind": "model", "status": "planned"}],
            "edges": [{"id": "edge", "inputs": ["missing"], "output": "child", "operation": "x", "status": "planned"}],
        }
        self.assertTrue(any("missing input" in error for error in validate_lineage(document)))


class EvidenceTests(unittest.TestCase):
    def test_evidence_hash_passes_and_then_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "raw.json"
            path.write_text("{}\n", encoding="utf-8")
            document = {"schema": "llm-portfolio-claims-v1", "claims": [
                {"id": "c1", "status": "observed", "statement": "fixture",
                 "evidence": [{"path": "raw.json", "sha256": sha256_file(path)}]}
            ]}
            self.assertEqual(validate_claim_index(document, root=root, verify_files=True), [])
            path.write_text("{\"changed\": true}\n", encoding="utf-8")
            self.assertTrue(any("hash mismatch" in error for error in validate_claim_index(document, root=root, verify_files=True)))

    def test_observed_claim_requires_evidence(self):
        document = {"schema": "llm-portfolio-claims-v1", "claims": [
            {"id": "c1", "status": "observed", "statement": "unsupported claim", "evidence": []}
        ]}
        self.assertTrue(validate_claim_index(document))


class StatisticsAndRegressionTests(unittest.TestCase):
    def test_statistics_and_paired_difference(self):
        self.assertEqual(summarize([1, 2, 3])["mean"], 2.0)
        self.assertEqual(paired_differences([1, 2], [2, 4]), [1.0, 2.0])
        first = bootstrap_mean_interval([1, 2, 3], resamples=500, seed=7)
        second = bootstrap_mean_interval([1, 2, 3], resamples=500, seed=7)
        self.assertEqual(first, second)

    def test_regression_block_and_warning(self):
        specification = {"schema": "llm-portfolio-regression-v1", "rules": [
            {"metric": "quality", "operator": "ge", "threshold": 0.9, "severity": "block"},
            {"metric": "speed", "operator": "ge", "threshold": 10, "severity": "warn"},
        ]}
        self.assertTrue(evaluate_rules({"quality": 0.95, "speed": 1}, specification)["passed"])
        self.assertFalse(evaluate_rules({"quality": 0.8, "speed": 100}, specification)["passed"])


class BundleAndAuditTests(unittest.TestCase):
    def test_bundle_is_allowlisted_and_hashed(self):
        with tempfile.TemporaryDirectory() as source_directory, tempfile.TemporaryDirectory() as parent_directory:
            source = Path(source_directory)
            destination = Path(parent_directory) / "bundle"
            (source / "a.txt").write_text("a\n", encoding="utf-8")
            (source / "ignored.txt").write_text("ignored\n", encoding="utf-8")
            manifest = build_bundle(source, {"schema": "llm-portfolio-bundle-v1", "bundle_id": "x", "include": ["a.txt"]}, destination)
            self.assertEqual([item["path"] for item in manifest["files"]], ["a.txt"])
            self.assertFalse((destination / "ignored.txt").exists())
            self.assertTrue((destination / "checksums.sha256").is_file())

    def test_bundle_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as source_directory, tempfile.TemporaryDirectory() as parent_directory:
            with self.assertRaises(ValueError):
                build_bundle(source_directory, {"schema": "llm-portfolio-bundle-v1", "bundle_id": "x", "include": ["../outside"]}, Path(parent_directory) / "bundle")

    def _release_root(self, root: Path) -> None:
        for required in REQUIRED_FILES:
            (root / required).write_text("fixture\n", encoding="utf-8")
        (root / ".gitignore").write_text("*.safetensors\n*.gguf\n.env\n", encoding="utf-8")

    def test_release_audit_passes_safe_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._release_root(root)
            self.assertTrue(audit_tree(root)["passed"])

    def test_release_audit_blocks_secret_and_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._release_root(root)
            token = "gh" + "p_" + "A" * 24
            placeholder = "QUALIFICATION" + "_REQUIRED"
            (root / "bad.txt").write_text(token + "\n" + placeholder + "\n", encoding="utf-8")
            report = audit_tree(root)
            self.assertFalse(report["passed"])
            self.assertGreaterEqual(len(report["findings"]), 2)


if __name__ == "__main__":
    unittest.main()
