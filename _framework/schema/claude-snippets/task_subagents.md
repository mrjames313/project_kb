## Subagent pattern

When `task_subagents` is enabled, `/implement <spec> <task-id>` spawns a fresh subagent for the task. The subagent:

- Loads context from the role's preload list — not from the parent's working context.
- Reads the spec's `brief.md`, `plan.md`, and its single task block from `tasks.md`.
- May follow links from the task to additional pages as needed.
- Writes outputs to the task's declared `_Boundary:_`.
- Appends notes to `## Implementation Notes` in the task block.

Each task in `tasks.md` should be specified so it can be executed by an agent that has only the spec context plus the role's preload — no working memory carried over from prior tasks. The `_Depends:_` annotation tells the subagent which prior tasks must be complete (their outputs available on disk).

Subagents don't parallelize automatically and don't carry state between invocations except via files. Everything important must be persisted to wiki, spec, or pulse log.
