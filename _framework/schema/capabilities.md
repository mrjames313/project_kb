# Capabilities

The framework has four togglable capabilities. The `/framework` skill reads this document and applies the listed changes when capabilities are enabled or disabled.

Each capability section below describes:

- **Identity** — the key in `config.yml`.
- **Default** — initial state at template bootstrap.
- **Dependencies** — capabilities that must also be enabled.
- **Files created on enable** — what comes into existence.
- **Files made inert on disable** — content that stays on disk but stops being referenced.
- **CLAUDE.md sections** — which schema document sections are added/removed.
- **Role file edits** — what changes in role files (preload lists, boundaries, allowed skills).
- **Skill availability** — which skills become available or unavailable.
- **Lint rule changes** — which rules start or stop running.

---

## `multi_area`

**Identity**: `capabilities.multi_area`

**Default**: `false`

**Dependencies**: none

**Files created on enable**: none (exchange directories are created on demand by `/exchange` when first invoked).

**Files made inert on disable**: existing `exchanges/<a>--<b>/` directories. They remain on disk but skills become unavailable.

**CLAUDE.md sections**:
- Insert on enable: `## Cross-area reads`
- Remove on disable: same.

**Role file edits**:
- Insert in **Operating boundaries** (on enable): "Cross-area knowledge: prefer `/exchange` over deep reads into other areas' kb bodies."
- Insert in **Allowed skills** (on enable): `exchange, respond-exchange, close-exchange, answer-from-kb`.
- Remove on disable: same.

**Skill availability**: `exchange`, `respond-exchange`, `close-exchange`, `answer-from-kb`.

**Lint rule changes**: Rule 14 (exchange staleness) starts running on enable.

---

## `por`

**Identity**: `capabilities.por`

**Default**: `false`

**Dependencies**: none

**Files created on enable**:
- `commons/POR.md` (with placeholder template content; user fills in).
- `areas/<area>/POR.md` for every existing area and sub-area (same).
- `commons/roles/coordinator/role.md` with the coordinator role definition.

**Files made inert on disable**: existing POR files remain on disk. The coordinator role file is removed from `commons/roles/`.

**CLAUDE.md sections**:
- Insert on enable: `## POR discipline`.
- Remove on disable: same.

**Role file edits**:
- Insert in **Preload context** (on enable, every role): `/commons/POR.md` and `/areas/<their-area>/POR.md`.
- Remove on disable: same.

**Skill availability**: none added. The `wrap-up` skill changes behavior (prompts for POR updates when relevant events happened), but the skill itself is always available.

**Lint rule changes**: none.

**Coordinator role behavior**: the coordinator handles cross-area routing for requests that span multiple areas. When `por` is disabled, the `start` skill asks the human to pick an area instead of auto-routing to a coordinator.

---

## `task_subagents`

**Identity**: `capabilities.task_subagents`

**Default**: `false`

**Dependencies**: none

**Files created on enable**: none.

**Files made inert on disable**: none.

**CLAUDE.md sections**:
- Insert on enable: `## Subagent pattern`.
- Remove on disable: same.

**Role file edits**: none.

**Skill availability**: none added. The `/implement` skill changes behavior — without `task_subagents`, it runs the work in the current agent; with `task_subagents`, it spawns a fresh subagent loaded from the role's preload list.

**Lint rule changes**: none.

---

## `formal_review`

**Identity**: `capabilities.formal_review`

**Default**: `false`

**Dependencies**: `task_subagents` must be enabled. If `formal_review` is requested without `task_subagents`, the `framework` skill offers to enable both.

**Files created on enable**: for each existing area, a reviewer variant of each role at `areas/<area>/roles/<role-name>-reviewer/role.md`. Reviewer role files are derived from the implementer role's preload list, with `Operating boundaries` restricted to writes within the verdict file path, and `Allowed skills` limited to `review`.

**Files made inert on disable**: reviewer role files are removed from each area's `roles/` directory.

**CLAUDE.md sections**:
- Insert on enable: `## Formal review`.
- Remove on disable: same.

**Role file edits**:
- Insert in **Allowed skills** (on enable, implementer roles only): `review`.
- Remove on disable: same.

**Skill availability**: `review`, `review-promotion`.

**Lint rule changes**: none.

**Behavior changes**:
- `/implement` followed by `/review` now spawns a reviewer subagent that produces a verdict.
- Two rejections trigger an auto-debug subagent.
- `/propose-promotion` triggers `/review-promotion` for each other area; per-area verdict subagents produce `verdict-<area>.md` files. Consensus rules apply.

---

## Lint warning toggles

Separately from capabilities, individual lint warning rules can be enabled or disabled via `/framework enable-lint <rule>` and `/framework disable-lint <rule>`. The configurable rules are listed in `lint-rules.md`. Default: all warning rules are shadowed (off-visible); errors are always visible.
