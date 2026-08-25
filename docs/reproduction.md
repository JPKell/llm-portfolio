# Reproduction

## Tooling fixture

From a fresh Python 3.11+ environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/llm-portfolio lineage validate examples/fixture/lineage.json --root . --verify-files
.venv/bin/llm-portfolio claims validate examples/fixture/claims.json --root . --verify-files
.venv/bin/llm-portfolio regression evaluate examples/fixture/metrics.json examples/fixture/regression-rules.json
```

Expected outcome: tests and validators pass. The fixture metrics remain synthetic.

## Future observed experiment

An experiment-specific reproduction guide must name:

- hardware and minimum resources;
- environment/container lock and digest;
- exact source artifacts and acquisition checks;
- data/evaluation access and license constraints;
- commands with expected runtime/storage;
- deterministic settings and expected tolerance;
- raw-output locations and expected hashes where deterministic; and
- recovery/cleanup without deleting unrelated data.

The independent auditor should create a fresh environment from the lock and must not rely on an author's shell history, caches, database, or UI.
