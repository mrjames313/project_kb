# Framework Specification

This is the maximal specification for the Project Orchestration Framework — every directory, every file type, every capability, every rule. Bootstrap a new project via [SETUP.md](../SETUP.md); learn what's needed when from the [adoption guide](adoption-guide.md); reach for this document when you want the full reference.

A lightweight framework for orchestrating multi-area project development with Claude Code agents. Knowledge, code, and data are organized around shared project structures and area-specific structures, with disciplined paths for information to flow between them.

The framework is built around a small always-on foundation plus four togglable capabilities that can be enabled when their cost is justified by the project's signals.

---

## 1. Principles

The framework is built around five ideas, in priority order:

**Specialized areas build toward a shared goal.** A project's work splits across distinct knowledge domains — research, engineering, business model, product. Each area defines its own roles, operates with autonomy within its scope, and contributes back to the commons — the shared ground that holds the project's direction and distilled findings — through a defined promotion protocol. Path-based ownership is the mechanism: every file's location says who owns it.

**Specs precede work; replanning is normal.** Every substantive task — research, code, business model, customer study — starts with a brief and a plan. Phase gates exist so a human can correct course before effort is sunk. When reality diverges from the plan, agents replan via a documented step rather than silently drifting.

**Knowledge compounds; the wiki is the artifact.** The wiki is a persistent compounding artifact, not a transcript of chats. Findings, concepts, and decisions are filed as pages with lifecycle and provenance. The wiki layer (`kb/`) is distinct from the raw layer (`raw/`) — raw materials are immutable; the wiki is what compounds.

**Context loading is intentional.** What an agent loads is decided deliberately, not implicitly. Commons supplies the general background every role needs; frontmatter on each kb page declares relevance hints that guide what else to add. Agents read frontmatter first; full bodies load only when material to the task.

**Discipline scales with need.** A small always-on foundation handles the typical case; togglable capabilities add machinery (POR, subagents, formal review) when projects grow into needing them.

---

## 2. Directory layout

```
project-root/
├── README.md
├── CLAUDE.md                          # schema document — the operating manual
├── INBOX.md                           # human-attention items (async)
├── areas-index.md                     # lint-generated map of areas + roles
│
├── _framework/                        # all framework infrastructure
│   ├── spec.md                        # maximal specification (this document)
│   ├── config.yml                     # current configuration
│   ├── schema/
│   │   ├── frontmatter.md
│   │   ├── link-conventions.md
│   │   ├── lint-rules.md
│   │   ├── exchange-protocol.md
│   │   ├── promotion-protocol.md
│   │   ├── role-template.md
│   │   ├── capabilities.md            # describes each togglable capability
│   │   └── spec-template/
│   │       ├── brief.md.tmpl
│   │       ├── plan.md.tmpl
│   │       ├── tasks.md.tmpl
│   │       ├── revisions.md.tmpl
│   │       └── outcome.md.tmpl
│   ├── tools/                         # deterministic helpers (python)
│   │   ├── lint.py
│   │   ├── pulse_compact.py
│   │   ├── promote.py
│   │   ├── manifest_validate.py
│   │   ├── activity_days.py
│   │   └── framework.py
│   ├── skills/                        # claude code agent skills
│   │   ├── framework/SKILL.md
│   │   ├── start/SKILL.md
│   │   ├── ingest/SKILL.md
│   │   ├── ask/SKILL.md
│   │   ├── plan/SKILL.md
│   │   ├── implement/SKILL.md
│   │   ├── replan/SKILL.md
│   │   ├── wrap-up/SKILL.md
│   │   ├── check/SKILL.md
│   │   ├── propose-promotion/SKILL.md
│   │   ├── promote/SKILL.md
│   │   └── (capability-gated skills, see section 15)
│   └── hooks/
│       ├── session-start.sh
│       ├── pre-compact.sh
│       └── session-end.sh
│
├── commons/                           # shared ground for all areas
│   ├── brief.md
│   ├── POR.md                         # only when capability: por is enabled
│   ├── pulse.md                       # current state, bounded
│   ├── _journal/
│   │   └── pulse.log                  # append-only events
│   ├── CHANGELOG.md
│   ├── _proposed/
│   ├── roles/
│   │   ├── coordinator/role.md        # only when capability: por is enabled
│   │   └── (other project-wide roles)
│   ├── kb/                            # essential, distilled findings
│   │   ├── index.md                   # lint-generated
│   │   ├── findings/
│   │   ├── decisions/
│   │   ├── concepts/
│   │   └── sources/
│   ├── raw/
│   ├── code/
│   └── data/
│       └── manifests/
│
├── areas/
│   └── <area>/
│       ├── brief.md
│       ├── POR.md                     # only when capability: por is enabled
│       ├── pulse.md
│       ├── _journal/
│       │   └── pulse.log
│       ├── roles/
│       ├── kb/
│       ├── raw/
│       ├── code/
│       ├── data/
│       └── specs/
│
├── exchanges/                         # exists when capability: multi_area is on
│   └── <a>--<b>/
│       ├── OWNERS
│       ├── README.md
│       ├── index.md
│       └── q-*.md
│
└── .claude/
    └── settings.json                  # hooks wired here
```

