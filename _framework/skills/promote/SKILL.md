---
name: promote
description: Accept a proposal from commons/_proposed/<slug>/ and move the page into commons/kb/. Updates frontmatter, writes a CHANGELOG entry, and leaves an audit trail.
---

# /promote

Accepts a staged proposal and moves the page into `commons/kb/`. Typically run by the coordinator (when `por` is enabled) or by a human reviewer.

## When to use

- A proposal exists at `commons/_proposed/<slug>/` (created via `/propose-promotion`).
- The proposal has been reviewed:
  - With `multi_area` enabled: each affected area has filed a verdict file. The proposal is acceptable if there are no `OBJECT` verdicts.
  - Without `multi_area`: a human has confirmed the proposal should land.

## Steps

1. **Verify the proposal is acceptable.** Read every file in `commons/_proposed/<slug>/`:
   - `proposal.md` — confirm the rationale.
   - `page.md` — confirm the page is lint-clean and at a settled status.
   - Any `verdict-<area>.md` files (if `multi_area` is on) — if any has verdict `OBJECT`, surface that to the user and stop. The objecting area must approve (or change to ABSTAIN) before promotion can proceed.

2. **Run the promote tool.**
   ```
   python _framework/tools/promote.py <slug>
   ```
   The tool:
   - Moves `commons/_proposed/<slug>/page.md` → `commons/kb/<type>/<id>.md`.
   - Updates frontmatter: `area: commons`, `human_reviewed: false`, `promoted_from: <proposing-area>`, `promoted_on: <today>`, `updated: <today>`.
   - Prepends a CHANGELOG entry to `commons/CHANGELOG.md`.
   - Leaves `proposal.md` and verdict files in `commons/_proposed/<slug>/` as audit trail.

3. **Handle area-side cleanup.** The original page in the proposing area's kb is still there. Talk to the user about what to do:
   - **Most common**: mark the area copy `superseded` with `superseded_by: "[[<commons-id>]]"`. Then other area pages that cited the area copy still resolve through the supersession chain.
   - **Sometimes**: keep both, if the area version has area-specific framing that the commons version doesn't.

4. **Verify.** Run `python _framework/tools/lint.py`. The promoted page should be lint-clean. If the area copy was marked superseded, the supersession integrity rule (5) will check that `superseded_by` is populated.

5. **Record in pulse.log.** In whichever pulse log is most appropriate (the coordinator's commons pulse, or the proposing area's pulse):
   ```
   ## [YYYY-MM-DD HH:MM] decision <role>
   Promoted <page-id> to commons (from <proposing-area>).
   ```

6. **Brief the user.** Confirm what was promoted, what the new commons id is, and what (if any) area-side cleanup is still pending.

## Notes

- `promote.py` refuses to overwrite an existing file. If the target id already exists in commons, surface that — either the proposal duplicates an existing commons page (close the proposal as redundant) or the page needs a different id.
- The promoted page lands with `human_reviewed: false`. A human can later flip this to `true` after they've reviewed; until then, lint rule 10 (a configurable warning) can surface unverified commons pages.
- The audit trail in `commons/_proposed/<slug>/` is deliberately retained. Don't delete it; it's the record of who proposed what, when, and why.
- After promotion, references to the original area page (via `[[id]]`) still work *if* the area page was marked `superseded` with `superseded_by` pointing at the commons id. Other area pages need not be updated — supersession chains resolve automatically.
- Promotion does not pull dependent pages along with it. If the page references `[[c-foo-thing]]` and `c-foo-thing` is also area-local, you may need to promote that one too. Lint rule 9 (configurable warning) can surface unresolved cross-area citations in commons pages.
