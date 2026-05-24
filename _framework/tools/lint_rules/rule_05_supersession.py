"""
Rule 5 — Supersession integrity.

- Pages with `status: superseded` must have `superseded_by` populated.
- Forward wikilinks to pages with `status: superseded` are errors;
  suggest the replacement via the target's `superseded_by`.
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

RULE_ID = "rule_05"
SEVERITY = "error"


def _build_status_index(repo_root: Path) -> dict[str, tuple[Path, dict]]:
    """
    Build {wikilink_target: (path, frontmatter)} for every kb page.
    Used to look up a target's status and superseded_by.
    """
    index: dict[str, tuple[Path, dict]] = {}
    for page in iter_kb_pages(repo_root):
        try:
            text = page.read_text(encoding="utf-8")
            fm, _body = parse_frontmatter(text)
        except (OSError, yaml.YAMLError):
            continue
        if fm is None:
            continue
        rel = page.relative_to(repo_root)
        parts = rel.parts
        if "kb" in parts:
            kb_idx = parts.index("kb")
            within_kb = "/".join(parts[kb_idx + 1:])
            target = within_kb[:-3] if within_kb.endswith(".md") else within_kb
            index[target] = (page, fm)
            index.setdefault(page.stem, (page, fm))
    return index


def check(repo_root: Path, config: dict) -> list[Finding]:
    findings: list[Finding] = []
    status_index = _build_status_index(repo_root)

    # Pass 1: superseded pages must have superseded_by
    for page in iter_kb_pages(repo_root):
        try:
            text = page.read_text(encoding="utf-8")
            fm, _body = parse_frontmatter(text)
        except (OSError, yaml.YAMLError):
            continue
        if fm is None:
            continue

        rel = str(page.relative_to(repo_root))
        if fm.get("status") == "superseded":
            superseded_by = fm.get("superseded_by")
            # YAML can parse ~ as None; treat missing or None as unpopulated
            if not superseded_by or superseded_by == "~":
                findings.append(
                    Finding(
                        RULE_ID,
                        SEVERITY,
                        rel,
                        "status is 'superseded' but superseded_by is not populated",
                        line=1,
                        suggestion="set superseded_by to the wikilink target of the replacement page",
                    )
                )

    # Pass 2: forward links to superseded pages are errors
    for page in iter_kb_pages(repo_root):
        try:
            text = page.read_text(encoding="utf-8")
            _fm, body = parse_frontmatter(text)
        except (OSError, yaml.YAMLError):
            continue

        rel = str(page.relative_to(repo_root))
        for target in extract_wikilinks(body):
            if target in status_index:
                _target_path, target_fm = status_index[target]
                if target_fm.get("status") == "superseded":
                    replacement = target_fm.get("superseded_by")
                    suggestion = None
                    if replacement and replacement != "~":
                        suggestion = f"follow superseded_by → [[{replacement}]]"
                    findings.append(
                        Finding(
                            RULE_ID,
                            SEVERITY,
                            rel,
                            f"link to [[{target}]] which is superseded",
                            suggestion=suggestion,
                        )
                    )

    return findings