**Underscore convention.** A single `_framework/` directory holds all infrastructure. Project content has no underscore prefix (`commons`, `areas`, `roles`, `specs`, `kb`, `raw`, `code`, `data`, `exchanges`). Two exceptions: `_proposed/` inside `commons/` (workflow artifact; "do not write directly") and `_journal/` per area (transient working records; written through skills, not by hand).

**Areas nest.** Sub-specialties (e.g., `areas/research/optics/`) have the same internal shape as parents. Explicit inheritance — role files in the child explicitly reference parent paths in preload lists.

**Raw vs wiki.** Raw materials in `raw/` are immutable; agents read but never modify. The `source` page in `kb/sources/` is the structured summary, with frontmatter `provenance.raw_path` pointing back into `raw/`.

**Raw vs data.** Raw is documents and unstructured material (papers, transcripts, web clips); data is structured datasets with manifests in `data/manifests/`.

**Why `commons`.** The name captures jointly-stewarded shared ground — explicitly the resource the areas pool into and draw from. Direction flows down from commons to areas (brief, POR, mission); distilled findings flow up from areas to commons via the promotion protocol. The plural carries the bidirectional stewardship that a singular "common" couldn't.

### File maintenance categories

- **Human-authored (H)** — hand-edited; agents read but don't write.
- **Agent-maintained (A)** — agents read and write per protocol.
- **Lint-generated (L)** — auto-regenerated from other files; do not hand-edit.

Mapping:

| Path | Category |
|---|---|
| `README.md`, `CLAUDE.md` | H |
| `_framework/**` (schema, tools, skills, hooks, spec.md) | H |
| `_framework/config.yml` | A (managed by `/framework` skill) |
| `commons/brief.md`, `areas/**/brief.md` | H |
| `commons/roles/**/role.md`, `areas/**/roles/**/role.md` | H |
| `exchanges/**/OWNERS`, `exchanges/**/README.md` | H |
| `INBOX.md` | A (agents append; human clears) |
| `commons/POR.md`, `areas/**/POR.md` | A |
| `**/pulse.md` | A |
| `**/_journal/pulse.log` | A |
| `commons/CHANGELOG.md` | A |
| `commons/_proposed/**` | A |
| `commons/kb/**/*.md` (post-promotion) | A |
| `areas/**/kb/**/*.md` | A |
| `areas/**/data/manifests/**` | A |
| `areas/**/specs/**` | A |
| `exchanges/**/q-*.md` | A |
| `**/raw/**` | H (immutable; treated as if human-authored) |
| `areas-index.md` | L |
| `**/kb/index.md` | L |
| `exchanges/**/index.md` | L |
| `**/*.links.json` (backlink sidecars) | L |

Lint enforces category boundaries.

---

## 3. Capabilities and the `/framework` command

The framework defines a small always-on foundation plus four togglable capabilities. Each capability can be independently enabled or disabled. State lives in `_framework/config.yml`. Changes happen via the `/framework` skill — never by hand-editing config.

### The four capabilities

| Capability | What it adds | Default |
|---|---|---|
| `multi_area` | Pairwise Q&A protocol between areas (the "exchanges" protocol), plus `exchange`, `respond-exchange`, `close-exchange`, `answer-from-kb` skills. | off |
| `por` | Plan of Record files per area and in commons, plus the coordinator role for cross-area planning. POR is loaded into every role's preload list. | off |
| `task_subagents` | Tasks within specs are executed by fresh subagents (clean context, role-loaded). Parent agent plans and orchestrates; subagents implement. | off |
| `formal_review` | Adds rigor on top of subagent execution: independent reviewer subagent after each task, auto-debug subagent on second rejection, and per-area verdict subagents for commons promotions. **Requires `task_subagents`.** | off |

### What's always on (the foundation)

These are not capabilities; they define what the framework is:

