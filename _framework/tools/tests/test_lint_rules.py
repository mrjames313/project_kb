"""
Tests for lint rules in commit 2a.

Each rule gets a TestRuleNN class with at least one pass case and a fail case
per kind of violation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lint_rules import (
    rule_01_frontmatter,
    rule_02_forward_links,
    rule_03_backlinks,
    rule_05_supersession,
    rule_06_completeness,
    rule_07_pulse_size,
    rule_12_manifest,
    rule_15_index,
)

from lint_helpers import make_minimal_repo, write_kb_page


DEFAULT_CONFIG = {"lint": {"pulse_line_cap": 80}}


# --- Rule 1: Frontmatter validity ---

class TestRule01Frontmatter:
    def test_clean_repo(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(tmp_path, "areas/research", "finding", "ok")
        findings = rule_01_frontmatter.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []

    def test_missing_frontmatter_block(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        kb = tmp_path / "areas" / "research" / "kb" / "findings"
        kb.mkdir(parents=True)
        (kb / "f-2026-05-bad.md").write_text("# No frontmatter here\n\nJust body.\n")
        findings = rule_01_frontmatter.check(tmp_path, DEFAULT_CONFIG)
        assert any("missing frontmatter" in f.message for f in findings)

    def test_invalid_type(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "finding", "ok",
            frontmatter_overrides={"type": "bogus"},
        )
        findings = rule_01_frontmatter.check(tmp_path, DEFAULT_CONFIG)
        assert any("invalid type" in f.message for f in findings)

    def test_invalid_status_for_type(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "decision", "ok",
            frontmatter_overrides={"status": "developing"},  # not valid for decision
        )
        findings = rule_01_frontmatter.check(tmp_path, DEFAULT_CONFIG)
        assert any("invalid status" in f.message for f in findings)

    def test_missing_required_field(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        kb = tmp_path / "areas" / "research" / "kb" / "findings"
        kb.mkdir(parents=True)
        (kb / "f-2026-05-incomplete.md").write_text(
            "---\nid: f-2026-05-incomplete\ntitle: x\ntype: finding\n---\n\nbody\n"
        )
        findings = rule_01_frontmatter.check(tmp_path, DEFAULT_CONFIG)
        # Several required fields missing
        missing_msgs = [f.message for f in findings if "missing required" in f.message]
        assert len(missing_msgs) >= 3

    def test_malformed_yaml(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        kb = tmp_path / "areas" / "research" / "kb" / "findings"
        kb.mkdir(parents=True)
        (kb / "f-2026-05-broken.md").write_text(
            "---\nid: f-2026-05-broken\nthis is: not\n  : valid yaml\n---\n\nbody\n"
        )
        findings = rule_01_frontmatter.check(tmp_path, DEFAULT_CONFIG)
        assert any("malformed frontmatter" in f.message for f in findings)

    def test_bad_id_convention(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "finding", "ok",
            frontmatter_overrides={"id": "no-prefix-here"},
        )
        findings = rule_01_frontmatter.check(tmp_path, DEFAULT_CONFIG)
        assert any("does not match convention" in f.message for f in findings)


# --- Rule 2: Forward-link integrity ---

class TestRule02ForwardLinks:
    def test_resolved_link(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(tmp_path, "areas/research", "concept", "shot-noise")
        write_kb_page(
            tmp_path, "areas/research", "finding", "with-link",
            body="Builds on [[c-2026-05-shot-noise]].",
        )
        findings = rule_02_forward_links.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []

    def test_broken_link(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "finding", "broken-link",
            body="Links to [[c-2026-05-does-not-exist]].",
        )
        findings = rule_02_forward_links.check(tmp_path, DEFAULT_CONFIG)
        assert any("does not resolve" in f.message for f in findings)

    def test_raw_path_resolves(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        # Create the raw file
        raw_dir = tmp_path / "areas" / "research" / "raw" / "papers"
        raw_dir.mkdir(parents=True)
        (raw_dir / "paper.pdf").write_text("fake pdf bytes")
        # Create a source page pointing at it
        write_kb_page(
            tmp_path, "areas/research", "source", "paper",
            extra_frontmatter_yaml="provenance:\n  kind: external\n  retrieved: 2026-05-01\n  raw_path: areas/research/raw/papers/paper.pdf",
            frontmatter_overrides={"summary": "Test source"},
        )
        # Need to drop the default provenance our helper added — easier: just write a custom source.
        # Our helper already added one provenance; rewriting manually:
        page = tmp_path / "areas" / "research" / "kb" / "sources" / "s-2026-05-paper.md"
        page.write_text(
            "---\n"
            "id: s-2026-05-paper\n"
            "title: Test paper\n"
            "type: source\n"
            "status: active\n"
            "area: research\n"
            "created: 2026-05-08\n"
            "updated: 2026-05-08\n"
            "summary: Test source\n"
            "provenance:\n"
            "  kind: external\n"
            "  retrieved: 2026-05-01\n"
            "  raw_path: areas/research/raw/papers/paper.pdf\n"
            "---\n\n"
            "Body.\n"
        )
        findings = rule_02_forward_links.check(tmp_path, DEFAULT_CONFIG)
        # No findings about raw_path
        assert not any("raw_path" in f.message for f in findings)

    def test_raw_path_missing(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        page = tmp_path / "areas" / "research" / "kb" / "sources" / "s-2026-05-missing.md"
        page.parent.mkdir(parents=True)
        page.write_text(
            "---\n"
            "id: s-2026-05-missing\n"
            "title: x\ntype: source\nstatus: active\narea: research\n"
            "created: 2026-05-08\nupdated: 2026-05-08\nsummary: x\n"
            "provenance:\n  kind: external\n  raw_path: areas/research/raw/nope.pdf\n"
            "---\n\nx\n"
        )
        findings = rule_02_forward_links.check(tmp_path, DEFAULT_CONFIG)
        assert any("raw_path does not resolve" in f.message for f in findings)


# --- Rule 3: Backlink synchronization (fixup) ---

class TestRule03Backlinks:
    def test_writes_sidecars(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(tmp_path, "areas/research", "concept", "x")
        write_kb_page(
            tmp_path, "areas/research", "finding", "y",
            body="Builds on [[c-2026-05-x]].",
        )

        findings = rule_03_backlinks.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []

        # Sidecar for the finding should list the concept in links_out
        finding_sidecar = tmp_path / "areas/research/kb/findings/f-2026-05-y.md.links.json"
        assert finding_sidecar.is_file()
        import json
        data = json.loads(finding_sidecar.read_text())
        assert any("c-2026-05-x" in p for p in data["links_out"])

        # Sidecar for the concept should list the finding in links_in
        concept_sidecar = tmp_path / "areas/research/kb/concepts/c-2026-05-x.md.links.json"
        assert concept_sidecar.is_file()
        data = json.loads(concept_sidecar.read_text())
        assert any("f-2026-05-y" in p for p in data["links_in"])


# --- Rule 5: Supersession integrity ---

class TestRule05Supersession:
    def test_superseded_without_replacement(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "finding", "old",
            frontmatter_overrides={"status": "superseded"},
        )
        findings = rule_05_supersession.check(tmp_path, DEFAULT_CONFIG)
        assert any("superseded_by is not populated" in f.message for f in findings)

    def test_link_to_superseded(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(tmp_path, "areas/research", "finding", "new")
        write_kb_page(
            tmp_path, "areas/research", "finding", "old",
            frontmatter_overrides={"status": "superseded", "superseded_by": "[[f-2026-05-new]]"},
        )
        write_kb_page(
            tmp_path, "areas/research", "concept", "uses",
            body="Builds on [[f-2026-05-old]].",
        )
        findings = rule_05_supersession.check(tmp_path, DEFAULT_CONFIG)
        assert any("which is superseded" in f.message for f in findings)

    def test_clean_supersession(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(tmp_path, "areas/research", "finding", "new")
        write_kb_page(
            tmp_path, "areas/research", "finding", "old",
            frontmatter_overrides={"status": "superseded", "superseded_by": "[[f-2026-05-new]]"},
        )
        findings = rule_05_supersession.check(tmp_path, DEFAULT_CONFIG)
        # No link-to-superseded; old has its replacement set
        assert findings == []


# --- Rule 6: Type-specific completeness ---

class TestRule06Completeness:
    def test_concept_under_test_needs_evidence(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "concept", "ut",
            frontmatter_overrides={"status": "under_test"},
        )
        findings = rule_06_completeness.check(tmp_path, DEFAULT_CONFIG)
        assert any("needs non-empty `evidence`" in f.message for f in findings)

    def test_concept_developing_no_evidence_ok(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "concept", "dev",
            frontmatter_overrides={"status": "developing"},
        )
        findings = rule_06_completeness.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []

    def test_concept_supported_with_evidence_ok(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(
            tmp_path, "areas/research", "concept", "ok",
            frontmatter_overrides={
                "status": "supported",
                "evidence": ["[[s-foo]]", "[[s-bar]]"],
            },
        )
        findings = rule_06_completeness.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []

    def test_finding_needs_provenance(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        # Manually write a finding without provenance
        page = tmp_path / "areas/research/kb/findings/f-2026-05-noprov.md"
        page.parent.mkdir(parents=True)
        page.write_text(
            "---\n"
            "id: f-2026-05-noprov\ntitle: x\ntype: finding\nstatus: active\n"
            "area: research\ncreated: 2026-05-08\nupdated: 2026-05-08\nsummary: x\n"
            "---\n\nx\n"
        )
        findings = rule_06_completeness.check(tmp_path, DEFAULT_CONFIG)
        assert any("provenance" in f.message for f in findings)

    def test_decision_needs_alternatives_field(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        page = tmp_path / "areas/research/kb/decisions/d-2026-05-noalt.md"
        page.parent.mkdir(parents=True)
        page.write_text(
            "---\n"
            "id: d-2026-05-noalt\ntitle: x\ntype: decision\nstatus: active\n"
            "area: research\ncreated: 2026-05-08\nupdated: 2026-05-08\nsummary: x\n"
            "---\n\nx\n"
        )
        findings = rule_06_completeness.check(tmp_path, DEFAULT_CONFIG)
        assert any("alternatives_considered" in f.message for f in findings)


# --- Rule 7: Pulse size ---

class TestRule07PulseSize:
    def test_under_cap(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        (tmp_path / "commons" / "pulse.md").write_text("\n".join(["line"] * 50))
        findings = rule_07_pulse_size.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []

    def test_over_cap(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        (tmp_path / "commons" / "pulse.md").write_text("\n".join(["line"] * 200))
        findings = rule_07_pulse_size.check(tmp_path, DEFAULT_CONFIG)
        assert any("exceeds line cap" in f.message for f in findings)

    def test_per_area_pulse(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        area_pulse = tmp_path / "areas" / "research" / "pulse.md"
        area_pulse.parent.mkdir(parents=True)
        area_pulse.write_text("\n".join(["x"] * 200))
        findings = rule_07_pulse_size.check(tmp_path, DEFAULT_CONFIG)
        assert any("research/pulse.md" in f.file_path for f in findings)

    def test_custom_cap(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        (tmp_path / "commons" / "pulse.md").write_text("\n".join(["x"] * 30))
        # With cap of 20, should fire
        findings = rule_07_pulse_size.check(tmp_path, {"lint": {"pulse_line_cap": 20}})
        assert any("exceeds line cap" in f.message for f in findings)


# --- Rule 12: Data manifest integrity ---

class TestRule12Manifest:
    def _write_manifest(self, tmp_path: Path, **fm_overrides) -> Path:
        manifest_dir = tmp_path / "areas/research/data/manifests"
        manifest_dir.mkdir(parents=True)
        fm = {
            "id": "m-2026-05-test",
            "title": "Test",
            "type": "source",
            "status": "active",
            "area": "research",
            "created": "2026-05-08",
            "updated": "2026-05-08",
            "summary": "test manifest",
            "storage_uri": "s3://bucket/dataset",
            "provenance": {"kind": "internal-experiment"},
            "context_pages": ["[[c-foo]]"],
        }
        fm.update(fm_overrides)
        lines = ["---"]
        for k, v in fm.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            elif isinstance(v, dict):
                lines.append(f"{k}:")
                for sk, sv in v.items():
                    lines.append(f"  {sk}: {sv}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("body")
        path = manifest_dir / "m-2026-05-test.md"
        path.write_text("\n".join(lines) + "\n")
        return path

    def test_valid_manifest(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        self._write_manifest(tmp_path)
        findings = rule_12_manifest.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []

    def test_missing_storage_uri(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        self._write_manifest(tmp_path, storage_uri="")
        findings = rule_12_manifest.check(tmp_path, DEFAULT_CONFIG)
        assert any("storage_uri" in f.message for f in findings)

    def test_missing_context_pages(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        self._write_manifest(tmp_path, context_pages=[])
        findings = rule_12_manifest.check(tmp_path, DEFAULT_CONFIG)
        assert any("context_pages" in f.message for f in findings)


# --- Rule 15: Index maintenance (fixup) ---

class TestRule15Index:
    def test_generates_areas_index(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        # Add an area with a brief
        area = tmp_path / "areas" / "research"
        area.mkdir(parents=True)
        (area / "brief.md").write_text("# Research\n\nWe investigate optical noise.\n")

        findings = rule_15_index.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []
        idx = tmp_path / "areas-index.md"
        assert idx.is_file()
        content = idx.read_text()
        assert "research" in content
        assert "investigate optical noise" in content

    def test_generates_kb_index(self, tmp_path: Path) -> None:
        make_minimal_repo(tmp_path)
        write_kb_page(tmp_path, "areas/research", "finding", "shot-noise")
        write_kb_page(
            tmp_path, "areas/research", "concept", "ut1",
            frontmatter_overrides={
                "status": "under_test",
                "evidence": ["[[s-1]]"],
            },
        )

        findings = rule_15_index.check(tmp_path, DEFAULT_CONFIG)
        assert findings == []
        kb_index = tmp_path / "areas/research/kb/index.md"
        assert kb_index.is_file()
        content = kb_index.read_text()
        assert "Findings" in content
        assert "Concepts under test" in content
        assert "f-2026-05-shot-noise" in content
        assert "c-2026-05-ut1" in content
