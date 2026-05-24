"""
Tests for _framework/tools/telemetry.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from telemetry import (
    iter_events,
    recent_sessions,
    session_end,
    session_start,
)

from lint_helpers import make_minimal_repo


def _make_role_file(repo_root: Path, role_name: str = "researcher", area: str = "research") -> Path:
    """Create a minimal role file."""
    role_dir = repo_root / "areas" / area / "roles" / role_name
    role_dir.mkdir(parents=True)
    role_path = role_dir / "role.md"
    # Reference a file that exists so estimate isn't all-missing
    (repo_root / "commons" / "brief.md").write_text("brief content " * 30)
    role_path.write_text(
        "---\n"
        f"role: {role_name}\n"
        f"area: {area}\n"
        "summary: test role\n"
        "---\n\n"
        "## Preload context (full)\n\n"
        "1. /commons/brief.md\n"
    )
    return role_path


class TestSessionStart:
    def test_writes_entry(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)
        entry = session_start(role_file, tmp_path)

        assert entry["event"] == "session_start"
        assert entry["role"] == "researcher"
        assert entry["area"] == "research"
        assert entry["full_preload_files"] == 1
        assert entry["total_preload_tokens_est"] > 0
        assert "session_id" in entry

    def test_creates_telemetry_dir(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)
        session_start(role_file, tmp_path)

        log = tmp_path / "_framework" / "telemetry" / "sessions.jsonl"
        assert log.is_file()
        # File contains one JSONL line
        lines = log.read_text().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event"] == "session_start"

    def test_writes_current_session_pointer(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)
        entry = session_start(role_file, tmp_path)
        pointer = tmp_path / "_framework" / "telemetry" / ".current-session"
        assert pointer.is_file()
        assert pointer.read_text().strip() == entry["session_id"]


class TestSessionEnd:
    def test_pairs_with_start(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)
        start_entry = session_start(role_file, tmp_path)
        end_entry = session_end(
            tmp_path,
            pages_cited=["areas/research/kb/findings/f-1.md"],
            bodies_loaded=["areas/research/kb/concepts/c-1.md"],
        )

        assert end_entry["session_id"] == start_entry["session_id"]
        assert end_entry["pages_cited"] == ["areas/research/kb/findings/f-1.md"]
        assert end_entry["bodies_loaded_beyond_preload"] == [
            "areas/research/kb/concepts/c-1.md"
        ]

    def test_clears_pointer(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)
        session_start(role_file, tmp_path)
        session_end(tmp_path)
        pointer = tmp_path / "_framework" / "telemetry" / ".current-session"
        assert not pointer.exists()

    def test_end_without_start(self, tmp_path: Path) -> None:
        """session_end called with no prior start should not crash; uses 'unknown' id."""
        make_minimal_repo(tmp_path)
        entry = session_end(tmp_path)
        assert entry["session_id"] == "unknown"

    def test_empty_lists_default(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        entry = session_end(tmp_path)
        assert entry["pages_cited"] == []
        assert entry["bodies_loaded_beyond_preload"] == []


class TestIterEvents:
    def test_empty_log(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        assert list(iter_events(tmp_path)) == []

    def test_reads_multiple_events(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)
        session_start(role_file, tmp_path)
        session_end(tmp_path)
        session_start(role_file, tmp_path)

        events = list(iter_events(tmp_path))
        assert len(events) == 3
        assert [e["event"] for e in events] == ["session_start", "session_end", "session_start"]


class TestRecentSessions:
    def test_pairs_start_and_end(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)

        session_start(role_file, tmp_path)
        # Sleep 1s to ensure distinct session_ids (which include seconds resolution)
        time.sleep(1)
        session_end(tmp_path)
        time.sleep(1)
        session_start(role_file, tmp_path)
        time.sleep(1)
        session_end(tmp_path)

        sessions = recent_sessions(tmp_path, n=10)
        assert len(sessions) == 2
        # Most recent first
        for s in sessions:
            assert s["start"] is not None
            assert s["end"] is not None

    def test_unpaired_start(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)
        session_start(role_file, tmp_path)  # no matching end

        sessions = recent_sessions(tmp_path, n=10)
        assert len(sessions) == 1
        assert sessions[0]["end"] is None

    def test_limits_to_n(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        role_file = _make_role_file(tmp_path)

        for _ in range(5):
            session_start(role_file, tmp_path)
            time.sleep(1)
            session_end(tmp_path)
            time.sleep(1)

        sessions = recent_sessions(tmp_path, n=3)
        assert len(sessions) == 3
