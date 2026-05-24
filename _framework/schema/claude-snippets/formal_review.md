## Formal review

When `formal_review` is enabled, three reviewer mechanisms come online (all require `task_subagents`):

**Task review.** After `/implement <spec> <task-id>` completes, `/review` spawns a reviewer subagent in a reviewer role variant. The reviewer reads the produced output against `brief.md`, `plan.md`, and the task block, then writes a verdict. On rejection, the parent may retry up to twice; a second rejection triggers auto-debug.

**Auto-debug.** Spawns in clean context to investigate root causes after the second rejection. Auto-debug doesn't retry the task — it analyzes why the task is stuck and surfaces findings to the human for direction.

**Promotion review.** `/propose-promotion` triggers `/review-promotion` for each other area. Each area's reviewer subagent reads the proposal and writes a `verdict-<area>.md` with `APPROVE | OBJECT | ABSTAIN` plus rationale. Consensus rules: all-non-abstain APPROVE → auto-promote; any OBJECT → escalate to human; all ABSTAIN → human decides.

Reviewer roles are read-broad, write-narrow: they can read the full repo but write only their verdict file. They use the same preload list as the implementer role they shadow.
