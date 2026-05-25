---
name: close-exchange
description: Close an answered exchange. The asker reviews the response, decides what becomes part of their area's kb, and marks the exchange closed. Requires the multi_area capability.
---

# /close-exchange

Finalizes an exchange that the responder has answered. The asker decides what (if anything) from the answer becomes part of their kb and marks the exchange `closed`.

## When to use

- An exchange filed by `/exchange` from your area now has `status: answered` (the responder filled in the Response section).
- The user explicitly invokes `/close-exchange <id>`.
- A `/start` surfaced an `answered` exchange from your area's asks.

## Steps

1. **Find the exchange.** User-named, or scan `exchanges/*/` for files with `status: answered` and `asker_area:` matching the role's area.

2. **Read the full thread.** Question + Context + Response. Understand what was asked and what the responder said.

3. **Decide on follow-up.** Three options:
   - **Satisfied** — the response answers the question. Proceed to step 4.
   - **Follow-up needed** — the response is partial or surfaced new questions. Fill in the `# Follow-up` section of the exchange file, change status back to `open`, update the index entry. The responder picks it up again. (Stop here; the exchange is not yet closed.)
   - **Insufficient and abandoned** — the response can't move the asker's work forward and you've decided to take a different direction. Close without incorporating. Note this in the closure record.

4. **Decide what becomes part of your kb.** The exchange is *not* part of your kb — it's a transcript. If the response established something durable, file it in your kb:
   - **A new finding** — write it under `areas/<area>/kb/findings/`. Cite the exchange as provenance:
     ```yaml
     provenance:
       kind: external
       retrieved: 2026-05-15
       raw_path: exchanges/<a>--<b>/<exchange-id>.md
     ```
     (Even though the exchange is a markdown file inside the repo, treating it as "external" for provenance purposes — it came from another area's role.)
   - **A new concept** — if the response surfaced a hypothesis to test. Start at status `developing`.
   - **A new decision** — if you're committing to a course of action based on the response.
   - **Nothing kb-worthy** — sometimes the response is just operational ("yes, that's correct") and doesn't need to be filed. Skip this step.

5. **Close the exchange.** Update the question file's frontmatter:
   - `status: closed`
   - Add `closed_on: YYYY-MM-DD` and `closed_by: <role>`.

   Append a brief closure note at the end of the file:
   ```markdown
   # Closure

   _Closed by <role>@<area> on YYYY-MM-DD._

   <Brief note: what (if anything) became part of <area>'s kb, citing the new pages.
   Or, if no kb additions, what direction the asker took based on the response.>
   ```

6. **Update the exchange index.** In `exchanges/<a>--<b>/index.md`, change the entry's status from `answered` to `closed`.

7. **Record in pulse.log.** In your area's `_journal/pulse.log`:
   ```
   ## [YYYY-MM-DD HH:MM] decision <role>
   Closed exchange <id>: <one-line summary of what came of it>.
   ```
   If new kb pages were created, also add the appropriate `finding`/`concept`/`decision` entries.

8. **Verify.** Run `python _framework/tools/lint.py`. New kb pages must have complete frontmatter; the exchange file remains lint-relevant for forward-link integrity.

9. **Brief the user.** Summarize what the exchange concluded and what (if anything) was added to the kb.

## Notes

- Closure is the asker's call. The responder doesn't close; they only respond.
- You can close without filing anything new in the kb. Not every exchange produces durable knowledge — sometimes it just unblocks a decision.
- An exchange that's been `answered` for a long time without being closed is a candidate for review. Lint rule 14 (configurable warning, off by default) can surface these.
- If the same question comes up repeatedly across different specs or follow-ups, that's a signal the answer should be **promoted to commons** via `/propose-promotion`. Especially if the responder's kb already has a finding that covers it.
- Don't reopen a closed exchange. If new questions arise, file a fresh `/exchange` referencing the closed one in the Context section.
