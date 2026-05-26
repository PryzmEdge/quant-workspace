"""
test_ingester.py — tests for proof/ingester.py
"""

import pytest
from ingester import ingest, assert_approved, IngesterError


class TestIngest:
    def test_valid_file_returns_dict(self, approved_md):
        result = ingest(approved_md)
        assert result["path"] == approved_md
        assert "hash_sha256" in result
        assert len(result["hash_sha256"]) == 64
        assert result["frontmatter"]["status"] == "approved"
        assert result["frontmatter"]["operator_approved"] is True

    def test_hash_is_deterministic(self, approved_md):
        r1 = ingest(approved_md)
        r2 = ingest(approved_md)
        assert r1["hash_sha256"] == r2["hash_sha256"]

    def test_missing_file_raises(self):
        with pytest.raises(IngesterError, match="not found"):
            ingest("/nonexistent/path/artifact.md")

    def test_no_frontmatter_returns_empty_dict(self, no_frontmatter_md):
        result = ingest(no_frontmatter_md)
        assert result["frontmatter"] == {}
        assert len(result["body"]) > 0

    def test_body_is_stripped(self, approved_md):
        result = ingest(approved_md)
        assert not result["body"].startswith("\n")

    def test_unapproved_file_ingests_successfully(self, unapproved_md):
        """Ingestion itself does not enforce approval — gate does."""
        result = ingest(unapproved_md)
        assert result["frontmatter"]["operator_approved"] is False


class TestAssertApproved:
    def test_approved_artifact_passes(self, approved_md):
        artifact = ingest(approved_md)
        assert_approved(artifact)  # should not raise

    def test_unapproved_artifact_raises(self, unapproved_md):
        artifact = ingest(unapproved_md)
        with pytest.raises(IngesterError, match="operator_approved"):
            assert_approved(artifact)

    def test_wrong_status_raises(self, unapproved_md):
        artifact = ingest(unapproved_md)
        with pytest.raises(IngesterError):
            assert_approved(artifact)