- Path-based ownership and the directory layout.
- Frontmatter discipline (the four types: source, concept, finding, decision; their lifecycles).
- CLAUDE.md as the schema document.
- Pulse discipline (per-area `pulse.md` + `_journal/pulse.log`; `wrap-up` compaction).
- Wiki/raw two-layer split.
- Lint correctness rules (always-on errors, see section 14).
- Single-human-gate promotion to commons (the *protection* is always on; `formal_review` adds per-area verdicts on top).
- Specs with phase gates and replanning.
- INBOX for asynchronous human attention; conversation as dominant interaction.

### The `/framework` command

A single skill provides all capability and lint-visibility management.

```
/framework                          show current state of all capabilities
                                    and lint visibility

/framework enable <capability>      enable a capability; prompts for approval,
                                    lists file changes, applies atomically

/framework disable <capability>     disable a capability; warns about content
                                    that becomes inert; applies atomically

/framework enable-lint <rule>       make a disabled lint warning visible

/framework disable-lint <rule>      stop displaying a lint warning
                                    (the rule still runs in shadow mode)

/framework lint-status              show which lint rules are visible vs shadow,
                                    plus recent shadow trigger counts
```

The skill's behavior on `enable`:

1. Reads `config.yml`. If already enabled, no-op.
2. Checks dependencies. If `formal_review` requested without `task_subagents`, offers to enable both.
3. Lists proposed file changes in conversation:
   - Files created (e.g., `POR.md` per area when enabling `por`).
   - Files edited (which sections of CLAUDE.md are added, which role files get updated, which skills come online).
4. After user approval (in conversation), applies all changes atomically.
5. Updates `config.yml`.
6. Runs `/check` to confirm clean lint state.

The skill's behavior on `disable`:

1. Identifies content that will become inert (e.g., POR.md files when disabling `por`, exchange files when disabling `multi_area`). Files are **not deleted** — they remain on disk but stop being referenced by role preload lists, schema document sections, and skill behaviors.
2. Warns the user in conversation if substantial content exists.
3. After approval, removes the relevant CLAUDE.md sections, role file entries, and skill conditionals.
4. Updates `config.yml`.
5. Re-enabling later picks up the existing files where they were.

Capability-specific change lists are described declaratively in `_framework/schema/capabilities.md`. The `framework` skill reads this file and applies the described edits. Adding a new capability later means a new section in `capabilities.md` plus a handler in `framework.py`.

### `config.yml` shape

```yaml
# _framework/config.yml

capabilities:
  multi_area: false
  por: false
  task_subagents: false
  formal_review: false

lint:
  # thresholds (apply regardless of warning visibility)
  pulse_line_cap: 80
  stale_concept_threshold_active_days: 30
  promotion_freshness_active_days: 14
  spec_abandonment_active_days: 60
  exchange_stale_active_days: 7
  cross_area_link_threshold: 3
  recent_decisions_window_active_days: 7

  # threshold for suggesting that a shadow rule be enabled
  shadow_suggest_threshold: 5

  # which warning rules are visible
  # disabled = run in shadow; trigger counts surface as suggestions
  warnings_visible:
    rule_4_orphans: false
    rule_8_stale_concept: false
    rule_9_cross_area_links: false
    rule_10_promotion_freshness: false
    rule_11_spec_abandonment: false
    rule_13_backlinker_freshness: false
    rule_14_exchange_staleness: false
    rule_16_cross_area_reads: false
```

Lint, hooks, and skills read from `config.yml` at runtime. Conditional behavior (e.g., does `/implement` spawn a subagent?) checks the relevant capability flag.

---

## 4. The schema document (CLAUDE.md)

CLAUDE.md contains operating principles. It's reshaped by `/framework enable` and `/framework disable` to reflect only currently-enabled capabilities. The current capability set is always visible in `_framework/config.yml`; CLAUDE.md reflects state, not options.

Always-present sections:

```
# Project operating manual

## What this project is
## How knowledge is organized
## How to start a session
## Communicating with the human
## When to write where
## How to interpret types
## How to handle concept stages
## Loading context: frontmatter vs full file
## Links and provenance
## Pulse discipline
## Spec lifecycle
## Skills
## Escalation triggers
```

Capability-gated sections:

```
## Cross-area reads                    (capability: multi_area)
## POR discipline                      (capability: por)
## Subagent pattern                    (capability: task_subagents)
## Formal review                       (capability: formal_review)
```

When a capability is enabled, the `/framework` skill inserts the appropriate section into CLAUDE.md. When disabled, the section is removed.

