"""
Rule 2 — Forward-link integrity.

- Every [[wikilink]] in a kb page resolves to an existing kb page.
- Every source page's provenance.raw_path resolves to an existing file.

Builds an index of available wikilink targets first, then validates each
forward link from every kb page against it.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from common import (
    Finding,
    extract_wikilinks,
    iter_kb_pages,
    parse_frontmatter,
)

RULE_ID = "rule_02"
SEVERITY = "error"


def _build_wikilink_index(repo_root: Path) -> dict[str, Path]:
    """
    Build a map from wikilink target to the resolving file path.

    Targets are matched in priority order: full relative path (e.g.,
    "concepts/c-2026-04-shot-noise"), then bare id ("c-2026-04-shot-noise").
    """
    index: dict[str, Path] = {}
    for page in iter_kb_pages(repo_root):
        rel = page.relative_to(repo_root)
        # Strip the leading "areas/<area>/kb/" or "commons/kb/" to get the
        # within-kb path the wikilink would use, like "concepts/c-2026-...".
        # We also register the bare id for convenience.
        parts = rel.parts
        if "kb" in parts:
            kb_idx = parts.index("kb")
            within_kb = "/".join(parts[kb_idx + 1:])
            # Without extension
            target_with_dir = within_kb[:-3] if within_kb.endswith(".md") else within_kb
            index[target_with_dir] = page
            # Also register bare id (the filename without extension)
            bare = page.stem
            index.setdefault(bare, page)
    return index


def _check_page(
    path: Path, repo_root: Path, wikilink_index: dict[str, Path]
) -> list[Finding]:
    findings: list[Finding] = []
    rel = str(path.relative_to(repo_root))

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return findings  # rule 1 will flag

    try:
        fm, body = parse_frontmatter(text)
    except yaml.YAMLError:
        return findings  # rule 1 will flag

    # Wikilinks in body
    for target in extract_wikilinks(body):
        if target not in wikilink_index:
            findings.append(
                Finding(
                    RULE_ID,
                    SEVERITY,
                    rel,
                    f"wikilink [[{target}]] does not resolve to any kb page",
                )
            )

    # Source-page raw_path
    if fm and fm.get("type") == "source":
        provenance = fm.get("provenance", {})
        if isinstance(provenance, dict):
            raw_path = provenance.get("raw_path")
            if raw_path:
                # raw_path is repo-root-relative
                resolved = repo_root / raw_path
                if not resolved.is_file():
                    findings.append(
                        Finding(
                            RULE_ID,
                            SEVERITY,
                            rel,
                            f"provenance.raw_path does not resolve: {raw_path}",
                            line=1,
                        )
                    )

    return findings


def check(repo_root: Path, config: dict) -> list[Finding]:
    findings: list[Finding] = []
    index = _build_wikilink_index(repo_root)
    for path in iter_kb_pages(repo_root):
        findings.extend(_check_page(path, repo_root, index))
    return findings
