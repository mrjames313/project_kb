# Frontmatter Specification

Every markdown file in `kb/` directories and every data manifest carries YAML frontmatter. This document is the canonical reference.

## Required fields on all kb pages

```yaml
---
id: f-2026-05-shot-noise-1310nm        # stable; <type-prefix>-<date>-<slug>
title: Shot noise floor at 1310nm photodetector
type: finding                           # source | concept | finding | decision
status: active                          # see type-specific lifecycles below
area: research/optics                   # path; "commons" for shared
created: 2026-05-04
updated: 2026-05-04
summary: At 1310nm with 1mA photocurrent, shot noise dominates above ~10kHz.
relevant_to:                            # topical hints; omit for commons pages
  - photodetector design
  - noise budget
  - 1310nm wavelength
---
```

### ID prefixes by type

- `s-` — source
- `c-` — concept
- `f-` — finding
- `d-` — decision

### `area`

For `commons/kb/` pages, set `area: commons`. For area pages, use the path under `areas/` (e.g., `research`, `research/optics`, `business-model`).

### `relevant_to`

Topical hints used by agents to decide whether a page is worth loading into context. Omit for `commons/kb/` pages — commons is by definition relevant to everyone.

### `summary`

One sentence (≤25 words). The "index card" version of the page. Agents read this before deciding whether to load the body.

## Type-specific fields

### `source`

```yaml
type: source
provenance:
  kind: external                        # external | internal-experiment | internal-notes
  title: Saleh & Teich, Photonics, ch 17
  author: Saleh, B.E.A.; Teich, M.C.
  url: ...                              # if external and web-accessible
  retrieved: 2026-04-12
  raw_path: raw/papers/saleh-teich-ch17.pdf
```

Lifecycle: `active` | `archived` | `superseded`.

The body of a source page is the structured summary of the raw material — key points, claims worth tracking, methods used, caveats. This summary is what agents cite when building concepts and findings; they don't re-read the raw PDF every time. Direct quotes (with location) may be used sparingly when exact wording matters.

### `concept`

```yaml
type: concept
status: under_test                      # see lifecycle below
evidence:                               # required if status is under_test or later
  - [[experiments/2026-04-photodetector-noise]]
  - [[sources/saleh-teich-ch17]]
confidence: medium                      # low | medium | high
```

Lifecycle:

- `seed` — initial spark; phrase as "one direction is..."
- `developing` — informal idea; phrase as "the working idea is..."
- `under_test` — formal claim with evidence being gathered.
- `supported` — sufficient evidence; ready for promotion to finding.
- `falsified` — disproven; anti-repetition memory.
- `dropped` — abandoned without resolution.
- `superseded` — replaced; follow `superseded_by`.

### `finding`

```yaml
type: finding
provenance:
  kind: concept                         # concept | external | experiment
  ref: [[concepts/c-2026-04-shot-noise]]
  raw_path: ~                           # populated if finding derives directly from raw material
evidence:
  - [[experiments/2026-04-photodetector-noise]]
confidence: high
superseded_by: ~
```

Lifecycle: `active` | `archived` | `superseded`.

A finding's provenance points back to the concept it was promoted from (`kind: concept`) or to an external source if it came in already-established (`kind: external`, with `raw_path` populated).

### `decision`

```yaml
type: decision
alternatives_considered:
  - [[concepts/c-2026-04-balanced-detection]]
  - [[concepts/c-2026-04-lower-bias]]
rationale_summary: ...
superseded_by: ~
```

Lifecycle: `active` | `superseded`.

## Commons-promoted items

Pages promoted into `commons/kb/` carry three additional fields:

```yaml
human_reviewed: false                   # flipped to true when human acks
promoted_from: areas/research/optics
promoted_on: 2026-05-08
```

## POR files

`POR.md` files (when the `por` capability is enabled) use a simpler frontmatter:

```yaml
---
type: por
area: research/optics
phase: detector characterization (2 of 4)
last_updated: 2026-05-08
---
```

## Lint-maintained, not author-written

The fields `links_in` and `links_out` are not written into the frontmatter directly. The linter maintains them in a sidecar `<page>.links.json` so they don't clutter the human-edited file. The sidecar is git-ignored.

## Field ordering convention

For readability, frontmatter fields appear in this order:

1. `id`
2. `title`
3. `type`
4. `status`
5. `area`
6. `created`, `updated`
7. `summary`
8. `relevant_to`
9. Type-specific fields (`provenance`, `evidence`, `confidence`, `alternatives_considered`, etc.)
10. Commons-promotion fields (`human_reviewed`, `promoted_from`, `promoted_on`) if present
11. `superseded_by` if present

Lint does not enforce ordering, but agents writing new pages should follow it.
