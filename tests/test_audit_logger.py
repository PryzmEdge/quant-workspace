"""
test_audit_logger.py — tests for _config/skills/audit_logger.py
"""

import json
import os
import hashlib
import pytest
from pathlib import Path

sys_path_insert = __import__("sys").path.insert
sys_path_insert(0, str(Path(__file__).parent.parent / "_config" / "skills"))
from audit_logger import write_receipt, sha256_str, sha256_file


SAMPLE_AUDIT_DATA = {
    "stage_id":   "03-output",
    "agent_id":   "test-agent-v1",
    "operator_id": "test-operator",
    "operator_comment": "automated test",
    "input_artifacts": [],
    "output_artifacts": [],
    "frontmatter_snapshot": {"status": "approved", "operator_approved": True},
    "gate_check_results": {"all_upstream_approved": True},
    "llm_prompt": "test prompt",
    "llm_response": "test response",
    "cost": {"tokens_in_uncached": 100, "tokens_out": 50, "usd_estimated": 0.001}
}


class TestSha256Helpers:
    def test_sha256_str_deterministic(self):
        h1 = sha256_str("hello")
        h2 = sha256_str("hello")
        assert h1 == h2
        assert len(h1) == 64

    def test_sha256_str_empty(self):
        assert sha256_str("") == ""

    def test_sha256_file_missing(self):
        result = sha256_file("/nonexistent/file.md")
        assert result == "FILE_NOT_FOUND"

    def test_sha256_file_real(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_bytes(b"hello")
        h = sha256_file(str(f))
        assert h == hashlib.sha256(b"hello").hexdigest()


class TestWriteReceipt:
    def test_receipt_written_to_filesystem(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = write_receipt(SAMPLE_AUDIT_DATA)
        assert Path(result["receipt_path"]).exists()

    def test_receipt_is_valid_json(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = write_receipt(SAMPLE_AUDIT_DATA)
        content = Path(result["receipt_path"]).read_text()
        parsed = json.loads(content)
        assert parsed["stage_id"] == "03-output"

    def test_receipt_has_all_required_fields(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = write_receipt(SAMPLE_AUDIT_DATA)
        receipt = json.loads(Path(result["receipt_path"]).read_text())
        for field in ["receipt_id", "timestamp", "stage_id", "agent_id",
                      "operator_signoff", "gate_check_results",
                      "llm_prompt_hash", "llm_response_hash", "cost"]:
            assert field in receipt, f"Missing field: {field}"

    def test_prompt_not_stored_in_plaintext(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = write_receipt(SAMPLE_AUDIT_DATA)
        content = Path(result["receipt_path"]).read_text()
        assert "test prompt" not in content
        assert "test response" not in content

    def test_pg_receipt_hash_matches_file(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = write_receipt(SAMPLE_AUDIT_DATA)
        file_content = Path(result["receipt_path"]).read_text()
        expected_hash = hashlib.sha256(file_content.encode()).hexdigest()
        assert result["pg_receipt_hash"] == expected_hash

    def test_each_receipt_has_unique_id(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        r1 = write_receipt(SAMPLE_AUDIT_DATA)
        r2 = write_receipt(SAMPLE_AUDIT_DATA)
        r1_data = json.loads(Path(r1["receipt_path"]).read_text())
        r2_data = json.loads(Path(r2["receipt_path"]).read_text())
        assert r1_data["receipt_id"] != r2_data["receipt_id"]

    def test_operator_signoff_recorded(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = write_receipt(SAMPLE_AUDIT_DATA)
        receipt = json.loads(Path(result["receipt_path"]).read_text())
        assert receipt["operator_signoff"]["name"] == "test-operator"
        assert receipt["operator_signoff"]["comment"] == "automated test"

    def test_artifact_hashes_computed(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        artifact = tmp_path / "test-artifact.md"
        artifact.write_text("# Test")
        data = {**SAMPLE_AUDIT_DATA, "input_artifacts": [{"path": str(artifact)}]}
        result = write_receipt(data)
        receipt = json.loads(Path(result["receipt_path"]).read_text())
        assert receipt["input_artifacts"][0]["hash_sha256"] != "FILE_NOT_FOUND"