The "Communicating with the human" section is always present and reads:

```
- Conversation is the dominant mode of interaction. Ask questions, surface
  uncertainties, request approvals, and discuss findings in conversation.
- INBOX.md is supplementary: it captures items that arose outside a
  conversation, items the human will see later, and items needing async
  attention.
- When the human is in session, default to conversation. Don't file an INBOX
  item for something you can ask directly.
```

---

## 5. Frontmatter spec

Four types (`source`, `concept`, `finding`, `decision`); status lifecycles per type; type-specific fields; commons-promoted items carry `human_reviewed`, `promoted_from`, `promoted_on`. Source provenance carries `raw_path` pointing into `raw/`. Lint sidecars for backlinks.

See `_framework/schema/frontmatter.md` for the full specification.

---

## 6. Role files

Role files are reshaped by `/framework enable` and `/framework disable` to reflect enabled capabilities. The general shape:

```markdown
---
role: optics-researcher
area: research/optics
summary: Investigates optical-domain questions; designs and runs experiments;
         maintains the optics kb.
---

# Optics Researcher

## Preload context (explicit; do not infer additional)

Schema and conventions:
1. /CLAUDE.md
2. /_framework/schema/frontmatter.md
3. /_framework/schema/link-conventions.md

Project and parent area:
4. /commons/brief.md
5. /commons/POR.md                              # only if capability: por
6. /commons/pulse.md
7. /areas/research/brief.md
8. /areas/research/POR.md                       # only if capability: por
9. /areas/research/pulse.md

Own area:
10. /areas/research/optics/brief.md
11. /areas/research/optics/POR.md               # only if capability: por
12. /areas/research/optics/pulse.md
13. /areas/research/optics/kb/index.md

## Operating boundaries

- Writes allowed: /areas/research/optics/** EXCEPT /areas/research/optics/raw/**.
- Raw materials anywhere are read-only; treat as immutable.
- Reads allowed: full repo, but prefer /exchange (when available) over deep
  reads into other areas' kb bodies.
- Writes to /commons/: forbidden; use /propose-promotion.
- Writes to other areas: forbidden; use /exchange (when available).

## Allowed skills

(set varies by enabled capabilities — see section 15)

## Default behaviors

- Cite using [[wikilinks]].
- When citing a concept, surface its status.
- When ending a session, run /wrap-up before clearing.
- When a task's plan looks wrong, invoke /replan; do not improvise.
- Ask the human in conversation when uncertain. INBOX is for items the
  human will see later, not a substitute for asking now.
```

A **reviewer role** is a stripped-down variant of the implementer role. Reviewer roles only exist when `formal_review` is enabled.

The **coordinator role** at `commons/roles/coordinator/role.md` exists only when `por` is enabled. It's read-broad, write-narrow: loads `commons/brief.md`, `commons/POR.md`, `areas-index.md`, all area `POR.md` files, `INBOX.md`, and active spec briefs. Writes only to `INBOX.md`, `commons/POR.md`, and specs across areas.

---

## 7. Session start and role routing

SessionStart hook loads `CLAUDE.md`, `areas-index.md`, `INBOX.md`. The `start` skill handles routing — identifies area and role, loads preload list, or asks for clarification.

When `coordinator` role is unavailable (i.e., `por` is off), cross-area requests prompt the human in conversation to pick an area rather than auto-adopting a coordinator role.

Explicit invocation: `/start <role> <request>` skips the routing and adopts the named role directly.

The `start` skill recognizes three patterns for in-request routing beyond the default content-based inference: (1) **inline area or role mentions** ("…in engineering", "as a researcher…") parsed and used directly without further prompting; (2) **mid-session switch language** ("switch to engineering", "now work as product-manager") that reloads the named role's preload list; and (3) **read-only cross-area queries** ("what's in engineering's pulse?") that keep the current role active and read the requested content without switching. Role switches happen only when the work would require writes outside the current role's boundaries.

**areas-index.md** is auto-maintained by lint. Format:

```markdown
# Areas Index
_Auto-maintained by lint; do not edit by hand._
_Last updated: 2026-05-08_

## commons/
Project-wide knowledge, code, and data. Use exchanges or area work,
not direct commons writes.

Roles:
- coordinator — cross-area planning, INBOX management, POR updates
  (only present when capability: por is enabled)

## areas/research/
[summary from areas/research/brief.md]

Roles:
- researcher — broad research questions

### areas/research/optics/
[summary from areas/research/optics/brief.md]

Roles:
- optics-researcher — optical-domain investigations
```

