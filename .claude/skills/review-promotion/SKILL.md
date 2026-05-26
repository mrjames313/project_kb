---
name: review-promotion
description: Independent review of a commons promotion proposal from the perspective of the reviewer's area. Files a verdict file (APPROVE | OBJECT | ABSTAIN) in commons/_proposed/<slug>/. Requires the formal_review capability.
---

# /review-promotion

Reviews a proposal staged in `commons/_proposed/<slug>/` from the perspective of the reviewer's area. Files a verdict that feeds into `/promote`'s acceptance decision.

## When to use

- A `/propose-promotion` was filed, and the proposal lists the reviewer's area as `affected`.
- The orchestrator (or coordinator) routes the review to the reviewer's area's reviewer role.
- Most commonly invoked by an orchestrator when a proposal is staged with cross-area implications.

Like `/review`, this is run by the **reviewer role** (a stripped-down variant of the implementer role with read-broad, write-narrow boundaries). The reviewer subagent's only job is to produce one verdict file and exit.

## Steps

1. **Read the proposal.** Everything in `commons/_proposed/<slug>/`:
   - `page.md` — the page being proposed for commons.
   - `proposal.md` — proposing area, proposer, rationale, list of affected areas.
   - Any existing `verdict-*.md` files from other areas (for cross-reviewer awareness, not for influence).

2. **Read the source page.** The proposal is a copy of an area kb page. Locate the original at `areas/<proposing-area>/kb/<type>/<id>.md` and read it (to confirm the proposal is a faithful copy and to see how it's used in its original context).

3. **Read your area's relevant pages.** Look at what your area already says about the topic:
   - `kb/findings/` and `kb/decisions/` pages with overlapping `relevant_to` tags.
   - `kb/concepts/` pages that might be affected if this becomes commons.

4. **Evaluate from your area's perspective.** Three concrete questions:
   - **Is the page correct as stated?** Would your area's evidence agree, or do you have findings/decisions that contradict it?
   - **Is "commons" the right home?** Or is the claim actually area-specific to the proposer's area, and would be wrongly generalized by being in commons?
   - **What's the downstream effect on your area?** If this lands, will your area's pages need updates (e.g., yours assumed the opposite, or yours cites something this contradicts)?

5. **Pick a verdict.**
   - **APPROVE** — the page is correct, broadly applicable, and your area is fine with it landing in commons. Brief rationale.
   - **OBJECT** — at least one of: incorrect as stated, mis-scoped for commons, or in direct conflict with your area's findings/decisions. Verdict must cite the conflict with `[[wikilinks]]` and state what would change it to APPROVE (e.g., "narrow the claim to apply only to X case", "add a caveat about Y").
   - **ABSTAIN** — this doesn't materially affect your area. Briefly explain (you're saying "we don't care", not "we're unsure").

6. **Write the verdict file** at `commons/_proposed/<slug>/verdict-<your-area>.md`:
   ```yaml
   ---
   reviewer_area: <your-area>
   reviewer_role: <your-reviewer-role>
   reviewed_on: 2026-05-15
   verdict: APPROVE | OBJECT | ABSTAIN
   ---

   # Promotion review: <slug>

   ## Verdict: <verdict>

   ## Assessment

   2–4 sentences on the proposed page from your area's perspective.

   ## Conflicts / Concerns

   (Required for OBJECT; optional for APPROVE; brief abstention reason for ABSTAIN.)

   - <bullet> citing `[[wikilinks]]` to your area's pages that conflict or that this would affect
   - <bullet> what would change it to APPROVE

   ## Notes

   (Optional. Suggestions for the proposer or for narrowing the proposal.)
   ```

7. **Verify.** Run `python _framework/tools/lint.py`. Verdict files have minimal lint requirements; the main check is that any `[[wikilinks]]` to your area's pages resolve.

8. **Exit.** The reviewer subagent does not journal, does not run `/wrap-up`. The orchestrator (or coordinator, or human) reads the verdict before invoking `/promote`.

## Notes

- The reviewer role for each area is auto-generated when `formal_review` is enabled (see `/framework enable formal_review`). It mirrors the implementer's preload so it has the same context — but writes only to verdict files.
- The reviewer must read the proposing area's kb broadly enough to evaluate the proposal in its original context. That's fine — reviewers are read-broad by design.
- An OBJECT does not auto-reject the proposal. `/promote` surfaces the OBJECT to the user; the proposer can revise the proposal (or narrow the claim), then re-request review.
- If multiple affected areas all ABSTAIN, the proposal can still proceed — `/promote` will check that there are no OBJECTs but ABSTAINs are non-blocking.
- An ABSTAIN with reason "this is outside our area's interests" is more useful than no verdict at all. It tells the proposer "we looked and we don't care," which is closure.
- Don't APPROVE just to be agreeable. If your area's evidence says otherwise, OBJECT with specifics. That's the point of formal review.
