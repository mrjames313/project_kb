"""
Token estimation for role preload lists.

Parses a role file, identifies its full-preload files and frontmatter-preload
patterns, and estimates total token cost.

The estimate is character-count-based (`chars / 4`) for now — consistent across
files, accurate enough for relative comparisons (which is what /budget and
/framework prune need), and dependency-free. We can swap in a proper tokenizer
(Anthropic SDK, tiktoken) in a later commit if we need closer-to-actual numbers.

Public API:
    estimate_role_preload(role_file, repo_root) -> EstimateResult
    parse_role_preload(role_file_text) -> {"full": [...], "frontmatter_patterns": [...]}
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Make `common` importable when running this file directly
sys.path.insert(0, str(Path(__file__).parent))

from common import find_repo_root, parse_frontmatter  # noqa: E402


# A consistent character-to-token ratio. English-ish prose tokenizes at roughly
# 4 chars per token for Claude's tokenizer; structured/code-y content is denser.
# We use 4 as a single conservative ratio; the estimate is for comparison, not
# capacity planning.
CHARS_PER_TOKEN = 4


@dataclass
class FileEstimate:
    """Per-file token estimate."""
    path: str  # relative to repo root
    tokens_est: int


@dataclass
class EstimateResult:
    """Full result of estimating a role's preload."""
    role_file: str
    full_preload_files: list[FileEstimate] = field(default_factory=list)
    frontmatter_preload_files: list[FileEstimate] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)

    @property
    def full_preload_tokens_est(self) -> int:
        return sum(fe.tokens_est for fe in self.full_preload_files)

    @property
    def frontmatter_preload_tokens_est(self) -> int:
        return sum(fe.tokens_est for fe in self.frontmatter_preload_files)

    @property
    def total_preload_tokens_est(self) -> int:
        return self.full_preload_tokens_est + self.frontmatter_preload_tokens_est

    def to_dict(self) -> dict:
        """Serializable form for telemetry."""
        return {
            "role_file": self.role_file,
            "full_preload_files": len(self.full_preload_files),
            "full_preload_tokens_est": self.full_preload_tokens_est,
            "frontmatter_preload_files": len(self.frontmatter_preload_files),
            "frontmatter_preload_tokens_est": self.frontmatter_preload_tokens_est,
            "total_preload_tokens_est": self.total_preload_tokens_est,
            "file_breakdown_full": [
                {"path": fe.path, "tokens_est": fe.tokens_est}
                for fe in self.full_preload_files
            ],
            "missing_files": self.missing_files,
        }


def estimate_text_tokens(text: str) -> int:
    """Estimate the token count of a text string. Returns at least 1 for any non-empty input."""
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


# --- Role file parsing ---

# Match a numbered or bulleted list item. Captures the content after the marker.
_LIST_ITEM_RE = re.compile(r"^\s*(?:\d+\.|-)\s+(.+?)\s*$")


def parse_role_preload(role_text: str) -> dict[str, list[str]]:
    """
    Parse a role file's markdown, extracting:
      - "full": list of repo-relative paths from the "Preload context (full)" section
      - "frontmatter_patterns": list of patterns from "Preload context (frontmatter only)"

    Paths in the role file have a leading slash (repo-root-relative); we strip it.
    Trailing comments (e.g. `# only if capability: por`) are stripped.
    Capability marker lines (e.g. `# capability: por`) are skipped.
    """
    full: list[str] = []
    frontmatter_patterns: list[str] = []
    current_section: str | None = None

    for raw_line in role_text.splitlines():
        line = raw_line.rstrip()

        # Section headers — `## ...`
        if line.startswith("##"):
            heading = line.lstrip("#").strip().lower()
            if heading.startswith("preload context (full)"):
                current_section = "full"
            elif heading.startswith("preload context (frontmatter"):
                current_section = "frontmatter"
            else:
                current_section = None
            continue

        if current_section is None:
            continue

        # Skip capability marker lines
        stripped = line.strip()
        if stripped.startswith("# capability:") or stripped.startswith("# end capability:"):
            continue

        match = _LIST_ITEM_RE.match(line)
        if not match:
            continue

        content = match.group(1)

        # Strip trailing inline comment
        content = re.sub(r"\s+#.*$", "", content)
        content = content.strip()

        # Strip backticks
        content = content.strip("`")

        # Must look like a repo-rooted path
        if not content.startswith("/"):
            continue

        path = content.lstrip("/")

        if current_section == "full":
            full.append(path)
        else:
            frontmatter_patterns.append(path)

    return {"full": full, "frontmatter_patterns": frontmatter_patterns}


# --- Estimation ---