---

## 8. POR (Plan of Record) — capability: `por`

When `por` is enabled, every area (and commons) has a `POR.md` file alongside `brief.md`. The three files complement each other:

- **brief.md** — why this exists. Changes rarely. Always present.
- **POR.md** — current plan and execution state. Updated when phases shift, workstreams change, or replans happen. Present only when `por` is enabled.
- **pulse.md** — what's current. Changes constantly. Always present.

POR content includes current phase, active workstreams, upcoming, dependencies, and status/risks.

The `wrap-up` skill prompts the user in conversation to confirm POR updates when relevant events occurred during the session.

The `coordinator` role exists when `por` is enabled and updates `commons/POR.md`. Area roles update their own area's POR.

**On disable.** Existing POR files remain on disk. Role preload lists are updated to remove POR references; CLAUDE.md's POR section is removed; the coordinator role file is removed from `commons/roles/`. Re-enabling later picks up the existing files where they were.

---

## 9. INBOX

`INBOX.md` at the project root collects items that need the human's attention asynchronously. Three sections (Needs decision, Awaiting your ack, Heads up). Agents append; human clears. Conversation remains the dominant interaction mode; INBOX is supplementary.

```markdown
# Inbox
_Last touched by agents: 2026-05-08 14:22_

## Needs decision
(blocked on you; agents cannot proceed)

- [2026-05-07] Objection on proposed promotion
  `commons/_proposed/2026-05-07-noise-finding/`. Engineering objects to scope;
  research approves. Verdict files in proposal dir.

- [2026-05-06] Spec `specs/2026-05-1f-noise` brief drafted in
  areas/research/optics/; awaiting your approval before plan phase.

## Awaiting your ack
(done, just needs your eyes)

- [2026-05-08] Promoted to commons: [[findings/f-2026-05-shot-noise]]
  (human_reviewed: false).

## Heads up
(FYI; you don't need to act, but you should know)

- [2026-05-08] 5 customer interview transcripts in `areas/product/raw/interviews/`
  not yet ingested.
- [2026-05-08] Exchange `engineering--research/q-2026-05-04-thermal` open
  for 4 active days without response.
```

---

## 10. Spec template

Every substantive task lives in a spec directory under `<area>/specs/<date>-<slug>/`:

```
specs/2026-05-photodetector-noise/
├── brief.md         # what we're doing and why; one screen
├── plan.md          # method, architecture, or approach
├── tasks.md         # discrete steps with _Boundary:_ and _Depends:_
├── revisions.md     # append-only log of replans
└── outcome.md       # what happened; produced pages; superseded plans
```

Per-task annotations:

```markdown
### T1: Set up the noise-floor measurement rig
_Boundary:_ /areas/research/optics/code/measurement-rig/
_Depends:_ —
_Status:_ planned
_Owner role:_ optics-researcher

[task description]

#### Implementation Notes
(Appended by subagents as they work; persists across sessions.)
```

Phase gates: brief → [human approves in conversation] → plan → [human approves] → tasks → execution → outcome → [human approves close]. `/replan` can fire from any point; appends to `revisions.md`; updates plan and/or tasks.

When `task_subagents` is off, `/implement` runs the work in the current agent. When on, each task spawns a fresh subagent.

---

## 11. Pulse mechanics

Each area, sub-area, and commons maintains a pair of files:

**pulse.md** — canonical current state, bounded. Maximum size enforced by lint (default 80 lines). Sections:

```markdown
# Research/Optics — pulse
_Last compaction: 2026-05-08 14:30_

## Current focus
(2–4 lines, rewritten not appended)

## Recent decisions (last 7 active days)
- [[decisions/d-2026-05-04-bias-current]] — bias at 1 mA, not 5 mA
- ...

## Active concepts under test
- [[concepts/c-2026-04-shot-noise]] — status: under_test
- ...

## Open questions
- Does 1/f noise floor depend on bias direction?
- ...

## Recent findings (last 5)
- [[findings/f-2026-05-shot-noise]]
- ...
```

**_journal/pulse.log** — append-only event log. Entries during the session:

```markdown
## [2026-05-08 09:14] decision optics-researcher
Adopted bias current of 1 mA per measurement constraints.
→ to be filed: decisions/d-2026-05-04-bias-current

## [2026-05-08 11:22] finding optics-researcher
Shot noise floor measured at 1310nm; matches theory within 8%.
→ to be filed: findings/f-2026-05-shot-noise

## [2026-05-08 13:45] focus-shift optics-researcher
Switching from noise-floor characterization to 1/f investigation per replan
in spec ...
```

