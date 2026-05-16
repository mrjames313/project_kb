# Project Orchestration Framework

A lightweight framework for orchestrating multi-area project development with Claude Code agents. Knowledge, code, and data are organized around shared project structures and area-specific structures, with disciplined paths for information to flow between them.

## Getting started

Launch Claude Code in a fresh directory and ask it:

> Follow the setup instructions at https://github.com/mrjames313/project_kb/blob/main/SETUP.md

Claude will read [SETUP.md](SETUP.md), ask you a handful of questions (project name, what it's about, your first area, your first role), and bootstrap a customized project for you. Setup takes 5–10 minutes.

## What's here

- **[SETUP.md](SETUP.md)** — the bootstrap runbook Claude follows to create a new project.
- **[_framework/spec.md](_framework/spec.md)** — the full framework specification.
- **[_framework/adoption-guide.md](_framework/adoption-guide.md)** — how to start minimal and extend as your project grows.

## Concepts in 30 seconds

A project has **areas** — specialized knowledge domains like research, engineering, product, or business model. Each area is a folder with its own knowledge base, raw materials, code, and data, and operates with significant autonomy. Distilled findings flow up from areas to a shared **commons** through a defined promotion protocol; project direction flows down from commons to areas.

Each area defines **roles** with explicit context-loading rules. Each kb page carries **frontmatter** (type, status, relevance hints) that tells agents how to interpret and load it. Work is structured by **specs** (brief → plan → tasks → outcome) with explicit phase gates.

A small always-on foundation handles the typical case. Four togglable capabilities (`multi_area`, `por`, `task_subagents`, `formal_review`) add machinery when projects grow into needing them, managed through the `/framework` skill.

## License

MIT — see [LICENSE](LICENSE).
