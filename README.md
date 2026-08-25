# llm-portfolio

Code-first tooling and evidence structure for a public, single-GPU local-LLM engineering portfolio.

## Current status

The repository is an **in-development portfolio scaffold**. Its lineage, evidence, regression, statistics, bundle, and release-audit utilities are tested. Files under `examples/fixture/` are synthetic demonstrations and are not model-quality results. Observed experiment reports will be added only after their raw evidence passes the independent M08 audit.

## What this repository demonstrates

- immutable model/transformation lineage with parent and tool/config identities;
- claim-to-raw-evidence hash verification;
- simple statistical summaries and deterministic bootstrap intervals;
- local model-regression gates;
- reproducibility-bundle construction; and
- public-release scanning for secrets, private paths, large/model artifacts, symlinks, and unresolved placeholders.

The toolkit uses only the Python standard library. It does not require or import FreeWeight, SweatMeter, WeightsDB, ModelRack, SetSpec, BaseAiCore, MirrorWall, LoadCoach, or IdeaPress. Those applications may consume exported JSON later without owning experiment truth.

## Quick start

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/llm-portfolio lineage validate examples/fixture/lineage.json --root . --verify-files
.venv/bin/llm-portfolio claims validate examples/fixture/claims.json --root . --verify-files
.venv/bin/llm-portfolio regression evaluate examples/fixture/metrics.json examples/fixture/regression-rules.json
.venv/bin/llm-portfolio release audit .
```

## Repository map

```text
src/llm_portfolio/   reusable implementation
tests/               unit and negative tests
configs/             schemas/examples for future real experiments
examples/fixture/    MIT synthetic evidence only
experiments/         model-run manifests and raw evidence indexes (later)
reports/             audited case studies (later)
docs/                architecture, evidence, licensing, reproduction
```

## Evidence before narrative

An `observed` claim needs raw evidence paths and SHA-256 hashes. A passing hash verifies bytes, not scientific validity; the protocol, controls, data separation, statistics, and lineage must also pass review. Planned, unsupported, inconclusive, fixture, and retracted outcomes remain visibly labeled.

## Licensing

Learner-authored repository code and prose are MIT licensed. This does not relicense model weights, datasets, tokenizers, upstream code, benchmark tasks, or future derivatives. See `docs/licensing.md` and `THIRD_PARTY.md`.
