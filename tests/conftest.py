"""
conftest.py — shared pytest fixtures for Markdown Architecture test suite.
"""

import os
import sys
import pytest
from pathlib import Path

# Ensure repo root is on sys.path so all _config modules resolve
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "proof"))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES


@pytest.fixture
def approved_md(fixtures_dir):
    return str(fixtures_dir / "approved.md")


@pytest.fixture
def unapproved_md(fixtures_dir):
    return str(fixtures_dir / "unapproved.md")


@pytest.fixture
def high_risk_md(fixtures_dir):
    return str(fixtures_dir / "high-risk.md")


@pytest.fixture
def sources_3rows_md(fixtures_dir):
    return str(fixtures_dir / "sources-3rows.md")


@pytest.fixture
def no_frontmatter_md(fixtures_dir):
    return str(fixtures_dir / "no-frontmatter.md")
