# Framework Tools

Deterministic Python helpers used by the framework. Run from the repo root.

## Setup

```bash
pip install -r _framework/tools/requirements.txt
```

Requires Python 3.10+.

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

Tests cover each rule module's pass case and per-violation cases, plus `activity_days` edge cases (empty repo, cold-project resumption, same-day deduplication).

## Architecture

Each lint rule lives in `lint_rules/rule_NN_<name>.py` and exposes a single function:

```python
def check(repo_root: Path, config: dict) -> list[Finding]:
    """Run this rule. Return list of findings."""
```

`lint.py` runs fixup rules first (rules 3 and 15, which write files), then inspection rules. Shared utilities are in `common.py`. Tests share fixtures from `tests/conftest.py` and `tests/lint_helpers.py`.

The lint tools have no dependencies on Claude or any LLM — they're pure Python with PyYAML and stdlib only.