The `_journal/` subdirectory holds transient working records — currently just `pulse.log`, but a natural home for any future append-only artifacts (debug traces, session histories) that agents produce during work and that get compacted or truncated later.

**Compaction (the `wrap-up` skill)**:

1. Read `_journal/pulse.log` and `pulse.md`.
2. For each log entry, decide:
   - **decision**: ensure a `decisions/` page exists; reference in "Recent decisions"; drop entries past activity-day threshold.
   - **finding**: ensure a `findings/` page exists; keep 5 most recent in pulse.
   - **concept**: update "Active concepts under test" with status changes.
   - **question**: add to "Open questions" if novel; remove when resolved.
   - **focus-shift**: rewrite "Current focus."
3. Verify `pulse.md` fits the line cap. If not, promote oldest items to kb or drop — never silent truncation.
4. If POR-affecting events occurred and `por` is enabled, prompt the user in conversation to confirm POR updates and apply them.
5. Truncate `_journal/pulse.log`.
6. Run lint.
7. Commit (optional; on by default).

**Compaction triggers**:
- Manual: `/wrap-up` invoked by user before session end or context clear.
- Hooks: `PreCompact` and `SessionEnd` invoke wrap-up as safety net.

A session that ends without `/wrap-up` and without hooks firing leaves a stale log. Next session's first read of pulse should detect a non-empty log and either compact first or surface a warning.

---

## 12. Exchange protocol — capability: `multi_area`

Exchanges are how agents in one area get authoritative answers from another area without deep-reading the other area's kb.

**Filing.** Asker in area X invokes `/exchange <other-area> <question>`. Skill:

1. If `exchanges/<a>--<b>/` doesn't exist, creates it with `OWNERS`, `README.md`, `index.md`.
2. Creates `q-<date>-<slug>.md`:

```yaml
---
id: ex-2026-05-08-thermal-sensitivity
status: open                  # open | answered | follow_up | closed
asker_area: engineering
asker_role: hardware-engineer
responder_area: research
created: 2026-05-08
relevant_to: [thermal budget, detector responsivity]
---

# Question
What's the temperature dependence of responsivity for the 1310 nm
photodetector?

## Context
[[concepts/c-2026-04-shot-noise]]; spec [[specs/2026-05-detector-thermal/brief]]

# Response
(filled in by responder)

# Follow-up
(optional; asker can drill in)
```

3. Appends an entry to `exchanges/<a>--<b>/index.md`.

**Responding.** When work in the responder area happens, the responder invokes `/respond-exchange <id>`. If `task_subagents` is on, the responder spawns a subagent with the responder area's role context, restricted to writing the Response section. Subagent may use `/answer-from-kb` to pull existing kb pages by reference. On completion, status flips to `answered`.

**Reviewing the answer.** Asker reviews. If sufficient, `/close-exchange <id>` flips status to `closed`. If not, asker edits the Follow-up section and flips status to `follow_up`; the cycle repeats.

**Staleness.** Lint flags exchanges with `status: open` aged past the activity-day threshold; entries surface to INBOX under "Heads up."

**On disable.** Existing exchange directories remain. Skills become unavailable; CLAUDE.md's "Cross-area reads" section is removed. Re-enabling picks up existing exchanges.

---

## 13. Link conventions

Within `kb/` directories, agents use Obsidian-style `[[wikilinks]]`. For files outside `kb/` (code, manifests, specs, raw materials), agents use relative markdown links with explicit paths.

**Forward links** are written by the authoring agent. **Backlinks** are maintained by the linter via sidecar `<page>.links.json` files. The author never edits the sidecar.

**Linking to superseded pages is an error.** The linter suggests the replacement via `superseded_by`.

**Cross-area links are valid but watched.** Lint warns when a single page accumulates links to multiple distinct areas (default 3+). Pages with `area: commons` are exempt.

**Bidirectional content consistency** requires both lint and convention:

- **Lint (Rule 13)**: flag pages whose `links_out` point to pages updated more recently than the page itself. Output goes to INBOX or `/check` summary.
- **Convention** (in CLAUDE.md): after substantively updating a page, agents check the page's backlinks. For each backlinker, the agent decides whether the update affects what the backlinker asserts. If yes, the agent updates the backlinker inline (preferred) or files an INBOX "Heads up" entry.

---

## 14. Lint rules

The linter (`_framework/tools/lint.py`) is deterministic Python. It runs on demand via `/check` and at the end of every `/wrap-up`.

