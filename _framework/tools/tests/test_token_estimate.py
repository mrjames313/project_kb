"""
Tests for _framework/tools/token_estimate.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from token_estimate import (
    CHARS_PER_TOKEN,
    estimate_role_preload,
    estimate_text_tokens,
    format_estimate,
    parse_role_preload,
)

from lint_helpers import make_minimal_repo, write_kb_page


# --- parse_role_preload ---

class TestParseRolePreload:
    def test_extracts_full_paths(self) -> None:
        role_text = textwrap.dedent("""
            ---
            role: x
            ---

            ## Preload context (full)

            Schema:
            1. /CLAUDE.md
            2. /_framework/schema/frontmatter.md

            Project:
            3. /commons/brief.md

            ## Operating boundaries

            - Writes allowed: /areas/x/**
        """).strip()
        result = parse_role_preload(role_text)
        assert result["full"] == [
            "CLAUDE.md",
            "_framework/schema/frontmatter.md",
            "commons/brief.md",
        ]
        assert result["frontmatter_patterns"] == []

    def test_extracts_frontmatter_patterns(self) -> None:
        role_text = textwrap.dedent("""
            ## Preload context (full)

            1. /CLAUDE.md

            ## Preload context (frontmatter only)

            Patterns:
            - /commons/kb/findings/
            - /areas/research/kb/

            ## Operating boundaries
        """).strip()
        result = parse_role_preload(role_text)
        assert result["full"] == ["CLAUDE.md"]
        assert result["frontmatter_patterns"] == [
            "commons/kb/findings/",
            "areas/research/kb/",
        ]

    def test_strips_inline_comments(self) -> None:
        role_text = textwrap.dedent("""
            ## Preload context (full)

            1. /CLAUDE.md
            2. /commons/POR.md   # only if capability: por
            3. /areas/x/pulse.md
        """).strip()
        result = parse_role_preload(role_text)
        assert result["full"] == ["CLAUDE.md", "commons/POR.md", "areas/x/pulse.md"]

    def test_skips_capability_markers(self) -> None:
        role_text = textwrap.dedent("""
            ## Preload context (full)

            1. /CLAUDE.md
            # capability: por
            2. /commons/POR.md
            # end capability: por
            3. /commons/brief.md
        """).strip()
        result = parse_role_preload(role_text)
        assert "commons/POR.md" in result["full"]
        # The marker lines themselves should not appear
        assert all("capability" not in p for p in result["full"])

    def test_ignores_non_path_list_items(self) -> None:
        role_text = textwrap.dedent("""
            ## Preload context (full)

            1. /CLAUDE.md
            2. not-a-path
            3. /commons/brief.md
        """).strip()
        result = parse_role_preload(role_text)
        assert result["full"] == ["CLAUDE.md", "commons/brief.md"]

    def test_empty_when_no_preload_sections(self) -> None:
        role_text = "## Operating boundaries\n\n- nothing\n"
        result = parse_role_preload(role_text)
        assert result == {"full": [], "frontmatter_patterns": []}


# --- estimate_text_tokens ---

class TestEstimateTextTokens:
    def test_empty_string(self) -> None:
        assert estimate_text_tokens("") == 0

    def test_short_string_minimum_one(self) -> None:
        # Even a single character should estimate as at least 1 token
        assert estimate_text_tokens("a") >= 1

    def test_proportional(self) -> None:
        n_chars = 1000
        result = estimate_text_tokens("a" * n_chars)
        # Should be approximately n_chars / CHARS_PER_TOKEN
        assert result == n_chars // CHARS_PER_TOKEN


# --- estimate_role_preload ---

class TestEstimateRolePreload:
    def _make_role_file(self, repo_root: Path, full_paths: list[str], frontmatter_patterns: list[str]) -> Path:
        role_dir = repo_root / "areas" / "research" / "roles" / "researcher"
        role_dir.mkdir(parents=True)
        role_path = role_dir / "role.md"
        lines = [
            "---",
            "role: researcher",
            "area: research",
            "summary: test role",
            "---",
            "",
            "## Preload context (full)",
            "",
        ]
        for i, p in enumerate(full_paths, 1):
            lines.append(f"{i}. /{p}")
        lines.extend(["", "## Preload context (frontmatter only)", ""])
        for p in frontmatter_patterns:
            lines.append(f"- /{p}")
        role_path.write_text("\n".join(lines))
        return role_path

    def test_full_preload_only(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        # Create some files for the role to point at
        (tmp_path / "commons" / "brief.md").write_text("x" * 800)  # ~200 tokens
        role_file = self._make_role_file(tmp_path, ["CLAUDE.md", "commons/brief.md"], [])
        # CLAUDE.md doesn't exist in this minimal repo; it'll be in missing_files
        result = estimate_role_preload(role_file, tmp_path)
        assert len(result.full_preload_files) == 1
        assert result.full_preload_files[0].path == "commons/brief.md"
        assert result.full_preload_tokens_est == 200
        assert "CLAUDE.md" in result.missing_files
        assert result.frontmatter_preload_tokens_est == 0

    def test_frontmatter_preload(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        # Create three kb pages
        write_kb_page(tmp_path, "areas/research", "finding", "a")
        write_kb_page(tmp_path, "areas/research", "finding", "b")
        write_kb_page(tmp_path, "areas/research", "finding", "c")
        role_file = self._make_role_file(tmp_path, [], ["areas/research/kb/findings/"])
        result = estimate_role_preload(role_file, tmp_path)
        # We should pick up 3 files
        assert len(result.frontmatter_preload_files) == 3
        # Tokens should be non-zero (each frontmatter is at least ~30 tokens)
        assert result.frontmatter_preload_tokens_est > 0

    def test_full_and_frontmatter_combined(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        (tmp_path / "commons" / "brief.md").write_text("brief content " * 50)
        write_kb_page(tmp_path, "areas/research", "finding", "a")
        role_file = self._make_role_file(
            tmp_path,
            ["commons/brief.md"],
            ["areas/research/kb/findings/"],
        )
        result = estimate_role_preload(role_file, tmp_path)
        assert result.full_preload_tokens_est > 0
        assert result.frontmatter_preload_tokens_est > 0
        assert result.total_preload_tokens_est == (
            result.full_preload_tokens_est + result.frontmatter_preload_tokens_est
        )

    def test_missing_pattern_dir_is_silent(self, tmp_path: Path) -> None:
        """Pattern resolves to non-existent dir -> no files, no error."""
        make_minimal_repo(tmp_path)
        role_file = self._make_role_file(tmp_path, [], ["areas/nonexistent/kb/"])
        result = estimate_role_preload(role_file, tmp_path)
        assert result.frontmatter_preload_files == []
        # Missing patterns don't go to missing_files (patterns ≠ files)
        assert result.missing_files == []

    def test_to_dict(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        (tmp_path / "commons" / "brief.md").write_text("hello world " * 100)
        role_file = self._make_role_file(tmp_path, ["commons/brief.md"], [])
        result = estimate_role_preload(role_file, tmp_path)
        d = result.to_dict()
        assert d["full_preload_files"] == 1
        assert d["full_preload_tokens_est"] > 0
        assert d["total_preload_tokens_est"] == d["full_preload_tokens_est"]
        assert isinstance(d["file_breakdown_full"], list)
        assert d["file_breakdown_full"][0]["path"] == "commons/brief.md"

    def test_role_file_outside_repo_root(self, tmp_path: Path) -> None:
        """Role file outside repo_root should not crash; uses absolute path."""
        make_minimal_repo(tmp_path)
        # Put the role file in a sibling dir, outside the repo
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        role_path = outside_dir / "role.md"
        role_path.write_text(
            "---\nrole: x\narea: x\nsummary: x\n---\n\n"
            "## Preload context (full)\n\n1. /commons/brief.md\n"
        )
        (tmp_path / "commons" / "brief.md").write_text("content")
        # Should not raise
        result = estimate_role_preload(role_path, tmp_path)
        assert result.role_file == str(role_path.resolve())
        # Cleanup
        role_path.unlink()
        outside_dir.rmdir()


# --- format_estimate ---

class TestFormatEstimate:
    def test_human_readable_output(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        (tmp_path / "commons" / "brief.md").write_text("content " * 200)
        role_dir = tmp_path / "areas" / "research" / "roles" / "researcher"
        role_dir.mkdir(parents=True)
        role_path = role_dir / "role.md"
        role_path.write_text(
            "---\nrole: x\narea: x\nsummary: x\n---\n\n"
            "## Preload context (full)\n\n1. /commons/brief.md\n"
        )
        result = estimate_role_preload(role_path, tmp_path)
        report = format_estimate(result)
        assert "Full preload" in report
        assert "TOTAL" in report
        assert "commons/brief.md" in report
