# Framework Tools

Deterministic Python helpers used by the framework. Run from the repo root.

## Setup

Requires Python 3.10+.

The recommended approach is a venv at the repo root so dependencies stay local to the project:

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r _framework/tools/requirements.txt
```

For running the test suite, also install pytest:

```bash
pip install pytest
```

If you'd rather not use a venv, install globally with `--break-system-packages` (on systems that require it):

```bash
pip install -r _framework/tools/requirements.txt
pip install pytest    # only if running tests
```

In either case, activate the venv before invoking the tools, or run them via `./.venv/bin/python _framework/tools/lint.py`.

## Tools

### `lint.py` — knowledge-base linter

Runs all enabled lint rules and reports findings. See `_framework/schema/lint-rules.md` for the rule catalogue.

```bash
python _framework/tools/lint.py            # run all rules
python _framework/tools/lint.py --rule 01  # run only rule 01
python _framework/tools/lint.py --json     # machine-readable output
```

Exit codes: `0` no findings, `1` errors, `2` warnings only (when warning rules land), `3` lint runner setup error.

Implemented in commit 2a (errors only):
- Rule 1 — Frontmatter validity
- Rule 2 — Forward-link integrity
- Rule 3 — Backlink synchronization (fixup; writes `.links.json` sidecars)
- Rule 5 — Supersession integrity
- Rule 6 — Type-specific completeness
- Rule 7 — Pulse size
- Rule 12 — Data manifest integrity
- Rule 15 — Index maintenance (fixup; regenerates `areas-index.md` and `kb/index.md`)
- Rule 17 — Raw immutability

Deferred for later commits: configurable warnings (Rule 4, 8, 9, 10, 11, 13, 14, 16) and Rule 18 (maintenance-category violations).

### `pulse_compact.py` — wrap-up compaction

Materializes pulse.log events into pulse.md and truncates the log. Regenerates the auto-derived sections (recent decisions, active concepts, recent findings) from current kb state; preserves human-edited sections (current focus, open questions) and updates them from log entries.

```bash
python _framework/tools/pulse_compact.py                  # compact all (commons + every area)
python _framework/tools/pulse_compact.py areas/research   # compact one area
```

Idempotent: running with an empty log is a no-op. Exits non-zero if any pulse.md exceeds the line cap after compaction.

### `promote.py` — proposal → commons

Moves a page from `commons/_proposed/<slug>/page.md` to `commons/kb/<type>/<id>.md`, updating frontmatter (`area: commons`, `human_reviewed: false`, `promoted_from`, `promoted_on`) and writing a CHANGELOG entry. The proposal directory remains as audit trail (only `page.md` is moved).

```bash
python _framework/tools/promote.py 2026-05-shot-noise
```

Errors cleanly when the target already exists, the proposal is missing, or the frontmatter is invalid.

### `manifest_validate.py` — single-manifest validator

Focused inspector for a single data manifest. Same checks as lint Rule 12 (provenance, storage_uri, context_pages) but scoped to one file with prose output.

```bash
python _framework/tools/manifest_validate.py areas/research/data/manifests/m-2026-05-test.md
python _framework/tools/manifest_validate.py areas/research/data/manifests/m-2026-05-test.md --json
```

### `token_estimate.py` — preload token-cost estimator

Estimates the token cost of loading a role's preload list (both full and frontmatter tiers). Used by `/budget` to identify heavy roles and by the telemetry layer to record per-session preload cost.

```bash
python _framework/tools/token_estimate.py areas/research/roles/researcher/role.md
python _framework/tools/token_estimate.py areas/research/roles/researcher/role.md --json
```

The estimate is character-count-based (chars / 4). Accurate enough for relative comparisons (which is what `/budget` and `/framework prune` actually need); not a substitute for Claude Code's `/context` for exact runtime numbers.

### `telemetry.py` — per-session event log

Writes session events to `_framework/telemetry/sessions.jsonl` (git-ignored). Each session generates two events: a `session_start` with the preload estimate and a `session_end` with citation/load data.

```bash
# Recorded by the start skill when it adopts a role
python _framework/tools/telemetry.py session-start --role areas/research/roles/researcher/role.md

# Recorded by /wrap-up or the session-end hook
python _framework/tools/telemetry.py session-end \
    --cited "areas/research/kb/findings/f-1.md,areas/research/kb/concepts/c-3.md" \
    --loaded "areas/research/kb/concepts/c-4.md"

# Inspect recent sessions
python _framework/tools/telemetry.py recent --n 10
python _framework/tools/telemetry.py recent --n 10 --json
```

The telemetry log feeds `/budget` (per-role trends, heavy paths) and `/framework prune` (stale-preload detection based on citation history). Both consumers will land in later commits.

### `activity_days.py` — git-log-derived active days

Helper used by lint and other tools for activity-based thresholds.

```bash
python _framework/tools/activity_days.py --since 2026-01-01
python _framework/tools/activity_days.py --back 30    # calendar date 30 active days ago
```

## Tests

```bash
cd _framework/tools
python -m pytest tests/ -q
```

Tests cover each rule module's pass case and per-violation cases, plus `activity_days`, `token_estimate`, and `telemetry` edge cases (empty repo, cold-project resumption, role file outside repo root, unpaired session_end, etc.).

## Architecture

Each lint rule lives in `lint_rules/rule_NN_<name>.py` and exposes a single function:

```python
def check(repo_root: Path, config: dict) -> list[Finding]:
    """Run this rule. Return list of findings."""
```

`lint.py` runs fixup rules first (rules 3 and 15, which write files), then inspection rules. Shared utilities are in `common.py`. Tests share fixtures from `tests/conftest.py` and `tests/lint_helpers.py`.

`token_estimate.py` and `telemetry.py` are standalone but interoperate: telemetry calls `estimate_role_preload` when recording a session start.

The lint tools have no dependencies on Claude or any LLM — they're pure Python with PyYAML and stdlib only.