**All rules always run.** What changes per configuration is whether findings are *visible* (displayed and acted on) or *shadowed* (counted internally; surfaced as suggestions when frequent).

**Always-visible rules** (errors and structural correctness):

```
Rule 1.  Frontmatter validity.
Rule 2.  Forward-link integrity (including provenance.raw_path).
Rule 3.  Backlink synchronization.
Rule 5.  Supersession integrity.
Rule 6.  Type-specific completeness.
Rule 7.  Pulse size (pulse.md exceeding line cap is an error).
Rule 12. Data manifest integrity.
Rule 15. Index maintenance (regenerate areas-index.md, kb/index.md).
Rule 17. Raw immutability.
Rule 18. Maintenance category violations.
```

**Configurable-visibility rules** (warnings):

```
Rule 4.  Orphan detection.
Rule 8.  Stale concept warning (concept: under_test > 30 active days).
Rule 9.  Cross-area link threshold (>= N areas; commons pages exempt).
Rule 10. Promotion freshness (human_reviewed: false > 14 active days).
Rule 11. Spec hygiene (tasks non-terminal > 60 active days).
Rule 13. Backlinker freshness.
Rule 14. Exchange staleness (status: open > 7 active days, if multi_area on).
Rule 16. Cross-area read pattern.
```

**Shadow run behavior.** When a rule is shadowed, the linter still evaluates it but doesn't display findings in the standard report. Instead, the linter accumulates trigger counts and adds a suggestion section at the bottom of the report:

```
Disabled lint rules with significant findings:
  Rule 4 (orphans) — 12 findings
  Rule 11 (spec abandonment) — 3 findings

Consider enabling: /framework enable-lint rule_4
```

A rule's findings surface as a suggestion when the trigger count meets `shadow_suggest_threshold` (default 5).

**Activity-based thresholds.** All time thresholds use git-log-derived active days, computed via `_framework/tools/activity_days.py`.

**Capability-conditional rules.** Rule 14 (exchange staleness) only runs when `multi_area` is enabled.

The linter is the trust anchor. No LLM in the loop.

---

## 15. Skills

Each skill is a Claude Code Agent Skill with a `SKILL.md`. Skills can be invoked explicitly by slash command or autonomously when context matches the skill's trigger conditions.

**Always available:**

| Skill | Purpose |
|---|---|
| `framework` | Manage capabilities and lint visibility. |
| `start` | Route a fresh session: identify area, suggest role, load preload list. |
| `ingest` | Store raw material in `raw/`; create source summary in `kb/sources/` with provenance; link to concepts. |
| `ask` | Query the wiki; synthesize an answer; optionally file as kb page. |
| `plan` | Bootstrap a spec: brief → plan → tasks (human gates in conversation). |
| `implement` | Execute one task. Behavior depends on `task_subagents`. |
| `replan` | Append revision entry; update plan and tasks; require human approval. |
| `propose-promotion` | Copy area page to `commons/_proposed/`; generate proposal; register in INBOX. |
| `promote` | Apply promotion after consensus or human override; write CHANGELOG entry. Behavior depends on `formal_review`. |
| `wrap-up` | Compact `_journal/pulse.log` → `pulse.md`; file pending pages; prompt POR updates (if `por` on); run lint. |
| `check` | Run lint; display findings; surface shadow-rule suggestions. |

**Capability-gated:**

| Skill | Available when |
|---|---|
| `exchange` | `multi_area` on |
| `respond-exchange` | `multi_area` on |
| `close-exchange` | `multi_area` on |
| `answer-from-kb` | `multi_area` on |
| `review` | `formal_review` on |
| `review-promotion` | `formal_review` on |

---

## 16. Promotion-review protocol

The always-on protection: any change to `commons/` goes through `commons/_proposed/` first, with a human gate before promotion.

**Without `formal_review`.** Filing happens via `/propose-promotion`. The human reads the proposal (often in conversation, or via INBOX). The human approves or rejects. On approval, `/promote` applies the change.

**With `formal_review`.** After filing, `/review-promotion` spawns a subagent in each other area's reviewer role. Each subagent writes `verdict-<area>.md` with `APPROVE | OBJECT | ABSTAIN` plus rationale. Consensus rules apply: all non-abstain APPROVE → auto-promote; any OBJECT → human escalation; all ABSTAIN → human decides. The human still acks (`human_reviewed: true`) after promotion.

In both cases, audit trail (`_proposed/` directory, verdict files when applicable) is kept after promotion.

---

## 17. Subagent pattern — capability: `task_subagents`

