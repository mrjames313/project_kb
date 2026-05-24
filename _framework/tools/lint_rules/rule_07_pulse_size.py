"""
Rule 7 — Pulse size.

Each pulse.md must have at most `pulse_line_cap` lines (default 80).
The /wrap-up skill is responsible for compacting; silent truncation is forbidden.
"""

from __future__ import annotations

from pathlib import Path

from common import Finding, iter_pulse_files

RULE_ID = "rule_07"
SEVERITY = "error"


def check(repo_root: Path, config: dict) -> list[Finding]:
    cap = config.get("lint", {}).get("pulse_line_cap", 80)
    findings: list[Finding] = []
    for path in iter_pulse_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        n_lines = len(text.splitlines())
        if n_lines > cap:
            findings.append(
                Finding(
                    RULE_ID,
                    SEVERITY,
                    str(path.relative_to(repo_root)),
                    f"pulse.md exceeds line cap: {n_lines} > {cap}",
                    suggestion="run /wrap-up to compact; or promote stale items to kb",
                )
            )
    return findings
