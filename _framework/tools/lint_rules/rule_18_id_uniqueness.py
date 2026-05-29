"""
Rule 18 — Page ID uniqueness across the project.

Every kb page (across `commons/kb/` and `areas/<area>/kb/`) must have an `id`
that is unique within the project. Duplicates produce wikilink ambiguity
(`[[some-id]]` could resolve to two different files) and silently break
backlink/forward-link integrity.

This rule was added after a bug where `/promote` retained the source area
page's id on the new commons page, producing collisions when the source area
page was still in place (the protocol leaves it). The fix is the
`<prefix>-commons-<slug>` id convention; this rule catches the recurrence.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from common import (
    Finding,
    iter_kb_pages,
    parse_frontmatter,
)

RULE_ID = "rule_18"
SEVERITY = "error"


def check(repo_root: Path, config: dict) -> list[Finding]:
    """Scan every kb page; flag any id used by more than one file."""
    by_id: dict[str, list[Path]] = defaultdict(list)

    for path in iter_kb_pages(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(text)
        except (OSError, yaml.YAMLError):
            continue
        if not fm:
            continue
        page_id = fm.get("id")
        if not page_id:
            continue
        by_id[page_id].append(path)

    findings: list[Finding] = []
    for page_id, paths in by_id.items():
        if len(paths) <= 1:
            continue
        # Sort for deterministic test output
        rels = sorted(str(p.relative_to(repo_root)) for p in paths)
        # Report under each file involved so the user sees the issue
        # from whichever file they happen to be looking at
        peers_summary = ", ".join(rels)
        for rel in rels:
            findings.append(
                Finding(
                    rule_id=RULE_ID,
                    severity=SEVERITY,
                    file_path=rel,
                    message=(
                        f"id {page_id!r} is used by {len(paths)} pages: {peers_summary}. "
                        "Each kb page must have a project-unique id."
                    ),
                    line=1,
                    suggestion=(
                        "If this is a promoted page, rename the commons copy using "
                        "the `<prefix>-commons-<slug>` convention. Otherwise, change "
                        "one page's id to a distinct value."
                    ),
                )
            )
    return findings
