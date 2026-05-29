---
name: ask
description: Answer a question using the project's knowledge base. Searches kb pages, cites with wikilinks, and modifies no files. Use when the user wants information, not action.
---

# /ask

Answers a question from the kb without changing any state. The output is prose with citations.

## When to use

- User asks "what do we know about X?", "have we decided Y?", "is there a finding about Z?"
- User wants to orient before deciding what work to do next.
- The question is informational, not a task.

If the user wants to act on what they learn (e.g. write something, run an experiment), they should follow up with `/plan` or `/implement`.

## Steps

1. **Identify the relevant areas.** Look at the question's keywords. If the role's area covers it, search there first. If the question is project-wide, also search `commons/kb/`. Don't search every area for every question; use the role's area + commons unless the user names another area.

2. **Search the kb.** For each candidate area:
   - Scan `kb/index.md` for an overview (the lint regenerates this).
   - Read frontmatter blocks of pages whose `relevant_to` tags match the question's keywords.
   - For promising hits, check `when_to_load` (if present) before loading the body. The field tells you whether the body is worth the token cost for *this* task — it commonly names a cheaper alternative ("the underlying findings cover the regulatory mechanics; this page is the playbook spine") or scopes what the page does and doesn't contain. If `when_to_load` suggests skipping for this task's shape, follow that and look at the named alternative instead.
   - Then read the full body for the pages that survive the filter.

3. **Synthesize an answer.** Combine what you found. Be explicit about:
   - What is established (findings with status `active`).
   - What is contested or under test (concepts with status `under_test`, decisions with `superseded`).
   - What's missing (no relevant pages found in this area).

4. **Cite.** Every claim that comes from the kb gets a `[[wikilink]]` to the page it came from. Don't paraphrase without attribution.

5. **Note gaps.** If the question can't be answered from current kb, say so. Suggest one of:
   - `/ingest` if the user has source material that would answer it.
   - `/plan` if the answer requires new work.
   - `/exchange` (if `multi_area` is enabled) if another area might have the answer.

## Notes

- `/ask` never writes to any file — not even pulse.log. It's a pure read operation.
- Don't load full bodies for pages whose frontmatter clearly doesn't match. Read frontmatter first, then body only if relevant.
- If the kb contradicts itself (two findings pointing different directions), flag that explicitly. Don't pick one and hide the other.
- For questions that span multiple areas and `multi_area` is disabled: answer from your area's kb + commons only. Don't read deeply into other areas' kb bodies (lint rule 16 surfaces this if you do it a lot).
- When citing decisions, prefer the most recent non-superseded one. If a decision has been superseded, link to the replacement (its `superseded_by` field).
