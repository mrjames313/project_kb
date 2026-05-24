"""
Tests for rule 17 (raw immutability). Uses git commits to set up scenarios.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from lint_rules import rule_17_raw_immutability

from conftest import make_commit
from lint_helpers import make_minimal_repo


DEFAULT_CONFIG = {"lint": {}}


@pytest.fixture
def repo_with_raw(tmp_path: Path) -> Path:
    """A git-initialized repo with the framework skeleton and a raw/ directory."""
    make_minimal_repo(tmp_path)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    raw_dir = tmp_path / "areas" / "research" / "raw" / "papers"
    raw_dir.mkdir(parents=True)
    return tmp_path


class TestRule17:
    def test_single_commit_ok(self, repo_with_raw: Path) -> None:
        """A raw file in exactly one commit is fine (initial add)."""
        paper = repo_with_raw / "areas/research/raw/papers/paper.pdf"
        paper.write_text("paper content v1")
        make_commit(repo_with_raw, "areas/research/raw/papers/paper.pdf", content="paper content v1")
        findings = rule_17_raw_immutability.check(repo_with_raw, DEFAULT_CONFIG)
        assert findings == []

    def test_modified_raw_flagged(self, repo_with_raw: Path) -> None:
        """A raw file modified after initial commit is flagged."""
        rel = "areas/research/raw/papers/paper.pdf"
        make_commit(repo_with_raw, rel, content="v1")
        make_commit(repo_with_raw, rel, content="v2", message="modify raw — should be illegal")

        findings = rule_17_raw_immutability.check(repo_with_raw, DEFAULT_CONFIG)
        assert any("modified after initial commit" in f.message for f in findings)
        assert any(f.file_path == rel for f in findings)

    def test_deleted_raw_flagged(self, repo_with_raw: Path) -> None:
        """A raw file deleted from history is flagged."""
        rel = "areas/research/raw/papers/paper.pdf"
        make_commit(repo_with_raw, rel, content="v1")
        # Delete and commit
        (repo_with_raw / rel).unlink()
        subprocess.run(["git", "add", "-A"], cwd=repo_with_raw, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "delete raw — should be illegal"],
            cwd=repo_with_raw, check=True,
        )

        findings = rule_17_raw_immutability.check(repo_with_raw, DEFAULT_CONFIG)
        assert any("deleted from history" in f.message for f in findings)

    def test_uncommitted_raw_file_ok(self, repo_with_raw: Path) -> None:
        """A newly-added raw file not yet committed is fine."""
        # Make at least one commit to establish HEAD (so git log doesn't error)
        make_commit(repo_with_raw, "README.md", content="initial")
        # Add a raw file but don't commit yet
        paper = repo_with_raw / "areas/research/raw/papers/new.pdf"
        paper.write_text("freshly added")
        # The check should not flag it (it's untracked)
        findings = rule_17_raw_immutability.check(repo_with_raw, DEFAULT_CONFIG)
        # No "modified" complaint for new.pdf
        assert not any(
            "areas/research/raw/papers/new.pdf" in f.file_path
            and "modified after initial commit" in f.message
            for f in findings
        )

    def test_non_git_repo_silent(self, tmp_path: Path) -> None:
        """Without a git repo, the rule is inapplicable and produces no findings."""
        make_minimal_repo(tmp_path)
        raw = tmp_path / "areas/research/raw/papers"
        raw.mkdir(parents=True)
        (raw / "paper.pdf").write_text("anything")
        # Note: no git init
        findings = rule_17_raw_immutability.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []
