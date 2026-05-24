"""
Shared utilities for lint rules and other framework tools.

Provides:
- Finding dataclass — the unit of lint output
- Frontmatter parsing (YAML between leading and trailing ---)
- File discovery helpers (kb pages, manifests, role files, raw files)
- Repo-root detection
- Constants (valid types, valid statuses per type, etc.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml

# --- Constants describing the framework's data model ---

VALID_TYPES = {"source", "concept", "finding", "decision", "por"}

VALID_STATUSES_BY_TYPE = {
    "source": {"active", "archived", "superseded"},
    "concept": {"seed", "developing", "under_test", "supported", "falsified", "dropped", "superseded"},
    "finding": {"active", "archived", "superseded"},
    "decision": {"active", "superseded"},
    "por": {"active"},
}

REQUIRED_FIELDS_ALL = {"id", "title", "type", "status", "area", "created", "updated", "summary"}

ID_PREFIX_BY_TYPE = {
    "source": "s-",
    "concept": "c-",
    "finding": "f-",
    "decision": "d-",
    "por": None,  # POR files don't have id prefix convention
}


# --- Finding type ---

@dataclass
class Finding:
    """One result from a lint rule."""
    rule_id: str  # e.g., "rule_01"
    severity: str  # "error" or "warning"
    file_path: str  # path relative to repo root
    message: str
    line: int | None = None  # 1-indexed; None if not applicable
    suggestion: str | None = None

    def format(self, *, color: bool = False) -> str:
        """Format as a human-readable line."""
        sev = self.severity.upper()
        if color:
            sev_colored = f"\033[31m{sev}\033[0m" if self.severity == "error" else f"\033[33m{sev}\033[0m"
        else:
            sev_colored = sev

        loc = self.file_path
        if self.line is not None:
            loc = f"{loc}:{self.line}"

        lines = [f"{sev_colored:5}  {self.rule_id}  {loc}", f"       {self.message}"]
        if self.suggestion:
            lines.append(f"       suggestion: {self.suggestion}")
        return "\n".join(lines)


# --- Repo navigation ---

def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from `start` (or cwd) until we find _framework/. Raise if not found."""
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "_framework").is_dir():
            return candidate
    raise RuntimeError(
        f"could not find _framework/ in {here} or any parent — not a project_kb workspace"
    )


def load_config(repo_root: Path) -> dict:
    """Load _framework/config.yml. Returns parsed dict."""
    config_path = repo_root / "_framework" / "config.yml"
    if not config_path.is_file():
        raise RuntimeError(f"missing config: {config_path}")
    with config_path.open() as f:
        return yaml.safe_load(f) or {}


# --- Frontmatter parsing ---

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """
    Extract YAML frontmatter from the start of a markdown document.

    Returns (frontmatter_dict, body). If no frontmatter, returns (None, text).
    If frontmatter is malformed YAML, raises yaml.YAMLError.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    fm_text = m.group(1)
    body = text[m.end():]
    fm = yaml.safe_load(fm_text)
    if not isinstance(fm, dict):
        raise yaml.YAMLError(f"frontmatter must be a mapping, got {type(fm).__name__}")
    return fm, body


def read_page(path: Path) -> tuple[dict | None, str, list[str]]:
    """
    Read a markdown file. Returns (frontmatter, body, lines) where lines is the
    full file split for line-number reporting.

    Raises on file-not-found or YAML errors.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    fm, body = parse_frontmatter(text)
    return fm, body, lines


# --- File discovery ---

def iter_kb_pages(repo_root: Path) -> Iterator[Path]:
    """Yield all .md files under any kb/ directory in commons or areas."""
    for parent in [repo_root / "commons", repo_root / "areas"]:
        if not parent.is_dir():
            continue
        for path in parent.rglob("kb/**/*.md"):
            if path.is_file() and path.name != "index.md":
                yield path


def iter_role_files(repo_root: Path) -> Iterator[Path]:
    """Yield all role.md files under any roles/ directory."""
    for parent in [repo_root / "commons", repo_root / "areas"]:
        if not parent.is_dir():
            continue
        for path in parent.rglob("roles/**/role.md"):
            if path.is_file():
                yield path


def iter_pulse_files(repo_root: Path) -> Iterator[Path]:
    """Yield all pulse.md files (commons and per-area)."""
    for parent in [repo_root / "commons", repo_root / "areas"]:
        if not parent.is_dir():
            continue
        for path in parent.rglob("pulse.md"):
            if path.is_file():
                yield path


def iter_manifest_files(repo_root: Path) -> Iterator[Path]:
    """Yield all data manifest files under data/manifests/."""
    for parent in [repo_root / "commons", repo_root / "areas"]:
        if not parent.is_dir():
            continue
        for path in parent.rglob("data/manifests/*.md"):
            if path.is_file():
                yield path


def iter_raw_files(repo_root: Path) -> Iterator[Path]:
    """Yield all files under any raw/ directory."""
    for parent in [repo_root / "commons", repo_root / "areas"]:
        if not parent.is_dir():
            continue
        for raw_dir in parent.rglob("raw"):
            if not raw_dir.is_dir():
                continue
            for path in raw_dir.rglob("*"):
                if path.is_file() and not path.name.startswith(".git"):
                    yield path


def iter_areas(repo_root: Path) -> Iterator[Path]:
    """Yield each area directory (including sub-areas) under areas/."""
    areas_root = repo_root / "areas"
    if not areas_root.is_dir():
        return
    for path in areas_root.rglob("brief.md"):
        yield path.parent


# --- ID convention check ---

_ID_RE = re.compile(r"^[scfd]-\d{4}-\d{2}(?:-\d{2})?-[a-z0-9-]+$")


def is_valid_id(page_id: str, page_type: str) -> bool:
    """Check that an id matches the convention <prefix>-YYYY-MM[-DD]-<slug>."""
    if page_type == "por":
        return True  # POR doesn't use the id convention
    prefix = ID_PREFIX_BY_TYPE.get(page_type)
    if prefix is None:
        return True
    if not page_id.startswith(prefix):
        return False
    return bool(_ID_RE.match(page_id))


# --- Wikilink extraction ---

# Matches [[target]] or [[target|alias]]. Captures `target`.
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]")


def extract_wikilinks(text: str) -> list[str]:
    """Return all wikilink targets (no alias, no extension) from markdown text."""
    return [m.group(1).strip() for m in _WIKILINK_RE.finditer(text)]
