"""
Tests for _framework/tools/activity_days.py
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from activity_days import (
    GitError,
    active_days_back,
    active_days_between,
    active_days_since,
    is_git_repo,
)

from conftest import days_ago, make_commit


class TestNormalizeDate:
    def test_accepts_string(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date="2026-01-01")
        n = active_days_since("2025-12-31", repo_root=git_repo)
        assert n == 1

    def test_accepts_date(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date="2026-01-01")
        n = active_days_since(date(2025, 12, 31), repo_root=git_repo)
        assert n == 1

    def test_accepts_datetime(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date="2026-01-01")
        n = active_days_since(datetime(2025, 12, 31, 12, 0, 0), repo_root=git_repo)
        assert n == 1

    def test_rejects_malformed_string(self, git_repo: Path) -> None:
        with pytest.raises(ValueError):
            active_days_since("not-a-date", repo_root=git_repo)

    def test_rejects_wrong_type(self, git_repo: Path) -> None:
        with pytest.raises(TypeError):
            active_days_since(42, repo_root=git_repo)  # type: ignore[arg-type]


class TestActiveDaysSince:
    def test_empty_repo_returns_zero(self, git_repo: Path) -> None:
        """Empty repo (no commits yet) returns 0 active days, not an error."""
        n = active_days_since("2026-01-01", repo_root=git_repo)
        assert n == 0

    def test_single_commit(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date=days_ago(5))
        n = active_days_since(days_ago(10), repo_root=git_repo)
        assert n == 1

    def test_multiple_commits_same_day(self, git_repo: Path) -> None:
        d = days_ago(3)
        make_commit(git_repo, "a.txt", commit_date=d)
        make_commit(git_repo, "b.txt", commit_date=d)
        make_commit(git_repo, "c.txt", commit_date=d)
        n = active_days_since(days_ago(10), repo_root=git_repo)
        assert n == 1  # all same day

    def test_multiple_distinct_days(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date=days_ago(5))
        make_commit(git_repo, "b.txt", commit_date=days_ago(3))
        make_commit(git_repo, "c.txt", commit_date=days_ago(1))
        n = active_days_since(days_ago(10), repo_root=git_repo)
        assert n == 3

    def test_excludes_commits_before_since(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date=days_ago(20))
        make_commit(git_repo, "b.txt", commit_date=days_ago(2))
        n = active_days_since(days_ago(10), repo_root=git_repo)
        assert n == 1  # only the recent one

    def test_include_today_uncommitted(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date=days_ago(5))
        # No commit today
        n_without = active_days_since(days_ago(10), repo_root=git_repo)
        n_with = active_days_since(
            days_ago(10), repo_root=git_repo, include_today_uncommitted=True
        )
        assert n_with == n_without + 1


class TestActiveDaysBetween:
    def test_inclusive_range(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date="2026-01-01")
        make_commit(git_repo, "b.txt", commit_date="2026-01-05")
        make_commit(git_repo, "c.txt", commit_date="2026-01-10")
        n = active_days_between("2026-01-01", "2026-01-10", repo_root=git_repo)
        assert n == 3

    def test_excludes_outside_range(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date="2025-12-30")
        make_commit(git_repo, "b.txt", commit_date="2026-01-05")
        make_commit(git_repo, "c.txt", commit_date="2026-02-01")
        n = active_days_between("2026-01-01", "2026-01-31", repo_root=git_repo)
        assert n == 1


class TestActiveDaysBack:
    def test_rejects_zero_or_negative(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt")
        with pytest.raises(ValueError):
            active_days_back(0, repo_root=git_repo)
        with pytest.raises(ValueError):
            active_days_back(-3, repo_root=git_repo)

    def test_returns_none_if_insufficient_history(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date=days_ago(2))
        result = active_days_back(10, repo_root=git_repo)
        assert result is None

    def test_returns_correct_date(self, git_repo: Path) -> None:
        make_commit(git_repo, "a.txt", commit_date="2026-01-01")
        make_commit(git_repo, "b.txt", commit_date="2026-01-05")
        make_commit(git_repo, "c.txt", commit_date="2026-01-10")
        # 1 active day back = today's most recent active day = 2026-01-10
        # 2 active days back = 2026-01-05
        # 3 active days back = 2026-01-01
        assert active_days_back(1, repo_root=git_repo) == date(2026, 1, 10)
        assert active_days_back(2, repo_root=git_repo) == date(2026, 1, 5)
        assert active_days_back(3, repo_root=git_repo) == date(2026, 1, 1)


class TestIsGitRepo:
    def test_returns_true_for_git_repo(self, git_repo: Path) -> None:
        assert is_git_repo(git_repo)

    def test_returns_false_for_non_repo(self, tmp_path: Path) -> None:
        assert not is_git_repo(tmp_path)


class TestColdProjectBehavior:
    """Verify the 'active days resume from your return' property."""

    def test_long_gap_then_return(self, git_repo: Path) -> None:
        # Three months ago: a flurry of activity
        make_commit(git_repo, "a.txt", commit_date=days_ago(95))
        make_commit(git_repo, "b.txt", commit_date=days_ago(94))
        make_commit(git_repo, "c.txt", commit_date=days_ago(93))
        # Then 90 days of nothing.
        # Today: returning to the project.
        make_commit(git_repo, "d.txt", commit_date=days_ago(0))

        # Active days in the last 30 calendar days:
        n_recent = active_days_since(days_ago(30), repo_root=git_repo)
        assert n_recent == 1  # only today's commit counts; the gap doesn't fabricate days
