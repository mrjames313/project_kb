"""
Tests for _framework/tools/manifest_validate.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from manifest_validate import validate_manifest

from lint_helpers import make_minimal_repo


def _write_manifest(repo_root: Path, **fm_overrides) -> Path:
    """Write a single manifest file with valid defaults plus overrides."""
    manifest_dir = repo_root / "areas" / "research" / "data" / "manifests"
    manifest_dir.mkdir(parents=True)
    fm_lines = [
        "id: m-2026-05-test",
        "title: Test manifest",
        "type: source",
        "status: active",
        "area: research",
        "created: 2026-05-08",
        "updated: 2026-05-08",
        "summary: Test manifest.",
        "storage_uri: s3://bucket/dataset",
        "provenance:",
        "  kind: internal-experiment",
        "  acquired_on: 2026-05-04",
        "context_pages:",
        "  - \"[[c-foo]]\"",
    ]
    # Apply overrides — for simplicity, just append. Overrides replace earlier values.
    for k, v in fm_overrides.items():
        if v is None:
            # Remove the field — re-emit without it
            fm_lines = [line for line in fm_lines if not line.startswith(f"{k}:")]
        elif isinstance(v, list):
            fm_lines = [line for line in fm_lines if not line.startswith(f"{k}:") and not line.startswith(f"  - \"[[")]
            fm_lines.append(f"{k}:")
            if not v:
                fm_lines[-1] = f"{k}: []"
            else:
                for item in v:
                    fm_lines.append(f"  - {item}")
        else:
            fm_lines = [line if not line.startswith(f"{k}:") else f"{k}: {v}" for line in fm_lines]

    path = manifest_dir / "m-2026-05-test.md"
    content = "---\n" + "\n".join(fm_lines) + "\n---\n\nManifest body.\n"
    path.write_text(content)
    return path


class TestValidateManifest:
    def test_clean_manifest(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        path = _write_manifest(tmp_path)
        findings = validate_manifest(path, tmp_path)
        assert findings == []

    def test_missing_storage_uri(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        path = _write_manifest(tmp_path, storage_uri="")
        findings = validate_manifest(path, tmp_path)
        assert any("storage_uri" in f.message for f in findings)

    def test_missing_provenance(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        # Manually write a manifest without provenance
        manifest_dir = tmp_path / "areas/research/data/manifests"
        manifest_dir.mkdir(parents=True)
        path = manifest_dir / "m-no-prov.md"
        path.write_text(textwrap.dedent("""
            ---
            id: m-2026-05-noprov
            title: No provenance
            type: source
            status: active
            area: research
            created: 2026-05-08
            updated: 2026-05-08
            summary: x
            storage_uri: s3://x/y
            context_pages:
              - "[[c-foo]]"
            ---

            body
        """).strip() + "\n")
        findings = validate_manifest(path, tmp_path)
        assert any("provenance" in f.message for f in findings)

    def test_empty_context_pages(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        # Manually write
        manifest_dir = tmp_path / "areas/research/data/manifests"
        manifest_dir.mkdir(parents=True)
        path = manifest_dir / "m-empty-ctx.md"
        path.write_text(textwrap.dedent("""
            ---
            id: m-2026-05-empty
            title: Empty context
            type: source
            status: active
            area: research
            created: 2026-05-08
            updated: 2026-05-08
            summary: x
            storage_uri: s3://x/y
            provenance:
              kind: external
            context_pages: []
            ---

            body
        """).strip() + "\n")
        findings = validate_manifest(path, tmp_path)
        assert any("context_pages" in f.message for f in findings)

    def test_file_not_found(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        findings = validate_manifest(tmp_path / "nope.md", tmp_path)
        assert any("not found" in f.message for f in findings)

    def test_no_frontmatter(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        path = tmp_path / "areas" / "research" / "data" / "manifests" / "m.md"
        path.parent.mkdir(parents=True)
        path.write_text("just body, no frontmatter\n")
        findings = validate_manifest(path, tmp_path)
        assert any("missing frontmatter" in f.message for f in findings)

    def test_malformed_yaml(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        path = tmp_path / "areas" / "research" / "data" / "manifests" / "m.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\nthis is: not\n  : valid yaml\n---\n\nbody\n")
        findings = validate_manifest(path, tmp_path)
        assert any("malformed frontmatter" in f.message for f in findings)
