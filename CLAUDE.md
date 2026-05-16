# Project operating manual

This is the schema document for agents working in this project. It contains operating principles, not domain knowledge. Read it end-to-end before doing any work; refer back when uncertain.

The file is reshaped by the `/framework` skill when capabilities are enabled or disabled. Do not edit by hand.

## What this project is

See `commons/brief.md` for the project's mission and objectives. The brief is the most-loaded file across every role.

## How knowledge is organized

The project has **two layers**:
- `raw/` — immutable source materials (PDFs, transcripts, web clips). Read but never modified.
- `kb/` — the wiki, agent-maintained. The structured artifact that compounds.

Knowledge pages in `kb/` come in **four types**:
- **source** — summary of a raw material; provenance points back into `raw/`.
- **concept** — hypothesis or claim under investigation; carries a status lifecycle (see below).
- **finding** — established understanding; treat as given background.
- **decision** — recorded choice; alternatives noted; supersession explicit.

**Path-based ownership.** Every file's location says who owns it:
- `commons/` is jointly stewarded; direct writes are forbidden; use `/propose-promotion`.
- `areas/<area>/` is owned by that area's roles.
- `areas/<a>/<sub>/` is owned by the sub-area; sub-areas explicitly inherit parent context via role preload lists (no implicit inheritance).

## How to start a session

1. Read `INBOX.md` and `areas-index.md` (loaded automatically by SessionStart hook).
2. Identify the area and role most relevant to the user's request.
3. Adopt a role by loading its preload list. The role file is the contract for "what context does this kind of work need."
4. Never inherit context from a previous session — always reload from the role.

## Communicating with the human

- **Conversation is the dominant mode of interaction.** Ask questions, surface uncertainties, request approvals, and discuss findings in conversation.
- **INBOX.md is supplementary** — it captures items that arose outside a conversation, items the human will see later, and items needing async attention.
- When the human is in session, default to conversation. Don't file an INBOX item for something you can ask directly.

## When to write where

- Findings, decisions, concepts within your area: write directly to area `kb/`.
- Same content that's project-wide: write to your area's `kb/`, then `/propose-promotion`.
- Never write directly to `commons/` — proposals only.
- Never write to any `raw/` directory — raw materials are immutable.

## How to interpret types

- **source**: external; the page in `kb/sources/` is a structured summary of the raw material in `raw/`. Cite when used; preserve provenance.
- **concept**: hypothesis or claim with a status stage (see below); never propagate as fact until promoted to finding.
- **finding**: established understanding; treat as given; provenance distinguishes external source (with `raw_path`) vs promoted concept.
- **decision**: prescriptive choice; alternatives noted; check supersession.

## How to handle concept stages

A concept's `status` field carries the maturity stage and the handling rule:

- **seed** — initial spark; phrase as "one direction is..."
- **developing** — informal idea; phrase as "the working idea is..."
- **under_test** — formal claim with evidence being gathered; cite evidence list; surface "we're testing whether..." in derived statements.
- **supported** — sufficient evidence; treat as "we have evidence that..." but not yet established; promote to finding via proposal.
- **falsified** — disproven; cite as anti-repetition memory; never propagate the falsified assertion as a working assumption.
- **dropped** — abandoned without resolution; cite only when explaining history.
- **superseded** — replaced; follow the `superseded_by` link.

## Loading context: frontmatter vs full file

- When evaluating relevance, **read frontmatter only** (summary, type, status, `relevant_to`). Frontmatter is the index card; the body is the book.
- Load the full body only when (a) the page is in your role's preload list, (b) the frontmatter indicates material relevance to your current task, or (c) you intend to cite, build on, or supersede the page's content.
- When scanning many pages, never open every body.

## Links and provenance

- Use `[[wikilinks]]` for kb cross-references.
- Forward links are written by agents; the linter maintains backlinks via `.links.json` sidecars.
- Linking to a page with `status: superseded` is an error — follow `superseded_by`.
- After substantively updating a page, check its backlinks. For each backlinker, decide whether your update affects what the backlinker asserts. If yes, update inline or file a note into INBOX under "Heads up."

## Pulse discipline

- Append events to `_journal/pulse.log` during the session.
- Before `/clear` or end of session: invoke `/wrap-up`.
- `pulse.md` is bounded (default 80 lines); the wrap-up skill enforces the line cap by promoting items to kb or dropping them — never silent truncation.

## Spec lifecycle

brief → plan → tasks → execution → outcome.

Each transition is a human gate, decided in conversation. `/replan` can fire from any point; appends to `revisions.md`; updates plan and/or tasks.

## Skills

Skills may be invoked explicitly by slash command (`/ingest`, `/plan`, etc.) or autonomously when the request matches the skill's trigger conditions. Both paths execute the same skill.

The set of available skills depends on which capabilities are enabled. The `/framework` skill manages capability state.

## Escalation triggers (when to stop and ask)

- A change touches `commons/` — invoke proposal, do not write directly.
- Two findings contradict — file a concept with `status: under_test`; do not silently overwrite.
- A spec's outcome diverges materially from the plan — `/replan`, not improvise.
- An area boundary needs to change — ask the human in conversation; do not move files unilaterally.
- A request spans multiple areas with no obvious lead — ask the human in conversation; do not pick an area unilaterally.
