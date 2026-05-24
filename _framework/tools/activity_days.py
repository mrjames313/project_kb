"""
Active days helper — computes the number of days on which the project had at
least one commit, used as the unit for all activity-based thresholds in the
framework.

A cold project (no commits for a while) doesn't generate spurious "stale" warnings:
when you return after a break, day 1 of your return is active day 1 since the break.
"""

from __future__ import annotations

import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path


class GitError(RuntimeError):
    """Raised when git commands fail or the directory is not a git repo."""


def _run_git(args: list[str], cwd: Path | str) -> str:
    """Run a git command and return stdout. Raise GitError on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except FileNotFoundError as e:
        raise GitError("git executable not found on PATH") from e
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() or e.stdout.strip() or "unknown error"
        raise GitError(f"git {' '.join(args)} failed: {msg}") from e


def _normalize_date(d: date | datetime | str) -> str:
    """Convert date-like input to YYYY-MM-DD string for git --since."""
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    if isinstance(d, str):
        # Validate format
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"date string must be YYYY-MM-DD, got {d!r}") from e
        return d
    raise TypeError(f"expected date, datetime, or YYYY-MM-DD str, got {type(d).__name__}")


def active_days_since(
    since: date | datetime | str,
    *,
    repo_root: Path | str = ".",
    include_today_uncommitted: bool = False,
) -> int:
    """
    Return the number of distinct days the repo had at least one commit
    on or after `since`.

    If `include_today_uncommitted` is True and today is not already in the
    commit history, today is counted as an active day (useful when an
    in-flight session counts toward activity before its first commit).
    """
    since_str = _normalize_date(since)
    output = _run_git(
        ["log", "--all", f"--since={since_str} 00:00:00", "--pretty=format:%cs"],
        cwd=repo_root,
    )
    # %cs is committer-date short, YYYY-MM-DD; empty line per commit
    dates = {line.strip() for line in output.splitlines() if line.strip()}

    if include_today_uncommitted:
        today = date.today().isoformat()
        dates.add(today)

    return len(dates)


def active_days_between(
    start: date | datetime | str,
    end: date | datetime | str,
    *,
    repo_root: Path | str = ".",
) -> int:
    """
    Return the number of distinct days the repo had at least one commit
    between `start` and `end` (inclusive on both ends).
    """
    start_str = _normalize_date(start)
    end_str = _normalize_date(end)
    output = _run_git(
        [
            "log",
            "--all",
            f"--since={start_str} 00:00:00",
            f"--until={end_str} 23:59:59",
            "--pretty=format:%cs",
        ],
        cwd=repo_root,
    )
    dates = {line.strip() for line in output.splitlines() if line.strip()}
    return len(dates)


def active_days_back(
    n_active_days: int,
    *,
    repo_root: Path | str = ".",
) -> date | None:
    """
    Walk backwards through commit history; return the calendar date that
    is `n_active_days` active days in the past. Returns None if the repo
    doesn't have that many active days yet.

    Useful for computing thresholds like "concept under_test older than
    30 active days" — pass 30, get the calendar date, compare to the
    concept's `updated`.
    """
    if n_active_days <= 0:
        raise ValueError("n_active_days must be positive")

    try:
        output = _run_git(
            ["log", "--all", "--pretty=format:%cs"],
            cwd=repo_root,
        )
    except GitError:
        # Not a git repo, or no commits yet. We have no history to walk back
        # through; treat that the same as "insufficient history".
        return None
    # Distinct dates, sorted newest first
    dates = sorted({line.strip() for line in output.splitlines() if line.strip()}, reverse=True)

    if len(dates) < n_active_days:
        return None

    target = dates[n_active_days - 1]
    return datetime.strptime(target, "%Y-%m-%d").date()


def is_git_repo(path: Path | str = ".") -> bool:
    """Check whether the given path is inside a git working tree."""
    try:
        _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
        return True
    except GitError:
        return False


def _main() -> int:
    """CLI entry point: print active days since a given date."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute git-log-derived active days in the current repo."
    )
    parser.add_argument("--since", help="YYYY-MM-DD; count active days since this date")
    parser.add_argument("--back", type=int, help="N active days; print the calendar date N active days ago")
    parser.add_argument("--repo", default=".", help="path to repo root (default: current dir)")
    args = parser.parse_args()

    if not args.since and not args.back:
        parser.error("provide either --since YYYY-MM-DD or --back N")

    try:
        if args.since:
            n = active_days_since(args.since, repo_root=args.repo)
            print(n)
        else:
            d = active_days_back(args.back, repo_root=args.repo)
            if d is None:
                print("(insufficient history)")
                return 1
            print(d.isoformat())
    except (GitError, ValueError) as e:
        print(f"error: {e}", file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
