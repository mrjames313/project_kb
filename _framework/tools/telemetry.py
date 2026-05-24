"""
Per-session telemetry for the framework.

Writes JSONL events to `_framework/telemetry/sessions.jsonl`. Each line is one
event. Two event types:

- session_start: role adopted, preload estimate.
- session_end: pages cited, bodies loaded beyond preload.

A pointer file `_framework/telemetry/.current-session` records the currently
active session_id so session_end knows which start to pair with.

Aggregation (e.g., per-role averages, prune candidates) is left to consumers
(`/budget`, `/framework prune`). This module just records and queries raw events.

Public API:
    session_start(role_file, repo_root) -> dict (the entry written)
    session_end(repo_root, *, pages_cited=[], bodies_loaded=[]) -> dict
    iter_events(repo_root) -> Iterator[dict]
    recent_sessions(repo_root, n) -> list[dict]   # paired start+end records
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# Make `common` importable when running directly
sys.path.insert(0, str(Path(__file__).parent))

from common import find_repo_root, parse_frontmatter  # noqa: E402
from token_estimate import estimate_role_preload  # noqa: E402


# --- Paths ---

def _telemetry_dir(repo_root: Path) -> Path:
    return repo_root / "_framework" / "telemetry"


def _sessions_log(repo_root: Path) -> Path:
    return _telemetry_dir(repo_root) / "sessions.jsonl"


def _current_session_pointer(repo_root: Path) -> Path:
    return _telemetry_dir(repo_root) / ".current-session"


# --- Time helpers ---

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_session_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# --- Reading the role file's frontmatter (for area) ---

def _read_role_metadata(role_file: Path) -> dict:
    try:
        text = role_file.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
    except Exception:  # noqa: BLE001
        return {}
    return fm or {}


# --- Event writing ---

def _append_event(repo_root: Path, event: dict) -> None:
    """Append one JSON event as a line to sessions.jsonl. Creates dir if needed."""
    log_path = _sessions_log(repo_root)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def session_start(role_file: Path, repo_root: Path) -> dict:
    """
    Record a session_start event. Estimates the role's preload and writes
    an entry with the preload metrics. Saves the session_id to a pointer
    file so session_end can find it.

    Returns the entry that was written.
    """
    role_file = role_file.resolve()
    repo_root = repo_root.resolve()

    estimate = estimate_role_preload(role_file, repo_root)
    metadata = _read_role_metadata(role_file)
    session_id = _generate_session_id()

    try:
        role_file_rel = str(role_file.relative_to(repo_root))
    except ValueError:
        role_file_rel = str(role_file)

    entry = {
        "event": "session_start",
        "timestamp": _utc_now_iso(),
        "session_id": session_id,
        "role": metadata.get("role", "unknown"),
        "area": metadata.get("area", "unknown"),
        "role_file": role_file_rel,
        "full_preload_files": len(estimate.full_preload_files),
        "full_preload_tokens_est": estimate.full_preload_tokens_est,
        "frontmatter_preload_files": len(estimate.frontmatter_preload_files),
        "frontmatter_preload_tokens_est": estimate.frontmatter_preload_tokens_est,
        "total_preload_tokens_est": estimate.total_preload_tokens_est,
    }
    if estimate.missing_files:
        entry["missing_preload_files"] = estimate.missing_files

    _append_event(repo_root, entry)

    pointer = _current_session_pointer(repo_root)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(session_id, encoding="utf-8")

    return entry


def session_end(
    repo_root: Path,
    *,
    pages_cited: list[str] | None = None,
    bodies_loaded: list[str] | None = None,
) -> dict:
    """
    Record a session_end event. Reads the current session_id from the pointer
    file (if present), writes an entry with citation/load data, and clears
    the pointer.
    """
    repo_root = repo_root.resolve()
    pointer = _current_session_pointer(repo_root)
    if pointer.is_file():
        session_id = pointer.read_text(encoding="utf-8").strip()
        try:
            pointer.unlink()
        except OSError:
            pass
    else:
        session_id = "unknown"

    entry = {
        "event": "session_end",
        "timestamp": _utc_now_iso(),
        "session_id": session_id,
        "pages_cited": pages_cited or [],
        "bodies_loaded_beyond_preload": bodies_loaded or [],
    }
    _append_event(repo_root, entry)
    return entry


# --- Reading ---

def iter_events(repo_root: Path) -> Iterator[dict]:
    """Yield each event from sessions.jsonl in order."""
    log_path = _sessions_log(repo_root)
    if not log_path.is_file():
        return
    with log_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def recent_sessions(repo_root: Path, n: int = 10) -> list[dict]:
    """
    Return the N most recent paired session records (start + end joined by session_id).
    An unpaired session_start (no matching session_end) is included with end=None.

    Sessions are ordered most-recent first.
    """
    by_id: dict[str, dict] = {}
    order: list[str] = []

    for event in iter_events(repo_root):
        sid = event.get("session_id")
        if not sid:
            continue
        if event.get("event") == "session_start":
            if sid not in by_id:
                order.append(sid)
                by_id[sid] = {"session_id": sid, "start": event, "end": None}
            else:
                by_id[sid]["start"] = event
        elif event.get("event") == "session_end":
            if sid in by_id:
                by_id[sid]["end"] = event
            else:
                # session_end without a matching start; include it anyway
                order.append(sid)
                by_id[sid] = {"session_id": sid, "start": None, "end": event}

    # Most recent first
    return [by_id[sid] for sid in reversed(order)][:n]


# --- CLI ---

def main() -> int:
    parser = argparse.ArgumentParser(description="Per-session telemetry recorder.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    start = sub.add_parser("session-start", help="record a session start with preload estimate")
    start.add_argument("--role", type=Path, required=True, help="path to the role file being adopted")
    start.add_argument("--repo", type=Path, default=None)

    end = sub.add_parser("session-end", help="record a session end with citation/load data")
    end.add_argument("--cited", default="", help="comma-separated list of pages cited")
    end.add_argument("--loaded", default="", help="comma-separated list of bodies loaded beyond preload")
    end.add_argument("--repo", type=Path, default=None)

    recent = sub.add_parser("recent", help="show recent sessions")
    recent.add_argument("--n", type=int, default=10)
    recent.add_argument("--repo", type=Path, default=None)
    recent.add_argument("--json", action="store_true", default=False, dest="as_json")

    args = parser.parse_args()

    try:
        if args.repo:
            repo_root = args.repo.resolve()
        else:
            start_dir = args.role.parent if args.cmd == "session-start" else Path.cwd()
            repo_root = find_repo_root(start_dir)
    except RuntimeError as e:
        print(f"telemetry: {e}", file=sys.stderr)
        return 2

    if args.cmd == "session-start":
        entry = session_start(args.role, repo_root)
        print(json.dumps(entry, indent=2))
        return 0

    if args.cmd == "session-end":
        cited = [s.strip() for s in args.cited.split(",") if s.strip()]
        loaded = [s.strip() for s in args.loaded.split(",") if s.strip()]
        entry = session_end(repo_root, pages_cited=cited, bodies_loaded=loaded)
        print(json.dumps(entry, indent=2))
        return 0

    if args.cmd == "recent":
        sessions = recent_sessions(repo_root, n=args.n)
        if args.as_json:
            print(json.dumps(sessions, indent=2))
        else:
            if not sessions:
                print("No sessions recorded yet.")
                return 0
            for s in sessions:
                print(_format_session_pair(s))
        return 0

    return 1


def _format_session_pair(pair: dict) -> str:
    start = pair.get("start") or {}
    end = pair.get("end") or {}
    sid = pair.get("session_id", "?")
    role = start.get("role", "?")
    area = start.get("area", "?")
    tokens = start.get("total_preload_tokens_est", "?")
    ts = start.get("timestamp") or end.get("timestamp", "?")
    closed = "closed" if end else "open"
    return f"  {sid}  {ts}  {role}@{area}  ~{tokens}t  [{closed}]"


if __name__ == "__main__":
    raise SystemExit(main())
