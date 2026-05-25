# Risk Register

| Risk Category | Hazard Vector | Severity Tier | Mitigation Strategy |
|---|---|---|---|
| Security | Prompt injection from untrusted external sources | Critical | FIDES labels, variable indirection, quarantined analysis |
| System | State drift from uncommitted files or manual edits | High | Git clean checks before promotion |
| Storage | CRDT binary bloat and row rewrite overhead | Medium | Append-only update rows + compaction |
| Operational | Stalled pipelines from missing operator approvals | Low | Local notifications and `ATTENTION.md` review trigger |
