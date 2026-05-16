# Role Template

A role file lives at `<area>/roles/<role-name>/role.md` and defines what context an agent in that role loads and what they're allowed to do.

The template below shows the full shape. Sections marked `# capability: X` are inserted by the `/framework` skill when the relevant capability is enabled and removed when it's disabled. Don't add these sections manually.

```markdown
---
role: <role-name>
area: <area-path>
summary: <one sentence describing what this role does>
---

# <Role Name>

## Preload context (explicit; do not infer additional)

Schema and conventions:
1. /CLAUDE.md
2. /_framework/schema/frontmatter.md
3. /_framework/schema/link-conventions.md

Project and parent area:
4. /commons/brief.md
5. /commons/pulse.md
# capability: por
6. /commons/POR.md
# end capability: por
7. /areas/<parent>/brief.md                 # only for sub-areas
8. /areas/<parent>/pulse.md                 # only for sub-areas
# capability: por
9. /areas/<parent>/POR.md                   # only for sub-areas
# end capability: por

Own area:
10. /areas/<area-path>/brief.md
11. /areas/<area-path>/pulse.md
# capability: por
12. /areas/<area-path>/POR.md
# end capability: por
13. /areas/<area-path>/kb/index.md

## Operating boundaries

- Writes allowed: /areas/<area-path>/** EXCEPT /areas/<area-path>/raw/**.
- Raw materials anywhere are read-only; treat as immutable.
- Writes to /commons/: forbidden; use /propose-promotion.
- Writes to other areas: forbidden.
# capability: multi_area
- Cross-area knowledge: prefer /exchange over deep reads into other areas' kb bodies.
# end capability: multi_area
- Reads allowed: full repo.

## Allowed skills

start, ingest, ask, plan, implement, replan, wrap-up, check, propose-promotion, promote, framework
# capability: multi_area
exchange, respond-exchange, close-exchange, answer-from-kb
# end capability: multi_area
# capability: formal_review
review
# end capability: formal_review

## Default behaviors

- Cite using [[wikilinks]].
- When citing a concept, surface its status ("we're testing whether...", "we have evidence that...").
- When ending a session, run /wrap-up before clearing.
- When a task's plan looks wrong, invoke /replan; do not improvise.
- Ask the human in conversation when uncertain. INBOX is for items the human will see later, not a substitute for asking now.
```

## Reviewer role variants

When `formal_review` is enabled, a reviewer variant exists for each implementer role:

- **Preload context** — same as the implementer role.
- **Operating boundaries** — read full repo; writes restricted to the verdict file at `commons/_proposed/<slug>/verdict-<area>.md` (or equivalent for task review).
- **Allowed skills** — only `review`.

## Coordinator role

When `por` is enabled, a project-wide coordinator role lives at `commons/roles/coordinator/role.md`. It is read-broad, write-narrow:

- **Preload context** — `CLAUDE.md`, schema files, `commons/brief.md`, `commons/POR.md`, `areas-index.md`, all area `POR.md` files, `INBOX.md`.
- **Operating boundaries** — writes allowed to `INBOX.md`, `commons/POR.md`, and to specs across areas. Cannot write area kb or commons kb.
- **Purpose** — cross-area planning, INBOX management, POR updates, routing for requests that span multiple areas.
