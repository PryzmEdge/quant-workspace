"""
graphify_query.py — Graphify MCP client skill v1.0

Allows agents to query the Graphify knowledge graph via its local MCP server
instead of loading full Markdown files into context.

This skill is the bridge between the five-layer context hierarchy (Layer 3)
and the Graphify graph index. Agents call this skill to retrieve only the
relevant graph slice for their current task.

Usage (direct CLI):
  python _config/skills/graphify_query.py --query "synthesis stage risk artifacts"
  python _config/skills/graphify_query.py --node stages/02-analysis/output/risk.md
  python _config/skills/graphify_query.py --path-from stages/00-intake/output/problem.md \\
                                            --path-to stages/03-output/output/
  python _config/skills/graphify_query.py --filter status=approved

API (imported by agent):
  from _config.skills.graphify_query import query, get_node, get_path, filter_nodes

Requires:
  Graphify MCP server running: graphify serve --config graphify.config.json
  pip install httpx
"""

import argparse
import json
import sys
import os

try:
    import httpx
except ImportError:
    httpx = None

GRAPHIFY_MCP_URL = os.environ.get("GRAPHIFY_MCP_URL", "http://localhost:7331")
DEFAULT_TOKEN_BUDGET = 800


# ---------------------------------------------------------------------------
# Core MCP client
# ---------------------------------------------------------------------------

def _call(tool: str, params: dict) -> dict:
    """Call a Graphify MCP tool and return the result."""
    if httpx is None:
        raise RuntimeError(
            "httpx is required: pip install httpx"
        )
    try:
        resp = httpx.post(
            f"{GRAPHIFY_MCP_URL}/tool/{tool}",
            json=params,
            timeout=10.0
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Graphify MCP server not running at {GRAPHIFY_MCP_URL}.\n"
            "Start it with: graphify serve --config graphify.config.json"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def query(text: str, max_tokens: int = DEFAULT_TOKEN_BUDGET) -> dict:
    """
    Semantic query against the graph.
    Returns relevant nodes within the token budget.
    """
    return _call("query_node", {"query": text, "max_tokens": max_tokens})


def get_node(path: str) -> dict:
    """
    Get a single node by file path.
    Returns frontmatter metadata + body summary.
    """
    return _call("get_neighbors", {"node": path, "depth": 1})


def get_path(from_node: str, to_node: str) -> dict:
    """
    Find the dependency path between two nodes.
    Useful for tracing stage promotion chains.
    """
    return _call("find_path", {"from": from_node, "to": to_node})


def filter_nodes(field: str, value: str) -> dict:
    """
    Filter all nodes by a frontmatter metadata field.
    Example: filter_nodes("status", "approved")
             filter_nodes("risk_tier", "High")
    """
    return _call("filter_by_metadata", {"field": field, "value": value})


def get_stage_slice(stage_id: str) -> dict:
    """
    Convenience: return all nodes belonging to a specific stage.
    Example: get_stage_slice("02-analysis")
    """
    return filter_nodes("stage", stage_id)


def get_blocked_artifacts() -> dict:
    """Return all artifacts with status=blocked or operator_approved=false."""
    return filter_nodes("status", "blocked")


def get_high_risk_artifacts() -> dict:
    """Return all artifacts with risk_tier High or Critical."""
    results = {}
    for tier in ["High", "High/Critical", "Critical"]:
        r = filter_nodes("risk_tier", tier)
        results[tier] = r.get("nodes", [])
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="graphify_query — query the Graphify knowledge graph"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query",       metavar="TEXT",  help="Semantic query")
    group.add_argument("--node",        metavar="PATH",  help="Get node by path")
    group.add_argument("--filter",      metavar="K=V",   help="Filter by metadata field (e.g. status=approved)")
    group.add_argument("--stage-slice", metavar="STAGE", help="Get all nodes for a stage (e.g. 02-analysis)")
    group.add_argument("--blocked",     action="store_true", help="List blocked artifacts")
    group.add_argument("--high-risk",   action="store_true", help="List High/Critical risk artifacts")
    parser.add_argument("--path-from",  metavar="FROM",  help="Path-finding: source node")
    parser.add_argument("--path-to",    metavar="TO",    help="Path-finding: target node")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_TOKEN_BUDGET)
    args = parser.parse_args()

    try:
        if args.query:
            result = query(args.query, args.max_tokens)
        elif args.node:
            result = get_node(args.node)
        elif args.filter:
            k, v = args.filter.split("=", 1)
            result = filter_nodes(k.strip(), v.strip())
        elif args.stage_slice:
            result = get_stage_slice(args.stage_slice)
        elif args.blocked:
            result = get_blocked_artifacts()
        elif args.high_risk:
            result = get_high_risk_artifacts()
        elif args.path_from and args.path_to:
            result = get_path(args.path_from, args.path_to)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(result, indent=2))

    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
