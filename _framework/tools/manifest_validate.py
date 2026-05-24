"""
Validate a single data manifest.

A focused inspector for individual manifest files. Same checks as lint Rule 12
(provenance, storage_uri, context_pages) but scoped to one file, with a more
verbose human-readable report.

Public API:
    validate_manifest(manifest_path, repo_root) -> list[Finding]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from common import Finding, find_repo_root, parse_frontmatter  # noqa: E402


def validate_manifest(manifest_path: Path, repo_root: Path) -> list[Finding]:
    """Run manifest checks against a single file. Returns findings."""
    manifest_path = manifest_path.resolve()
    repo_root = repo_root.resolve()

    try:
        rel = str(manifest_path.relative_to(repo_root))
    except ValueError:
        rel = str(manifest_path)

    findings: list[Finding] = []

    if not manifest_path.is_file():
        findings.append(
            Finding(
                rule_id="manifest",
                severity="error",
                file_path=rel,
                message=f"manifest file not found: {manifest_path}",
            )
        )
        return findings

    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as e:
        findings.append(
            Finding(
                rule_id="manifest",
                severity="error",
                file_path=rel,
                message=f"could not read: {e}",
            )
        )
        return findings

    try:
        fm, _body = parse_frontmatter(text)
    except yaml.YAMLError as e:
        findings.append(
            Finding(
                rule_id="manifest",
                severity="error",
                file_path=rel,
                message=f"malformed frontmatter: {e}",
                line=1,
            )
        )
        return findings

    if not fm:
        findings.append(
            Finding(
                rule_id="manifest",
                severity="error",
                file_path=rel,
                message="missing frontmatter block",
                line=1,
            )
        )
        return findings

    # provenance
    provenance = fm.get("provenance")
    if not provenance or not isinstance(provenance, dict):
        findings.append(
            Finding(
                rule_id="manifest",
                severity="error",
                file_path=rel,
                message="missing or empty `provenance` dict",
                line=1,
                suggestion="set provenance with kind (external | internal-experiment | internal-notes) "
                           "and acquired_on (or retrieved)",
            )
        )

    # storage_uri
    storage_uri = fm.get("storage_uri")
    if not storage_uri or not isinstance(storage_uri, str):
        findings.append(
            Finding(
                rule_id="manifest",
                severity="error",
                file_path=rel,
                message="missing or empty `storage_uri`",
                line=1,
                suggestion="point at the storage location: s3://..., file://..., or relative repo path",
            )
        )

    # context_pages
    context_pages = fm.get("context_pages")
    if not context_pages or not isinstance(context_pages, list) or len(context_pages) == 0:
        findings.append(
            Finding(
                rule_id="manifest",
                severity="error",
                file_path=rel,
                message="missing or empty `context_pages` list",
                line=1,
                suggestion="link to at least one kb page describing what this data is for",
            )
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a single data manifest."
    )
    parser.add_argument("manifest", type=Path, help="path to the manifest .md file")
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        repo_root = args.repo.resolve() if args.repo else find_repo_root(args.manifest.parent)
    except RuntimeError as e:
        print(f"manifest_validate: {e}", file=sys.stderr)
        return 2

    findings = validate_manifest(args.manifest, repo_root)

    if args.json:
        import json
        payload = [
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "file_path": f.file_path,
                "line": f.line,
                "message": f.message,
                "suggestion": f.suggestion,
            }
            for f in findings
        ]
        print(json.dumps(payload, indent=2))
    else:
        if not findings:
            print(f"manifest_validate: {args.manifest} — OK.")
        else:
            for f in findings:
                print(f.format())
                print()
            print(f"manifest_validate: {len(findings)} issue(s).")

    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
