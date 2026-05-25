---
name: budget
description: Show how the project is spending its context budget. Reports per-role preload costs, recent session totals, missing-file warnings, and prune candidates. Read-only; no file changes.
---

# /budget

Surfaces where context budget is going across roles and sessions. Combines per-role token estimates with telemetry history so the user can decide what to trim.

## When to use

- The user feels the project is "heavy" (long preload, slow start, hitting context limits).
- After adding several new pages or enabling a capability, to check the cost.
- Periodically as a health check.
- Before deciding whether to `/framework prune` a role or `/framework disable` a capability.

## Steps

1. **Per-role token estimates.** For every role file under `commons/roles/` and `areas/*/roles/`, run:
   ```
   python _framework/tools/token_estimate.py <path-to-role.md>
   ```
   Collect the totals. Build a table:

   ```
   Role                     Full preload    Frontmatter preload    Total
   --------------------------------------------------------------------------
   researcher               4 files / ~3.2K   180 files / ~12.4K   ~15.6K
   engineer                 4 files / ~2.8K   45 files / ~3.0K     ~5.8K
   ...
   ```

   Highlight any role where the total exceeds a threshold the user cares about (rule of thumb: above 15K tokens of preload is heavy; above 30K is a cause for action).

2. **Heaviest individual files per role.** For roles flagged as heavy, surface the top 3–5 heaviest files in their full preload (token_estimate output includes a `Heaviest full-preload files` section). This usually points at the actual culprit — often `_framework/spec.md` if it shouldn't be there, or a large brief that could be trimmed.

3. **Missing files.** For each role, report any `missing_preload_files` from the token_estimate output. Missing files are usually stale role files referencing pages that were deleted or renamed — recommend `/framework prune`.

4. **Recent session activity.** Run:
   ```
   python _framework/tools/telemetry.py recent --n 10
   ```
   Show the user the last 10 sessions: role, area, preload size, whether they completed (closed) or were left open. If the same role is being adopted frequently and consistently exceeds expected token cost, that's a signal.

5. **Prune candidates.** Run:
   ```
   python _framework/tools/framework.py prune
   ```
   List any candidates. Lifecycle-flagged ones (dead pages still in preload) are safe to remove via `/framework prune --apply`. Activity-flagged ones (not cited in N sessions) are heuristics — surface them but defer to user judgment.

6. **Summarize.** A few lines:
   - Which roles are heaviest and why.
   - Any missing files (and which `/framework prune` would clean them up).
   - Concrete suggestions (e.g., "the researcher role's frontmatter tier is heavy because `/areas/research/kb/` has grown to 180 files. Consider narrowing to specific subdirectories, or `/framework prune` to flag stale ones.")

## Notes

- `/budget` is **read-only.** It doesn't modify any files, doesn't toggle anything, doesn't apply prune. It's a reporting tool. Acting on its output is the user's call, via `/framework prune` or `/framework disable` or manual role-file edits.
- The token estimate is character-based (chars / 4). Accurate enough for relative comparisons across roles; not exact. For real token counts at runtime, see Claude Code's `/context` command.
- If telemetry data is sparse (few sessions recorded), activity-based signals will be weak. That's fine — lifecycle-based prune candidates and per-role heaviness analysis still work without telemetry.
- "Heavy" is relative to the budget the user has. A 15K-token preload that gets reused across many sessions is reasonable; a 15K-token preload that loads once and is mostly unused is waste.
- Roles inherit "always-on" preload entries (CLAUDE.md, schema docs). Those costs are unavoidable; focus the report on what's *specific* to each role.
