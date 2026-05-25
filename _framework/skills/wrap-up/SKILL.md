---
name: wrap-up
description: Close out a working session. Compacts pulse.log into pulse.md, writes outcome.md for any completed specs, runs lint, and records a session_end telemetry event with citation/load metadata.
---

# /wrap-up

Closes a working session cleanly: compacts the journal into pulse.md, finalizes any completed specs, verifies lint, and records the session_end event.

## When to use

- End of a working session (always).
- Before switching roles (`/start <other-role>` after `/wrap-up`).
- Before committing work to git.
- If the user is stopping for the day and won't return for a while.

If a session ends without `/wrap-up`, pulse.log will be non-empty when the next session starts. The next `/start` will notice and offer to wrap up first.

## Steps

1. **Check spec completion.** For each spec under `areas/<area>/specs/` with work done in this session:
   - If all tasks in `tasks.md` are complete (`- [x]`) and the work resolved the brief, write `outcome.md`. Use the template at `_framework/schema/spec-template/outcome.md`.
   - If some tasks are still open, leave the spec in place; the next session can continue.

2. **Compact pulse.** Run:
   ```
   python _framework/tools/pulse_compact.py areas/<area>
   ```
   (Or with no argument to compact every area and commons.) This:
   - Verifies that filed kb pages from the log exist (warns if not).
   - Regenerates pulse.md's "Recent decisions", "Active concepts under test", and "Recent findings" sections from current kb state.
   - Preserves "Current focus" and "Open questions", updating them from any `focus-shift` and `question` log entries this session.
   - Truncates `_journal/pulse.log`.

   If pulse_compact reports any missing-filed-path warnings, that means a journal entry referenced a kb page that doesn't exist. Create the missing page (it was probably forgotten during `/implement`) or fix the journal entry, then re-run.

3. **Verify lint.** Run:
   ```
   python _framework/tools/lint.py
   ```
   Fix any errors. The session is not wrapped up if lint is dirty — leave the journal in place and ask the user how to address the issues.

4. **Record session_end telemetry.** Gather:
   - **pages_cited** — every `[[wikilink]]` you referenced in your own outputs this session. Include their paths.
   - **bodies_loaded** — any pages whose body you read beyond the preload tier (i.e., pages from `## Preload context (frontmatter only)` patterns whose body you ended up loading, plus any pages outside preload entirely).

   Run:
   ```
   python _framework/tools/telemetry.py session-end \
       --cited "<comma-separated paths>" \
       --loaded "<comma-separated paths>"
   ```

5. **Summarize.** Tell the user, in 3–5 lines:
   - What was accomplished (which tasks/specs).
   - What's still open.
   - Any open questions surfaced during the session.

## Notes

- `pulse_compact.py` is idempotent. If you run it twice, the second run is a no-op (empty log, no new state).
- The line cap on pulse.md is enforced by lint rule 7 (default 80 lines). If `pulse_compact.py` exits with code 1, the pulse went over cap — review what was added and decide what to promote out (some decisions or findings may be ripe to leave the "recent" section and live only in their kb pages).
- **What counts as "cited" for telemetry?** A page is cited if you referred to it in output the user saw — either you used a `[[wikilink]]` to it, or you summarized its content in your response. A page that was preloaded but never referenced is not cited.
- **What counts as "loaded beyond preload"?** Anything where you read the full body and it wasn't in `## Preload context (full)`. Frontmatter-tier pages whose bodies you read count.
- Don't agonize over getting telemetry exactly right. Best-effort is fine; the data is for trend analysis (which preloads aren't being used) not precise accounting.
- If `por` is enabled, also update `POR.md` for the area if anything material shifted: phase change, completed workstream, new dependency.
- After `/wrap-up` is the natural place to `git commit`. The skill itself doesn't commit, but the project is in a clean, journaled state ready for one.
