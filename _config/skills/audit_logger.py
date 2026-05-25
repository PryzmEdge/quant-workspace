"""
audit-logger skill — v1.0

Produces a PromptExecutionReceipt JSON file for a completed stage.
Called by the Output Assembly Agent at Stage 03 before final promotion.

Usage (direct):
  python _config/skills/audit_logger.py --stage 03-output --operator <name>

API (imported by agent):
  from _config.skills.audit_logger import write_receipt
  result = write_receipt(audit_data)
  # result: { "auditId": str, "timestamp": str, "receipt_path": str, "pg_receipt_hash": str }

Inputs (audit_data dict):
  {
    "stage_id": str,              # e.g. "03-output"
    "agent_id": str,              # e.g. "agent-output-v1.0"
    "operator_id": str,           # named human approver
    "operator_comment": str,      # optional
    "input_artifacts": [
      {"path": str},              # hash computed automatically
    ],
    "output_artifacts": [
      {"path": str, "fides_label": str},
    ],
    "frontmatter_snapshot": dict, # YAML frontmatter of the primary output artifact
    "gate_check_results": dict,   # boolean results from gate formula fields
    "llm_prompt": str | None,     # raw prompt text (hashed, not stored in plain)
    "llm_response": str | None,   # raw response text (hashed, not stored in plain)
    "cost": {
      "tokens_in_uncached": int,
      "tokens_out": int,
      "usd_estimated": float
    }
  }

Outputs:
  Writes <timestamp>.json to stages/<stage_id>/output/receipts/
  Returns { "auditId", "timestamp", "receipt_path", "pg_receipt_hash" }

Note on pg_receipt_hash:
  The SHA-256 of the full receipt JSON. This hash should be committed to the
  Postgres provenance_log table (ADR-001) by the calling workflow.
  This skill does NOT write to Postgres directly.
"""

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return sha256_bytes(f.read())
    except FileNotFoundError:
        return "FILE_NOT_FOUND"

def sha256_str(s: str) -> str:
    return sha256_bytes(s.encode("utf-8")) if s else ""

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def write_receipt(audit_data: dict) -> dict:
    """
    Build and write the PromptExecutionReceipt.
    Returns { "auditId", "timestamp", "receipt_path", "pg_receipt_hash" }.
    """
    stage_id  = audit_data.get("stage_id", "unknown-stage")
    agent_id  = audit_data.get("agent_id", "unknown-agent")
    operator  = audit_data.get("operator_id", "unknown-operator")
    timestamp = now_iso()
    audit_id  = str(uuid.uuid4())

    # Hash input artifacts
    input_artifacts = []
    for artifact in audit_data.get("input_artifacts", []):
        path = artifact.get("path", "")
        input_artifacts.append({
            "path": path,
            "hash_sha256": sha256_file(path)
        })

    # Hash output artifacts
    output_artifacts = []
    for artifact in audit_data.get("output_artifacts", []):
        path = artifact.get("path", "")
        output_artifacts.append({
            "path": path,
            "hash_sha256": sha256_file(path),
            "fides_label": artifact.get("fides_label", "INTERNAL_TRUSTED")
        })

    # Hash prompt and response (never store plaintext)
    llm_prompt   = audit_data.get("llm_prompt")   or ""
    llm_response = audit_data.get("llm_response") or ""

    receipt = {
        "receipt_id":             audit_id,
        "timestamp":              timestamp,
        "stage_id":               stage_id,
        "agent_id":               agent_id,
        "input_artifacts":        input_artifacts,
        "output_artifacts":       output_artifacts,
        "yaml_frontmatter_snapshot": audit_data.get("frontmatter_snapshot", {}),
        "gate_check_results":     audit_data.get("gate_check_results", {}),
        "llm_prompt_hash":        sha256_str(llm_prompt),
        "llm_response_hash":      sha256_str(llm_response),
        "operator_signoff": {
            "name":      operator,
            "timestamp": timestamp,
            "comment":   audit_data.get("operator_comment", "")
        },
        "cost": audit_data.get("cost", {
            "tokens_in_uncached": 0,
            "tokens_out": 0,
            "usd_estimated": 0.0
        })
    }

    # Write receipt file
    receipts_dir = Path(f"stages/{stage_id}/output/receipts")
    receipts_dir.mkdir(parents=True, exist_ok=True)
    ts_clean = timestamp.replace(":", "").replace("-", "")
    receipt_path = receipts_dir / f"{ts_clean}.json"

    receipt_json = json.dumps(receipt, indent=2)
    with open(receipt_path, "w", encoding="utf-8") as f:
        f.write(receipt_json)

    pg_receipt_hash = sha256_str(receipt_json)

    print(f"[audit-logger] Receipt written: {receipt_path}")
    print(f"[audit-logger] pg_receipt_hash (commit to provenance_log): {pg_receipt_hash}")

    return {
        "auditId":         audit_id,
        "timestamp":       timestamp,
        "receipt_path":    str(receipt_path),
        "pg_receipt_hash": pg_receipt_hash
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="audit-logger skill: write a PromptExecutionReceipt"
    )
    parser.add_argument("--stage",    required=True, help="Stage ID, e.g. 03-output")
    parser.add_argument("--agent",    default="agent-output-v1.0")
    parser.add_argument("--operator", required=True, help="Named human approver")
    parser.add_argument("--comment",  default="")
    args = parser.parse_args()

    # Minimal CLI invocation — collects artifact paths from stage output dir
    output_dir = Path(f"stages/{args.stage}/output")
    output_artifacts = [
        {"path": str(p), "fides_label": "INTERNAL_TRUSTED"}
        for p in output_dir.glob("*.md")
        if p.name != "ATTENTION.md"
    ] if output_dir.exists() else []

    audit_data = {
        "stage_id":   args.stage,
        "agent_id":   args.agent,
        "operator_id": args.operator,
        "operator_comment": args.comment,
        "input_artifacts":  [],
        "output_artifacts": output_artifacts,
        "frontmatter_snapshot": {},
        "gate_check_results": {},
    }

    result = write_receipt(audit_data)
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
