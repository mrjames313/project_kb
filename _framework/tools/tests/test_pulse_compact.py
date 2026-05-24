"""
Tests for _framework/tools/pulse_compact.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pulse_compact import (
    LogEntry,
    compact_area,
    parse_pulse_log,
    split_sections,
    update_current_focus,
    update_open_questions,
)

from lint_helpers import make_minimal_repo, write_kb_page


DEFAULT_CONFIG = {"lint": {"pulse_line_cap": 80, "recent_decisions_window_active_days": 7}}


# --- parse_pulse_log ---

class TestParsePulseLog:
    def test_empty_log(self) -> None:
        assert parse_pulse_log("") == []

    def test_single_decision_entry(self) -> None:
        log = textwrap.dedent("""
            ## [2026-05-08 09:14] decision optics-researcher
            Adopted bias current of 1 mA per measurement constraints.
            → to be filed: decisions/d-2026-05-04-bias-current
        """).strip()
        entries = parse_pulse_log(log)
        assert len(entries) == 1
        assert entries[0].timestamp == "2026-05-08 09:14"
        assert entries[0].event_type == "decision"
        assert entries[0].role == "optics-researcher"
        assert "1 mA" in entries[0].description
        assert entries[0].filed_path == "decisions/d-2026-05-04-bias-current"

    def test_multiple_entries(self) -> None:
        log = textwrap.dedent("""
            ## [2026-05-08 09:14] decision optics-researcher
            First decision.
            → to be filed: decisions/d-1

            ## [2026-05-08 11:22] finding optics-researcher
            First finding.
            → to be filed: findings/f-1

            ## [2026-05-08 13:45] focus-shift optics-researcher
            Switching gears.
        """).strip()
        entries = parse_pulse_log(log)
        assert len(entries) == 3
        assert [e.event_type for e in entries] == ["decision", "finding", "focus-shift"]
        assert entries[2].filed_path is None  # focus-shift has no filed_path

    def test_handles_missing_role(self) -> None:
        log = "## [2026-05-08 09:14] decision\nNo role specified.\n"
        entries = parse_pulse_log(log)
        assert len(entries) == 1
        assert entries[0].role is None


# --- split_sections ---

class TestSplitSections:
    def test_basic_sections(self) -> None:
        text = textwrap.dedent("""
            # Header

            Preamble line.

            ## Current focus

            Some focus text.

            ## Open questions

            - q1
            - q2
        """).strip()
        sections = split_sections(text)
        assert "" in sections  # preamble
        assert "current focus" in sections
        assert "open questions" in sections
        # The preamble holds the title and any pre-section text
        assert any("Header" in line for line in sections[""])

    def test_parenthetical_in_heading_stripped(self) -> None:
        text = "## Recent decisions (last 7 active days)\n- d1\n"
        sections = split_sections(text)
        assert "recent decisions" in sections


# --- update_current_focus ---

class TestUpdateCurrentFocus:
    def test_no_focus_shift_leaves_unchanged(self) -> None:
        existing = ["## Current focus", "", "Previous focus.", ""]
        result = update_current_focus(existing, [])
        assert result == existing

    def test_focus_shift_replaces(self) -> None:
        existing = ["## Current focus", "", "Old focus.", ""]
        log_entries = [
            LogEntry(
                timestamp="2026-05-08 09:00",
                event_type="focus-shift",
                role="r",
                description="New focus on noise floor.",
                filed_path=None,
            )
        ]
        result = update_current_focus(existing, log_entries)
        assert any("New focus on noise floor" in line for line in result)
        assert not any("Old focus" in line for line in result)

    def test_multiple_shifts_latest_wins(self) -> None:
        existing = ["## Current focus", "", "Old.", ""]
        log_entries = [
            LogEntry("2026-05-08 09:00", "focus-shift", "r", "First shift.", None),
            LogEntry("2026-05-08 14:00", "focus-shift", "r", "Latest shift.", None),
        ]
        result = update_current_focus(existing, log_entries)
        assert any("Latest shift" in line for line in result)
        assert not any("First shift" in line for line in result)


# --- update_open_questions ---

class TestUpdateOpenQuestions:
    def test_adds_new_question(self) -> None:
        existing = ["## Open questions", "", "- Existing question?", ""]
        log_entries = [
            LogEntry("2026-05-08 09:00", "question", "r", "New question?", None)
        ]
        result = update_open_questions(existing, log_entries)
        assert any("Existing question?" in line for line in result)
        assert any("New question?" in line for line in result)

    def test_deduplicates(self) -> None:
        existing = ["## Open questions", "", "- Same question?", ""]
        log_entries = [
            LogEntry("2026-05-08 09:00", "question", "r", "Same question?", None)
        ]
        result = update_open_questions(existing, log_entries)
        # Should appear only once
        same_count = sum(1 for line in result if "Same question?" in line)
        assert same_count == 1

    def test_replaces_none_placeholder(self) -> None:
        existing = ["## Open questions", "", "_None yet._", ""]
        log_entries = [
            LogEntry("2026-05-08 09:00", "question", "r", "First question?", None)
        ]
        result = update_open_questions(existing, log_entries)
        assert any("First question?" in line for line in result)
        assert not any("_None yet._" in line for line in result)


# --- compact_area ---

class TestCompactArea:
    def _setup_area(self, tmp_path: Path) -> Path:
        """Create a minimal area with pulse.md, _journal/pulse.log, and empty kb/."""
        area_dir = tmp_path / "areas" / "research"
        (area_dir / "kb" / "findings").mkdir(parents=True)
        (area_dir / "kb" / "decisions").mkdir(parents=True)
        (area_dir / "kb" / "concepts").mkdir(parents=True)
        (area_dir / "kb" / "sources").mkdir(parents=True)
        (area_dir / "_journal").mkdir(parents=True)
        # Empty pulse.md template
        (area_dir / "pulse.md").write_text(textwrap.dedent("""
            # research — pulse

            _Initialized: 2026-05-08_

            ## Current focus

            _(set when work begins)_

            ## Recent decisions (last 7 active days)

            _None yet._

            ## Active concepts under test

            _None yet._

            ## Open questions

            _None yet._

            ## Recent findings (last 5)

            _None yet._
        """).strip() + "\n")
        (area_dir / "_journal" / "pulse.log").write_text("")
        return area_dir

    def test_empty_log_idempotent(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        result = compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        assert result.entries_compacted == 0
        assert not result.over_cap
        # pulse.md should still exist
        assert (area_dir / "pulse.md").is_file()

    def test_regenerates_recent_findings_from_kb(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        # Add two findings to the kb
        write_kb_page(tmp_path, "areas/research", "finding", "a")
        write_kb_page(tmp_path, "areas/research", "finding", "b")
        compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        pulse_content = (area_dir / "pulse.md").read_text()
        assert "f-2026-05-a" in pulse_content
        assert "f-2026-05-b" in pulse_content

    def test_regenerates_concepts_under_test(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "concept", "ut1",
            frontmatter_overrides={"status": "under_test", "evidence": ["[[s-foo]]"]},
        )
        write_kb_page(
            tmp_path, "areas/research", "concept", "dev1",
            frontmatter_overrides={"status": "developing"},
        )
        compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        pulse_content = (area_dir / "pulse.md").read_text()
        # Only the under_test one appears in that section
        assert "c-2026-05-ut1" in pulse_content
        # The developing concept doesn't show up as "under test"
        section_after_under_test = pulse_content.split("## Active concepts under test")[1]
        section_under_test_only = section_after_under_test.split("##")[0]
        assert "c-2026-05-dev1" not in section_under_test_only

    def test_log_focus_shift_updates_current_focus(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        (area_dir / "_journal" / "pulse.log").write_text(textwrap.dedent("""
            ## [2026-05-08 13:45] focus-shift optics-researcher
            Now investigating 1/f noise.
        """).strip() + "\n")
        compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        pulse_content = (area_dir / "pulse.md").read_text()
        assert "1/f noise" in pulse_content

    def test_log_question_added_to_open_questions(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        (area_dir / "_journal" / "pulse.log").write_text(textwrap.dedent("""
            ## [2026-05-08 11:00] question optics-researcher
            Does bias direction affect noise floor?
        """).strip() + "\n")
        compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        pulse_content = (area_dir / "pulse.md").read_text()
        assert "Does bias direction affect noise floor?" in pulse_content

    def test_log_is_truncated_after_compaction(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        (area_dir / "_journal" / "pulse.log").write_text("## [2026-05-08 09:00] question r\nq?\n")
        compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        log_after = (area_dir / "_journal" / "pulse.log").read_text()
        assert log_after == ""

    def test_missing_filed_path_warned(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        (area_dir / "_journal" / "pulse.log").write_text(textwrap.dedent("""
            ## [2026-05-08 09:00] decision r
            A decision.
            → to be filed: decisions/d-2026-05-not-actually-filed
        """).strip() + "\n")
        result = compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        assert "decisions/d-2026-05-not-actually-filed" in result.missing_filed_paths

    def test_over_cap_detected(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        # Add 20 findings to ensure pulse will be bigger than tight cap
        for i in range(20):
            write_kb_page(tmp_path, "areas/research", "finding", f"f{i}")
        result = compact_area(area_dir, tmp_path, {"lint": {"pulse_line_cap": 10, "recent_decisions_window_active_days": 7}})
        assert result.over_cap

    def test_idempotent(self, tmp_path: Path) -> None:
        """Running compact twice produces identical pulse.md the second time."""
        make_minimal_repo(tmp_path)
        area_dir = self._setup_area(tmp_path)
        write_kb_page(tmp_path, "areas/research", "finding", "a")
        compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        first = (area_dir / "pulse.md").read_text()
        compact_area(area_dir, tmp_path, DEFAULT_CONFIG)
        second = (area_dir / "pulse.md").read_text()
        assert first == second
