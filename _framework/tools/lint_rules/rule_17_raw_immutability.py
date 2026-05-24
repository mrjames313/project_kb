"""
Rule 17 — Raw immutability.

Files in raw/ are immutable once committed. New files may be added; existing
files must not be edited or deleted.

Implementation: for each file in any raw/ directory, check `git log --follow`
on the file. If it has more than one commit touching it, that's a modification
after initial add — error. If it shows up as deleted, also error.

The check is forgiving in two cases:
1. Files not yet committed (newly added): allowed.
2. Files in a single commit: allowed (that's the initial add).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from activity_days import GitError, is_git_repo
from common import Finding, iter_raw_files

RULE_ID = "rule_17"
SEVERITY = "error"


def _commit_count_for_file(repo_root: Path, rel_path: str) -> int:
    """Return the number of commits that touched a file. 0 if untracked."""
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--oneline", "--", rel_path],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return 0
    return len([line for line in result.stdout.splitlines() if line.strip()])


def _deleted_raw_files(repo_root: Path) -> list[str]:
    """Find raw/ files that have been deleted (per git status against HEAD)."""
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--diff-filter=D", "--name-only", "--pretty=format:"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []
    deleted: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Path is relative to repo root
        parts = Path(line).parts
        if "raw" in parts:
            # Only flag if the file isn't currently present (truly deleted)
            if not (repo_root / line).exists():
                deleted.add(line)
    return sorted(deleted)


def check(repo_root: Path, config: dict) -> list[Finding]:
    findings: list[Finding] = []

    if not is_git_repo(repo_root):
        # Without git history, we can't enforce immutability.
        # This isn't an error in the rule — it's just inapplicable.
        return findings

    for path in iter_raw_files(repo_root):
        rel = path.relative_to(repo_root)
        rel_str = str(rel)
        count = _commit_count_for_file(repo_root, rel_str)
        if count > 1:
            findings.append(
                Finding(
                    RULE_ID,
                    SEVERITY,
                    rel_str,
                    f"raw file has been modified after initial commit ({count} commits touching it)",
                    suggestion="raw materials are immutable; revert or move to a new file",
                )
            )

    # Detect deletions
    for deleted in _deleted_raw_files(repo_root):
        findings.append(
            Finding(
                RULE_ID,
                SEVERITY,
                deleted,
                "raw file has been deleted from history",
                suggestion="raw materials are immutable once added; deletion is not permitted",
            )
        )

    return findings
