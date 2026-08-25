# Evidence Standard

An observed result needs the following layers:

1. **Identity:** model, tokenizer, data, evaluator, configuration, code/tool, environment, and output hashes.
2. **Validity:** frozen controls, data separation, correct denominators/masks/templates, registered selection, and comparable conditions.
3. **Raw evidence:** per-sample results, generations, benchmark output, timings, logs, and telemetry availability.
4. **Statistics:** sample count, raw repetitions, summary, uncertainty/dispersion, seeds, and tolerance.
5. **Claim:** bounded statement with status, scope, evidence references, limitations, and publication decision.

`observed` is not a synonym for correct. The audit checks that evidence exists and matches; M08 checks whether it supports the conclusion.

## Result categories

- Language modeling: token-weighted loss/perplexity with one tokenizer/protocol.
- Standard benchmark: task implementation/dataset/prompt/harness revision and per-sample output.
- Application: reviewed assertions over held-out task cases.
- Performance: artifact/backend/hardware-specific prompt and generation measurements.

Never combine these four surfaces into one unexplained score.
