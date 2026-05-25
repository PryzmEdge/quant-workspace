# IP Disclosure Log — Markdown Architecture

**Owner**: PryzmEdge
**First Publication**: 2026-05-24
**Repository**: https://github.com/PryzmEdge/Markdown-Architecture
**Status**: Active — append-only

This document is a timestamped public record of original ideas, techniques,
architectural decisions, and design choices developed in this project.
It constitutes prior art for purposes of patent review and invalidity challenges.

Entries are append-only. Never edit or delete a prior entry.

---

## How to Read This Log

Each entry records:
- **Date**: When the idea was first documented or implemented
- **Claim**: The specific technique or design choice
- **Evidence**: Where it appears in the repository or external record
- **Prior Art References**: External work this builds on (to bound novelty claims)

---

## Disclosure Entries

### D-001 — Filesystem-as-State-Machine for Agentic Orchestration
**Date**: 2026-05-18 (first commit) / 2026-05-24 (formalized)
**Claim**: Using a structured directory hierarchy with numbered stage folders,
stage-specific CONTEXT.md files, and YAML-frontmatter artifacts as the
primary state machine for autonomous LLM agent orchestration — without a
separate workflow engine or binary execution layer.
**Evidence**:
- `stages/` directory structure, all CONTEXT.md files
- `docs/blueprint-v2.2.md` § Visual Pipeline
- `CLAUDE.md` navigation rules
**Prior Art References**:
- Van Clief & McDermott (2026). *Interpretable Context Methodology: Folder Structure as Agentic Architecture*. arXiv:2603.16021v2
- Unix filesystem philosophy (Ritchie & Thompson, 1974)

---

### D-002 — YAML Frontmatter as Inter-Stage Contract
**Date**: 2026-05-18
**Claim**: Embedding machine-readable gate conditions (`operator_approved`,
`risk_check_passed`, `status`, `risk_tier`) directly in Markdown YAML
frontmatter, and using a CLI validator (`stage-contract.py`) that exits
0/1 to enforce pipeline promotion as a deterministic check function
\(\mathcal{V}(a, s) \to \{0, 1\}\).
**Evidence**:
- `_config/stage-contract.py`
- `docs/blueprint-v2.2.md` § Gate Logic
- All stage output `.md` files
**Prior Art References**:
- Jekyll/Hugo YAML frontmatter convention (2008–present)
- GitHub Actions job condition syntax

---

### D-003 — Five-Layer Context Hierarchy with Token Budgets
**Date**: 2026-05-24
**Claim**: A named, numbered five-layer information architecture
(Identity / Routing / Stage Contracts / Reference Material / Working Artifacts)
with explicit per-layer token budgets, designed to prevent context rot,
prompt injection, and instruction-data blending in LLM agent systems.
**Evidence**:
- `docs/blueprint-v2.2.md` § Five-Layer Context Hierarchy
- `CLAUDE.md` load-order rules
**Prior Art References**:
- RAG retrieval architectures (Lewis et al., 2020)
- Parnas information-hiding principle (Parnas, 1972)

---

### D-004 — Operator-Gated Pipeline with Append-Only Audit Receipts
**Date**: 2026-05-24
**Claim**: A four-stage agentic pipeline where promotion between stages
requires explicit human operator sign-off (`operator_approved: true`),
combined with cryptographically hashed `PromptExecutionReceipt` JSON
artifacts written to both the filesystem and an append-only PostgreSQL
`provenance_log` table before any stage is declared complete.
**Evidence**:
- `_config/skills/audit_logger.py`
- `proof/schema.sql` (`provenance_log` table)
- `proof/workflow.py`
- `docs/blueprint-v2.2.md` § Audit Receipt
**Prior Art References**:
- PostgreSQL WAL append-only semantics
- ADR-001 (this repository)
- Merkle tree / hash-chain provenance (Merkle, 1979)

---

### D-005 — Sensitivity Ratchet as Lightweight IFC Alternative
**Date**: 2026-05-24
**Claim**: A session-scoped information-flow control mechanism that
permanently narrows an agent's active tool access scope upon first contact
with sensitive or untrusted data, as a O(1) complexity alternative to
full dynamic taint tracking for single-session CLI agents.
**Evidence**:
- `docs/blueprint-v2.2.md` § FIDES and Sensitivity Ratchet
- `_config/domain-rules.md`
**Prior Art References**:
- FIDES IFC framework (Microsoft Research, arXiv:2505.23643)
- Bell-LaPadula model (Bell & LaPadula, 1973)
- crewAI sensitivity ratchet issue #5262 (2025)

---

### D-006 — Gate Boolean Formulas as Executable Pipeline Spec
**Date**: 2026-05-24
**Claim**: Expressing pipeline stage promotion conditions as explicit,
version-controlled Python boolean expressions (gate_00 through gate_03)
inline with the validator source, making the specification and the
enforcement the same artifact.
**Evidence**:
- `_config/stage-contract.py` gate formula docstring
- `docs/blueprint-v2.2.md` § Gate Boolean Formulas
**Prior Art References**:
- Dijkstra's predicate transformers (1975)
- Makefile dependency rules

---

### D-007 — CRDT Append-Row Compaction Pattern over PostgreSQL BYTEA
**Date**: 2026-05-24
**Claim**: Storing incremental CRDT document updates as individual appended
rows in a `document_updates` table, then compacting them into a single
`BYTEA` snapshot via a transaction when a row-count threshold is exceeded,
to avoid repeated in-place binary rewrites and WAL amplification.
**Evidence**:
- `docs/blueprint-v2.2.md` § CRDT Storage Strategy
- ADR-002 (this repository)
**Prior Art References**:
- Yjs / Automerge CRDT frameworks
- PostgreSQL TOAST and BYTEA storage
- ADR-002 (this repository)

---

## Maintenance Rules

1. New entries are appended as `D-NNN` in chronological order
2. Dates reflect first documentation, not filing date
3. Evidence links must point to specific files or commits
4. Prior art references bound the novelty claim — include them honestly
5. This file is committed to `main` and therefore timestamped by GitHub

---

*Markdown Architecture IP Disclosure Log. PryzmEdge. First published 2026-05-24.*
