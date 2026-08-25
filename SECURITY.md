# Security Policy

## Reporting

Please do not open a public issue containing a credential, private dataset excerpt, personal information, exploitable generated program, or unreleased evaluation answer. Use GitHub's private vulnerability-reporting feature if enabled; otherwise contact the repository owner through the private contact method listed on the owner's GitHub profile.

## Scope

The repository treats model output, downloaded code/data, manifests, archives, and checkpoints as untrusted. Reproduction instructions must not execute third-party corpus code. Generated-code evaluation requires an isolated, resource-limited, network-disabled environment.

## Public-release rules

- Never commit credentials, environment files, private absolute paths, hidden-test answers, or unreviewed logs.
- Large model/data/optimizer artifacts stay outside Git.
- Verify licenses and notices before publishing any upstream or derived artifact.
- Run `python -m llm_portfolio release audit .` and inspect the staged diff before every release.

Security support is best effort for this educational project. No production-service guarantee is made.
