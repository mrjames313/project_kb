"""
Rule 12 — Data manifest integrity.

Each manifest in data/manifests/ must carry:
- `provenance` (populated dict)
- `storage_uri` (non-empty string)
- `context_pages` (non-empty list of wikilinks into kb/)
"""

from __future__ import annotations

from pathlib import Path

import yaml

from common import Finding, iter_manifest_files, parse_frontmatter

RULE_ID = "rule_12"
SEVERITY = "error"


def _check_manifest(path: Path, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = str(path.relative_to(repo_root))

    try:
        text = path.read_text(encoding="utf-8")
        fm, _body = parse_frontmatter(text)
    except (OSError, yaml.YAMLError):
        return findings

    if not fm:
        return findings

    if not fm.get("provenance") or not isinstance(fm.get("provenance"), dict):
        findings.append(
            Finding(RULE_ID, SEVERITY, rel, "manifest missing `provenance` dict", line=1)
        )

    storage_uri = fm.get("storage_uri")
    if not storage_uri or not isinstance(storage_uri, str):
        findings.append(
            Finding(RULE_ID, SEVERITY, rel, "manifest missing or empty `storage_uri`", line=1)
        )

    context_pages = fm.get("context_pages")
    if not context_pages or not isinstance(context_pages, list) or len(context_pages) == 0:
        findings.append(
            Finding(
                RULE_ID,
                SEVERITY,
                rel,
                "manifest needs non-empty `context_pages` linking to kb/",
                line=1,
            )
        )

    return findings


def check(repo_root: Path, config: dict) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_manifest_files(repo_root):
        findings.extend(_check_manifest(path, repo_root))
    return findings
