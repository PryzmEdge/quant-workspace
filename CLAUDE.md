---
version: "8.0.0"
tokens: "≤800"
scope: "navigation, structure, identity"
do_not_use_for: "hard constraints, behavioral enforcement"
---

# Quant Workspace — CLAUDE.md

> **Scope**: Structural navigation and identity only. Hard constraints live in hooks. Schema contracts live in Pydantic models. See `docs/v8.md` Part 3 and Part 6 for the full enforcement model.

---

## Workspace Identity

This is a quant research and AI-native DevOps workspace structured with the Interpretable Context Methodology (ICM). Every stage is a self-contained unit with explicit Inputs, Process, and Outputs declared in a `CONTEXT.md` file.

---

## Folder Structure

```
quant-workspace/
├── CLAUDE.md                   ← This file (≤800 tokens, navigation only)
├── docs/
│   └── v8.md                   ← Engineering position paper
├── _config/
│   ├── domain-rules.md         ← Constraints applied at every stage
│   └── stage-contract.py       ← Pydantic StageContract schema
├── stages/
│   ├── 00-intake/
│   │   └── CONTEXT.md
│   ├── 01-research/
│   │   └── CONTEXT.md
│   ├── 02-analysis/
│   │   └── CONTEXT.md
│   └── 03-output/
│       └── CONTEXT.md
├── .claude/
│   ├── settings.json           ← Hooks (hard constraints, deterministic enforcement)
│   └── hooks/
│       └── validate-mcp-response.py
└── Makefile
```

---

## Navigation Rules

- **Load stage context by section, not full file.** Reference only the section you need from a `CONTEXT.md` (Inputs, Process, or Outputs).
- **Never load full `domain-rules.md`.** Load the `## Constraints` section only.
- **Stage promotion requires `operator_approved: true`** in the stage's YAML frontmatter before writing to the next stage's `output/` directory.
- **Do not write to `output/`** of any stage until the current stage's acceptance criteria are GREEN.

---

## Required YAML Frontmatter (every .md artifact)

```yaml
---
status: draft | review | approved
operator_approved: false
risk_check_passed: false
stage: "00-intake" | "01-research" | "02-analysis" | "03-output"
---
```

---

## What Belongs Here vs. Elsewhere

| Concern | Location |
|---|---|
| File paths, build commands | CLAUDE.md (here) ✅ |
| Schema field definitions | `_config/stage-contract.py` ✅ |
| "Never run `DROP TABLE`" | `.claude/settings.json` hooks ✅ |
| "Always validate MCP responses" | `.claude/settings.json` hooks ✅ |
| Domain-specific constraints | `_config/domain-rules.md` ✅ |
| Behavioral rules | **Not here** — use hooks ❌ |

---

## Build Commands

```bash
# Parallel build (required — sequential is slow)
make -j$(nproc) all

# Single stage
make stage=02-analysis

# Validate a stage output before promotion
python _config/stage-contract.py --stage 02-analysis
```

---

## Skills

Load domain-specific skills on demand — do not load all skills on every turn:

- `domain-validator` — validate stage artifacts against `domain-rules.md`
- `context-compiler` — assemble token-budgeted context from stage inputs
- `audit-logger` — write `PromptExecutionReceipt` to the append-only log

---

*Token budget: this file must remain ≤800 tokens. Trim before adding.*
