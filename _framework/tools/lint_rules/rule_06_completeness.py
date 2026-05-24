"""
Rule 6 — Type-specific completeness.

- concept with status in {under_test, supported, falsified} must have
  a non-empty `evidence` list.
- finding must have `provenance` populated.
- decision must have `alternatives_considered` populated (may be empty list).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from common import Finding, iter_kb_pages, parse_frontmatter

RULE_ID = "rule_06"
SEVERITY = "error"

CONCEPT_STATUSES_REQUIRING_EVIDENCE = {"under_test", "supported", "falsified"}


def _check_page(path: Path, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = str(path.relative_to(repo_root))

    try:
        text = path.read_text(encoding="utf-8")
        fm, _body = parse_frontmatter(text)
    except (OSError, yaml.YAMLError):
        return findings

    if not fm:
        return findings

    page_type = fm.get("type")

    if page_type == "concept":
        if fm.get("status") in CONCEPT_STATUSES_REQUIRING_EVIDENCE:
            evidence = fm.get("evidence")
            if not evidence or not isinstance(evidence, list) or len(evidence) == 0:
                findings.append(
                    Finding(
                        RULE_ID,
                        SEVERITY,
                        rel,
                        f"concept at status {fm.get('status')!r} needs non-empty `evidence` list",
                        line=1,
                    )
                )

    elif page_type == "finding":
        provenance = fm.get("provenance")
        if not provenance or not isinstance(provenance, dict):
            findings.append(
                Finding(
                    RULE_ID,
                    SEVERITY,
                    rel,
                    "finding must have `provenance` populated",
                    line=1,
                    suggestion="set provenance with kind (concept|external|experiment) and ref or raw_path",
                )
            )

    elif page_type == "decision":
        if "alternatives_considered" not in fm:
            findings.append(
                Finding(
                    RULE_ID,
                    SEVERITY,
                    rel,
                    "decision must have `alternatives_considered` field (may be empty list)",
                    line=1,
                )
            )

    return findings


def check(repo_root: Path, config: dict) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_kb_pages(repo_root):
        findings.extend(_check_page(path, repo_root))
    return findings
