"""
test_graphify_query.py — tests for _config/skills/graphify_query.py

Uses a pytest fixture to run a lightweight mock MCP server so tests
don't require a live Graphify instance.
"""

import json
import threading
import pytest
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys_path_insert = __import__("sys").path.insert
sys_path_insert(0, str(Path(__file__).parent.parent / "_config" / "skills"))
import graphify_query


# ---------------------------------------------------------------------------
# Mock MCP server
# ---------------------------------------------------------------------------

MOCK_RESPONSES = {
    "query_node":         {"nodes": [{"path": "stages/02-analysis/output/risk.md", "score": 0.95}]},
    "get_neighbors":      {"node": "stages/00-intake/output/problem.md", "neighbors": []},
    "find_path":          {"path": ["stages/00-intake/output/problem.md", "stages/01-research/output/brief.md"]},
    "filter_by_metadata": {"nodes": [{"path": "stages/03-output/output/report.md", "status": "approved"}]},
}


class MockMCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        tool = self.path.split("/tool/")[-1]
        response = MOCK_RESPONSES.get(tool, {"error": "unknown tool"})
        body = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # suppress output


@pytest.fixture(scope="module")
def mock_mcp_server():
    server = HTTPServer(("127.0.0.1", 0), MockMCPHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    graphify_query.GRAPHIFY_MCP_URL = f"http://127.0.0.1:{port}"
    yield port
    server.shutdown()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGraphifyQuery:
    def test_query_returns_nodes(self, mock_mcp_server):
        result = graphify_query.query("risk artifacts")
        assert "nodes" in result
        assert len(result["nodes"]) > 0

    def test_query_node_path_present(self, mock_mcp_server):
        result = graphify_query.query("risk artifacts")
        assert result["nodes"][0]["path"] == "stages/02-analysis/output/risk.md"

    def test_get_node_returns_neighbors(self, mock_mcp_server):
        result = graphify_query.get_node("stages/00-intake/output/problem.md")
        assert "node" in result

    def test_get_path_returns_list(self, mock_mcp_server):
        result = graphify_query.get_path(
            "stages/00-intake/output/problem.md",
            "stages/01-research/output/brief.md"
        )
        assert "path" in result
        assert len(result["path"]) == 2

    def test_filter_nodes_returns_results(self, mock_mcp_server):
        result = graphify_query.filter_nodes("status", "approved")
        assert "nodes" in result

    def test_get_stage_slice(self, mock_mcp_server):
        result = graphify_query.get_stage_slice("02-analysis")
        assert "nodes" in result

    def test_get_blocked_artifacts(self, mock_mcp_server):
        result = graphify_query.get_blocked_artifacts()
        assert "nodes" in result

    def test_get_high_risk_artifacts(self, mock_mcp_server):
        result = graphify_query.get_high_risk_artifacts()
        assert isinstance(result, dict)
        assert "High" in result
        assert "Critical" in result


class TestGraphifyQueryErrors:
    def test_connect_error_raises_runtime(self):
        original_url = graphify_query.GRAPHIFY_MCP_URL
        graphify_query.GRAPHIFY_MCP_URL = "http://127.0.0.1:1"  # nothing running
        with pytest.raises(RuntimeError, match="not running"):
            graphify_query.query("test")
        graphify_query.GRAPHIFY_MCP_URL = original_url
