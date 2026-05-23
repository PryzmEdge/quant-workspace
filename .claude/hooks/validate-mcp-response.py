#!/usr/bin/env python3
"""
PostToolUse hook: validate every MCP tool response before it enters
the reasoning context.

MCP is not a trusted execution boundary. See docs/v8.md Part 8 and
arXiv:2504.03767 (MCP Safety Audit, 2025).

This hook reads the tool result from stdin (Claude Code hook protocol),
runs structural and content validation, and either passes it through
(exit 0) or blocks it with a diagnostic (exit 1).

Threat model:
  - Prompt injection via tool outputs
  - Server impersonation
  - Unauthorized data exfiltration via malicious server responses
"""

import json
import sys
import re
import hashlib
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

AUDIT_LOG = Path(".claude/logs/mcp-validation.jsonl")
MAX_RESPONSE_BYTES = 512_000  # 512KB hard ceiling — reject oversized responses

# Prompt injection patterns — extend as new vectors are discovered
INJECTION_PATTERNS = [
    # Instruction override attempts
    r"ignore (all |previous |your )?instructions",
    r"disregard (all |previous |your )?instructions",
    r"new (system )?prompt",
    r"you are now",
    r"act as (a |an )?(different|new|another)",
    # Exfiltration probes
    r"send .{0,40}(to|via) (http|https|ftp)",
    r"POST .{0,60}credentials",
    r"exfiltrate",
    # Shell injection
    r"`[^`]{0,200}`",          # backtick command substitution in text
    r"\$\([^)]{0,200}\)",      # $() substitution
    r";\s*(rm|curl|wget|bash|sh|python|nc)\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_hook_input() -> dict:
    """Read the hook payload from stdin."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw)
    except Exception as e:
        block(f"Failed to parse hook input: {e}", {})


def response_text(payload: dict) -> str:
    """Extract text content from the tool result for scanning."""
    result = payload.get("tool_result", {})
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        # Common MCP response shapes
        for key in ("content", "text", "output", "data", "result"):
            val = result.get(key, "")
            if isinstance(val, str):
                return val
            if isinstance(val, list):
                return " ".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in val
                )
    return json.dumps(result)


def append_audit(record: dict) -> None:
    """Append a validation record to the append-only audit log."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def block(reason: str, payload: dict) -> None:
    """Emit a blocking diagnostic and exit non-zero."""
    record = {
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "event": "mcp_response_blocked",
        "tool": payload.get("tool_name", "unknown"),
        "reason": reason,
    }
    append_audit(record)
    # Claude Code reads stderr for hook diagnostics
    print(f"[MCP VALIDATION BLOCKED] {reason}", file=sys.stderr)
    sys.exit(1)


def pass_through(payload: dict, content_hash: str) -> None:
    """Record a clean pass and exit zero."""
    record = {
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "event": "mcp_response_passed",
        "tool": payload.get("tool_name", "unknown"),
        "response_sha256": content_hash,
    }
    append_audit(record)
    sys.exit(0)


# ---------------------------------------------------------------------------
# Validation pipeline
# ---------------------------------------------------------------------------

def validate(payload: dict) -> None:
    text = response_text(payload)
    raw_bytes = text.encode("utf-8", errors="replace")

    # 1. Size gate — reject oversized responses before any further processing
    if len(raw_bytes) > MAX_RESPONSE_BYTES:
        block(
            f"Response size {len(raw_bytes):,} bytes exceeds {MAX_RESPONSE_BYTES:,} byte ceiling.",
            payload,
        )

    content_hash = hashlib.sha256(raw_bytes).hexdigest()

    # 2. Prompt injection scan
    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            block(
                f"Prompt injection pattern detected: '{pattern.pattern}' "
                f"at position {match.start()}.",
                payload,
            )

    # 3. Schema presence check — tool result must be parseable
    result = payload.get("tool_result")
    if result is None:
        block("MCP tool_result key missing from hook payload.", payload)

    # All checks passed
    pass_through(payload, content_hash)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    payload = load_hook_input()
    validate(payload)