When `task_subagents` is enabled, `/implement` spawns a fresh subagent for each task. The subagent's context is loaded from the role's preload list — it does not see the parent's working context.

**Without `formal_review`.** The subagent executes the task. The parent agent (or the human) reviews the output in conversation. No reviewer subagent.

**With `formal_review`.** After the subagent completes, `/review` spawns a reviewer subagent in a reviewer role variant. The reviewer reads the output against the spec and writes a verdict. On rejection, parent may re-invoke `/implement` with rejection notes (retry limit default 2). On second rejection, an auto-debug subagent loads in clean context to investigate root causes.

Subagents don't parallelize automatically, don't carry state between invocations except via files, and don't override role boundaries.

**On disable.** `/implement` switches back to running in the current agent. No content loss.

---

## 18. Raw materials and data manifests

Raw materials in `raw/` are immutable; source pages in `kb/sources/` summarize them with `provenance.raw_path` pointing to the raw file. Data manifests in `data/manifests/` describe datasets; structured input data lives in `data/`.

Manifest example:

```markdown
---
id: m-2026-05-photodetector-noise-run3
title: Photodetector noise floor measurements, run 3
type: source
area: research/optics
created: 2026-05-04
storage_uri: s3://...
schema_uri: ../schemas/noise-floor-v1.json
provenance:
  kind: internal-experiment
  acquired_on: 2026-05-04
  instrument: Keysight DSOX1204G + custom TIA board v0.3
context_pages:
  - [[concepts/c-2026-04-shot-noise]]
analysis_pages:
  - [[findings/f-2026-05-shot-noise]]
---

# Description
(Prose context — what's in the data, gotchas, known issues.)
```

Manifests link bidirectionally with kb. Lint enforces both directions.

---

## 19. What's deferred

- Multi-user collaboration.
- Search beyond `index.md`.
- CI integration (lint in CI).
- Web search ingest.
- Cross-spec contradiction review.

---

## 20. Bootstrap path

1. Create the template repo with `_framework/` populated, plus empty `commons/` and `areas/` skeletons. Write `CLAUDE.md` (always-on sections only), `_framework/config.yml` with initial state (all four capabilities off; all warnings shadowed).

2. Write `lint.py`, `pulse_compact.py`, `promote.py`, `framework.py`, and `activity_days.py` as deterministic Python.

3. Write the always-available skills as `_framework/skills/<name>/SKILL.md` with explicit trigger language. Write the capability-gated skills too, but the `framework` skill registers them with Claude Code based on `config.yml`.

4. Write `_framework/schema/capabilities.md` with one section per capability, declaratively describing the file edits each enable/disable operation performs.

5. Pick one project to instantiate. Write `commons/brief.md`. Pick 2 areas to start. Write area `brief.md` and one role per area.

6. **Pre-created at setup**: `INBOX.md` (empty), `areas-index.md` (lint populates), `roles/<role>/role.md` per area, `raw/` per area (empty subdirs), `kb/` per area (empty subdirs), `pulse.md` per area (empty template), `_journal/pulse.log` per area (empty). **On-demand**: exchanges (`/exchange` bootstraps), specs (`/plan` bootstraps), `_proposed/` entries (`/propose-promotion` bootstraps), POR files (when `/framework enable por` runs).

7. Run one end-to-end exercise: ingest 2–3 sources, run one spec brief → outcome, propose a finding to commons, promote it.

8. As the project grows, enable capabilities as signals appear. The framework skill handles all the mechanics.

---

## 21. Open questions

**Pulse line cap.** Default 80 lines. Reasonable across areas, or do some areas need different caps?

**Auto-debug retry limit.** Default 2 rejections before auto-debug fires (applies when `formal_review` on).

**Cross-area specs.** Default: spec lives under the area that owns the outcome; coordination via exchanges. Alternative: top-level `cross-area-specs/`. I'd avoid the alternative unless we find we need it.

**Sub-area POR.** Default: include but allow it to be a stub or omitted with a parent-POR note.

**Manifest type.** Marked `type: source`. Could add `type: data` if friction emerges.

**Raw subdirectory structure.** Suggested `papers/`, `articles/`, `transcripts/`, `web/`. Areas can add subdirs as needed; framework doesn't constrain.

**Shadow trigger threshold.** Default 5 findings before suggesting enable. Tunable in `config.yml`.

---

For the focused reference documents on individual topics (frontmatter, link conventions, lint rules, exchange protocol, promotion protocol, role template, capabilities), see the files in `_framework/schema/`.