def _estimate_full_file(repo_root: Path, rel_path: str) -> FileEstimate | None:
    """Read a file and estimate its token cost. None if file is missing."""
    full_path = repo_root / rel_path
    if not full_path.is_file():
        return None
    try:
        text = full_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return FileEstimate(path=rel_path, tokens_est=estimate_text_tokens(text))


def _estimate_frontmatter_pattern(
    repo_root: Path, pattern: str
) -> list[FileEstimate]:
    """
    Resolve a pattern (a directory path) to all .md files under it, and
    estimate the tokens of just the frontmatter blocks.
    """
    dir_path = repo_root / pattern
    if not dir_path.is_dir():
        return []

    estimates: list[FileEstimate] = []
    for md_path in sorted(dir_path.rglob("*.md")):
        if md_path.name == "index.md":
            continue
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Extract the frontmatter block (between leading and trailing ---)
        try:
            fm, _body = parse_frontmatter(text)
        except Exception:  # noqa: BLE001
            continue
        if fm is None:
            continue
        # Re-serialize just the frontmatter region (with delimiters) to estimate
        # what the agent actually loads. We approximate by counting the raw
        # frontmatter region from the source text.
        fm_text = _extract_frontmatter_region(text)
        rel = str(md_path.relative_to(repo_root))
        estimates.append(FileEstimate(path=rel, tokens_est=estimate_text_tokens(fm_text)))
    return estimates


_FRONTMATTER_REGION_RE = re.compile(r"^---\s*\n.*?\n---\s*\n?", re.DOTALL)


def _extract_frontmatter_region(text: str) -> str:
    """Return the raw frontmatter block from a markdown file, including delimiters."""
    m = _FRONTMATTER_REGION_RE.match(text)
    return m.group(0) if m else ""


def estimate_role_preload(role_file: Path, repo_root: Path) -> EstimateResult:
    """
    Estimate the total preload token cost for a role.

    Reads the role file, parses its preload sections, and computes per-file
    estimates. Missing files (referenced but not on disk) are recorded but
    don't fail the estimate.
    """
    role_file = role_file.resolve()
    repo_root = repo_root.resolve()

    try:
        role_text = role_file.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"could not read role file {role_file}: {e}") from e

    sections = parse_role_preload(role_text)
    try:
        rel_role = str(role_file.relative_to(repo_root))
    except ValueError:
        rel_role = str(role_file)  # role file is outside repo; fall back to absolute
    result = EstimateResult(role_file=rel_role)

    for rel_path in sections["full"]:
        fe = _estimate_full_file(repo_root, rel_path)
        if fe is None:
            result.missing_files.append(rel_path)
        else:
            result.full_preload_files.append(fe)

    for pattern in sections["frontmatter_patterns"]:
        # Whether or not the pattern resolves, no "missing" gets recorded —
        # patterns are directories, and missing directories yield empty results.
        result.frontmatter_preload_files.extend(
            _estimate_frontmatter_pattern(repo_root, pattern)
        )

    return result


# --- Reporting ---

def format_estimate(result: EstimateResult, *, top_n: int = 5) -> str:
    """Format an estimate as a human-readable report."""
    lines = [f"Role: {result.role_file}", ""]

    lines.append(
        f"Full preload:        {len(result.full_preload_files):3d} files, "
        f"~{result.full_preload_tokens_est:>6d} tokens"
    )
    lines.append(
        f"Frontmatter preload: {len(result.frontmatter_preload_files):3d} files, "
        f"~{result.frontmatter_preload_tokens_est:>6d} tokens"
    )
    lines.append(f"{'TOTAL':<21}{' ' * 13}~{result.total_preload_tokens_est:>6d} tokens")
    lines.append("")

    if result.full_preload_files:
        heaviest = sorted(result.full_preload_files, key=lambda fe: -fe.tokens_est)[:top_n]
        lines.append(f"Heaviest full-preload files (top {len(heaviest)}):")
        for fe in heaviest:
            lines.append(f"  ~{fe.tokens_est:>6d}  {fe.path}")
        lines.append("")

    if result.missing_files:
        lines.append("Missing files (referenced in role file but not on disk):")
        for m in result.missing_files:
            lines.append(f"  - {m}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate the token cost of a role's preload list."
    )
    parser.add_argument("role_file", type=Path, help="path to the role file (role.md)")
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="path to repo root (default: auto-detect from role file)",
    )
    parser.add_argument("--json", action="store_true", help="output JSON instead of text")
    args = parser.parse_args()

    try:
        if args.repo:
            repo_root = args.repo.resolve()
        else:
            repo_root = find_repo_root(args.role_file.parent)
    except RuntimeError as e:
        print(f"token_estimate: {e}", file=sys.stderr)
        return 2

    try:
        result = estimate_role_preload(args.role_file, repo_root)
    except RuntimeError as e:
        print(f"token_estimate: {e}", file=sys.stderr)
        return 2

    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_estimate(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
