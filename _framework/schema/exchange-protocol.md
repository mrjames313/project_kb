# Exchange Protocol

How agents in one area get authoritative answers from another area without reading through all of the other area's pages. Available when the `multi_area` capability is enabled.

## Filing an exchange

An agent in area X (the **asker**) invokes `/exchange <other-area> <question>`. The skill:

1. If `exchanges/<a>--<b>/` doesn't exist, creates it with `OWNERS`, `README.md`, and `index.md`.
2. Creates a new question file `q-<date>-<slug>.md`.
3. Appends an entry to `exchanges/<a>--<b>/index.md`.

The question file:

```yaml
---
id: ex-2026-05-08-thermal-sensitivity
status: open                  # open | answered | follow_up | closed
asker_area: engineering
asker_role: hardware-engineer
responder_area: research
created: 2026-05-08
relevant_to:
  - thermal budget
  - detector responsivity
---

# Question

What's the temperature dependence of responsivity for the 1310 nm
photodetector? We're sizing the thermal management envelope.

## Context

[[concepts/c-2026-04-shot-noise]]; spec [[specs/2026-05-detector-thermal/brief]]

# Response

_(filled in by responder)_

# Follow-up

_(optional; asker can drill in)_
```

## Directory naming

Exchange directories are named with the two areas in alphabetical order, joined by `--`:

```
exchanges/engineering--research/        # not "research--engineering"
```

This is enforced so a given pair has exactly one canonical directory regardless of which area asks first.

## Responding

When work in the responder area happens, the responder invokes `/respond-exchange <id>`.

When `task_subagents` is enabled, this spawns a subagent with the responder area's role context, restricted to writing the Response section. The subagent may use `/answer-from-kb` to pull existing kb pages by reference (with summarization, not duplication) — this is where the "expert summarization" payoff happens.

On completion, status flips to `answered`.

## Asker review

The asker reviews the response.

If sufficient: `/close-exchange <id>` flips status to `closed`.

If insufficient: the asker edits the Follow-up section and flips status to `follow_up`. The responder cycle repeats.

## Staleness

The linter (Rule 14, runs only when `multi_area` is enabled) flags exchanges with `status: open` aged past `exchange_stale_active_days` (default 7). Stale exchanges surface to INBOX under "Heads up."

## Persistence

Exchange files are kept indefinitely after closing. They're frequently the best institutional record of "why does X area think Y about Z." Closed exchanges are an audit trail; they don't get deleted or archived automatically.

## OWNERS and README

Each exchange directory has two human-authored support files:

- `OWNERS` — names the two areas as joint owners. Lint refuses to delete an exchange directory whose OWNERS file is intact.
- `README.md` — describes the scope of the exchange (what kinds of questions belong here). Drafted on directory creation; can be updated as the exchange's scope clarifies.

## On disable

When `multi_area` is disabled via `/framework disable multi_area`:

- Existing exchange directories remain on disk.
- The four exchange skills become unavailable.
- CLAUDE.md's "Cross-area reads" section is removed.
- Role files have exchange-related skills removed from their `Allowed skills` lists.
- Lint Rule 14 stops running.

Re-enabling later picks up existing exchanges where they were.

If `multi_area` is disabled while exchange directories contain content, the `framework` skill warns the user in conversation before applying the change.
