# Architecture

```text
experiment code ──► immutable artifacts + raw evidence
       │                         │
       └── configs/environment ──┤
                                 ▼
                         lineage + claim index
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              regression      bundle       release
                 gate          builder       audit
```

## Ownership

- Training, CPT, pruning, merging, conversion, and quantization implementations own transformations.
- Evaluators own raw predictions, assertions, task results, and summaries.
- This package validates portable evidence, lineage, and publication rules.
- Optional UIs/databases/telemetry tools may ingest exported files; they are not authoritative prerequisites.

## Design rules

1. Content hashes identify bytes; semantic metadata identifies how bytes were produced.
2. Every completed non-root artifact has exactly one producing transformation edge. A merge has multiple inputs on one edge.
3. Artifacts are immutable; a changed byte sequence gets a new node.
4. Claims reference evidence by path and SHA-256.
5. Raw evidence remains recomputable; reports are derived views.
6. Unsupported and negative results are first-class states.
7. The repository contains small public-safe evidence, not large/private runtime assets.
