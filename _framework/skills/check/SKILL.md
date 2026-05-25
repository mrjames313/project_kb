---
name: check
description: Run lint over the repo and surface any findings. Use to verify the project is healthy before committing or when something feels off.
---

# /check

Runs the linter and reports errors and warnings to the user. Optionally helps fix them.

## When to use

- Before committing.
- When a previous `/implement` or `/wrap-up` reported issues you didn't immediately resolve.
- Periodically as a health check.
- When something feels off (e.g., a wikilink isn't resolving in your search, or a page disappeared).

## Steps

1. **Run lint.**
   ```
   python _framework/tools/lint.py
   ```

   The runner does two phases:
   - **Fixup phase** — regenerates `.links.json` backlink sidecars (rule 3) and `areas-index.md` + per-`kb/` `index.md` files (rule 15). These quietly update; they don't report findings unless they fail to write.
   - **Inspection phase** — checks frontmatter validity (1), forward-link integrity (2), supersession integrity (5), type-specific completeness (6), pulse size (7), data manifest integrity (12), and raw immutability (17). These produce findings.

2. **Read the output.** Each finding has:
   - **rule_id** — which rule fired (e.g., `rule_01`).
   - **severity** — `error` or `warning`. For now, only errors fire; warnings will arrive in a later commit alongside the shadow-trigger mechanism.
   - **file_path:line** — where the issue is.
   - **message** — what's wrong.
   - **suggestion** (sometimes) — how to fix.

3. **Triage with the user.** Group findings by file. For each:
   - If the fix is obvious (e.g., add a missing frontmatter field, fix a typo'd wikilink), propose it. Apply only with user confirmation unless the user has indicated "just fix lint errors."
   - If the fix requires a judgment call (e.g., which page should supersede which, or which concept's evidence is missing), ask the user.
   - If the finding is a "raw immutability" violation (rule 17), do not silently fix it. Raw materials are immutable; the only correct response is to revert the modification (or, if intentional, archive the original raw file and add a new one). Ask the user how to proceed.

4. **Re-run lint after fixes.** Confirm clean.

5. **Brief the user.** Summarize what was found and what was fixed. If anything was deferred, say so.

## Notes

- `/check` is read-mostly. The only file edits it performs are explicit fixes the user asked for. The fixup phase (sidecars, indices) does write files but those are auto-regenerated artifacts, not user content.
- If lint surfaces many findings, don't try to fix them all in one `/check` invocation. Group them, propose a triage order, and tackle the most important first.
- For the specific `--rule N` flag, see `_framework/tools/README.md`. Running one rule at a time is useful for iterating on a fix.
- `/check` does not run telemetry. It's a tool call, not a session-bound action.
- A clean `lint: clean.` is the goal before any commit. CI integration (if added later) would run the same `lint.py` invocation.
