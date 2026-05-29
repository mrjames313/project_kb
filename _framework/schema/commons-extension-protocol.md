# Commons-extension protocol

A flow for opportunistically promoting area kb pages into commons at the moment a new area is added. Distinct from `/propose-promotion` + `/promote`, which is the proposal-based pathway for individual page promotions over the project's lifetime.

## When to use commons-extension

Triggered automatically (default on) during `/add-area` when ≥1 area already exists. The user passes `--no-extend-commons` to skip.

The intuition: when a new area is added, the addition itself reveals which knowledge is now cross-cutting. A finding written for one area may have been correctly area-scoped at the time but becomes obviously commons-worthy once a second area exists that would also reach for it. Commons-extension catches these moments instead of leaving them for the proposal-promote pathway later.

## When NOT to use it

- For a finding that's clearly area-specific (synthesis framed around how *this* area thinks about something). Use `/propose-promotion` later if it turns out to generalize.
- For the project's first area. Nothing to extend from.
- During mid-area work. Promotions of individual pages outside of the area-addition moment go through `/propose-promotion`.

## Difference from `/propose-promotion` + `/promote`

| Dimension | Commons-extension | Propose-promotion + promote |
|---|---|---|
| When triggered | At `/add-area` time | Anytime |
| Trigger reason | New area reveals cross-cutting knowledge | Single page proves broadly useful |
| Proposal step | None (interactive at add-area time) | `commons/_proposed/<slug>/` directory |
| Review step | Inline (user confirms each candidate) | Verdict files (if `formal_review` on) |
| Source page treatment | Left unchanged | Left unchanged (per protocol) |
| Bulk vs individual | Bulk (many pages in one flow) | Individual (one page per cycle) |
| Refinement | Agent decides per candidate | Agent decides during proposal |
| Frontmatter marker | `promotion_path: commons-extension`, `promoted_during_add_area: <name>` | `promoted_from`, `promoted_on` |

Both paths leave the source area page intact and create a new commons page. Both append to `commons/CHANGELOG.md`. The commons-extension flow's CHANGELOG entries are distinguishable (`commons-extension` tag) so a maintainer can audit either pathway independently.

## ID convention

The new commons page's id replaces the date segment of the source id with the literal `commons`:

- Source: `f-2026-05-26-accredited-investor-definition-and-verification`
- New commons: `f-commons-accredited-investor-definition-and-verification`

The date is dropped because commons content is conceptually timeless — the source page's date is the historical artifact, preserved in the source page itself (which remains in place). The new commons page's `created` and `updated` fields carry the extension date.

This convention guarantees no id collision between the source and the new commons version, so existing wikilinks targeting the source id continue to resolve to the source. References that should switch to the canonical commons version do so explicitly.

## Refinement vs copy-as-is

The agent decides per candidate. Two cases:

- **Copy as-is**: the source page's body is already in suitably general framing. Common for primary regulatory mechanics, definitions, and other content where the language was already generalized when written.
- **Refine**: the source page's body uses area-specific framing that would read awkwardly when invoked by another area. The agent rewrites the body for general framing, keeping the substantive content intact.

The user is shown which path the agent took (the `refined: true|false` flag in the tool's output) and can review the resulting commons page before continuing. If refinement is wrong, the user can edit the commons page directly afterward.

## Growth control

In a healthy project, commons-extension during the *2nd* area's addition tends to surface the most candidates — that's the moment when most foundational cross-cutting content gets identified. Subsequent additions should surface progressively fewer candidates as commons stabilizes.

If during a later area's addition the candidate count is still high, that may signal:

- The project's areas are genuinely disparate (the "shared ground" framing is breaking down).
- The new area covers ground commons doesn't already capture (which is fine).
- Commons has been under-populated and is catching up (also fine, but worth noting).

The skill's context-display step shows the user this framing so judgment calls are informed. A future `commons_coverage` configuration parameter could enforce growth-control policy explicitly; v1 leaves this to the user.

## When the source page should be updated

The protocol deliberately leaves source area pages untouched during commons-extension. This is the right default — the area stays self-consistent, existing wikilinks keep working.

A user who decides the source page should now be superseded by the commons version (because the commons version is canonical and the area-specific framing is no longer needed) can manually:

1. Set the source page's `status: superseded`.
2. Set `superseded_by: <commons-id>`.
3. Update the source page's body to point readers at the commons version, if desired.

This is a separate step from commons-extension and is the user's call. The framework doesn't auto-supersede because the decision is content-specific.

## Auditing extensions later

To see all commons pages created via commons-extension:

- Search `commons/kb/**/*.md` for frontmatter `promotion_path: commons-extension`.
- Or grep `commons/CHANGELOG.md` for `commons-extension`.

The `promoted_during_add_area` field shows which area-addition triggered the extension, which is useful when tracing back why a piece of commons content was first introduced.
