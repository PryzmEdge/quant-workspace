# Markdown Architecture

A research and AI-native DevOps workspace structured with the Interpretable Context Methodology (ICM).

**Thesis**: Markdown is a human-readable orchestration substrate — not an execution environment.

## Structure

- `docs/v10-draft.md` — Canonical engineering position paper (v10)
- `docs/adr/` — Architecture Decision Records (ADR-001 through ADR-005)
- `stages/` — ICM pipeline: 00-intake → 01-research → 02-analysis → 03-output
- `_config/` — Domain rules and stage contract validator
- `.claude/` — Hooks and hard constraints

## Quick Start

```bash
# Validate a stage
python _config/stage-contract.py --stage 01-research

# Parallel build
make -j$(nproc) all
```

## Paper

See [`docs/v10-draft.md`](docs/v10-draft.md) for the full engineering position paper.
See [`docs/adr/`](docs/adr/) for all architectural decision records.
