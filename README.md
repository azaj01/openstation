# Open Station

  A markdown-first, minimalistic and somewhere opinionated task management for coding AI agents.

  Markdowns are first-class citizens — tasks, specs, workflows, and agents are all
  simple `.md` files. Think of it as an optimized work environment for your AI agents, glued
  by a thin CLI with agentic harnesses.


## Why Open Station?

Coding agents can write code, but they have no structured way to receive tasks, report progress, or get their work verified. Most solutions add servers, databases, or dashboards. Open Station takes a different approach: a file-based convention with a defined lifecycle — no runtime, no dependencies, just markdown files with YAML frontmatter. A human (or designated reviewer) verifies every result before it ships, so agents propose and humans approve.

Since all outputs are .md artifacts, vim and Obsidian fit perfectly to view results, update tasks, and give agents instructions. Read the agent's findings and give feedback —manually or with the help of AI commands and agents.

## Features

- **Zero runtime** — no server, no database, no background process. Pure markdown files in your repo. Every competitor in this space requires a runtime; Open Station doesn't.
- **Defined agentic lifecycle** — Agents know pick up ready tasks, execute work, produce artifacts, hand off for review and verification.
- **Convention-first** — everything is markdown + YAML frontmatter, version-controlled alongside your code
- **Minimal, thus extensible** — `openstation init` scaffolds into any project under `.openstation/`. Minimal footprint allows to add your own agentic harnesses and combine with any tooling.
- **Adaptive** —  agents, skills, and commands are all markdown files you own.
  Reshape them to fit your project. Open Station is a starting point, not a framework

> Open Station manages its own development — every feature, bug fix, and research task goes through the same lifecycle that ships to users. See [`artifacts/tasks/`](artifacts/tasks/) for real examples.

## Install

**One-liner** (installs the CLI and scaffolds the project):

```bash
curl -fsSL https://raw.githubusercontent.com/leonprou/openstation/main/install.sh | bash
```

This does two things:

1. **Installs the CLI** — downloads `openstation` to `~/.local/bin/`
2. **Scaffolds the project** — runs `openstation init` to create the `.openstation/` vault, set up `.claude/` symlinks, and inject the managed section into `CLAUDE.md`

To scaffold additional projects after the CLI is installed, run `openstation init` directly from the project directory.

**Options:**

| Flag | Description |
|------|-------------|
| `--local PATH` | Copy from a local clone instead of downloading |
| `--no-agents` | Skip installing example agent specs |
| `--force` | Overwrite user-owned files during re-init |
| `--dry-run` | Show what would be done without writing |

## Quick Start

### One-time setup

```bash
openstation init
```

Creates the `.openstation/` vault (directories, docs, commands, skills), installs agent templates, and sets up `.claude/` symlinks so Claude Code discovers agents and commands. Safe to re-run — existing files are preserved.

### Daily workflow

**1. Create a task**

```
/openstation.create Add input validation to the signup form
```

A short interview refines requirements, picks an agent, and sets the task to `ready`.

**2. Run the task**

```bash
openstation run --task 0001-add-input-validation
```

The agent picks up the task, follows the manual, executes the work, and sets `status: review` when done.

**3. Review the result**

```bash
openstation show 0001 --vim # `openstation show 1` will work too
```

**4. Verify and complete**

```
/openstation.done 0001-add-input-validation
```

## Vault Structure

```
docs/              — Project documentation (lifecycle, task spec, README)
artifacts/         — Canonical artifact storage (source of truth)
  tasks/           —   Task files
  research/        —   Research outputs
  specs/           —   Specifications & designs
agents/            — Agent specs (identity + skill references)
skills/            — Agent skills (not user-invocable)
commands/          — User-invocable slash commands
```

When installed into another project, these are placed under `.openstation/`.

## Agents

Open Station ships with template agents. Each is a markdown file you own — edit or create new ones to fit your project. See [`docs/agent.spec.md`](docs/agent.spec.md) for the full spec format.

| Agent | Role |
|-------|------|
| **project-manager** | Creates tasks, assigns agents, reviews completed work |
| **architect** | Designs systems, writes specs, sets technical standards |
| **developer** | Turns specs into working code and tests |
| **researcher** | Gathers and synthesizes information from code, docs, and the web |
| **author** | Crafts agent specs, skills, commands, and documentation |

## Architecture

```
  You                      Open Station                    Agent
   │                            │                            │
   ├── /openstation.create ────►│                            │
   │   (interview + ready)      │                            │
   │                            ├── openstation run ────────►│
   │                            │                            ├── discover task
   │                            │                            ├── execute work
   │                            │                            ├── produce artifacts
   │                            │◄── status: review ─────────┤
   │                            │                            │
   ├── review (show --vim) ────►│                            │
   ├── /openstation.done ──────►│                            │
```

Under the hood: `lifecycle.md` defines the state machine, `task.spec.md` defines the file format, and each agent loads the `execute` skill to discover and run tasks.

## Commands

| Command                 | Description                                        |
| ----------------------- | -------------------------------------------------- |
| `/openstation.create`   | Create a new task spec from a description          |
| `/openstation.list`     | List all tasks with status, agent, and dates       |
| `/openstation.show`     | Show full details of a single task                 |
| `/openstation.ready`    | Promote a task from backlog to ready               |
| `/openstation.update`   | Update task frontmatter fields                     |
| `/openstation.done`     | Mark a task done and move it to done/              |
| `/openstation.reject`   | Reject a task in review and mark it failed         |
| `/openstation.dispatch` | Preview agent details and show launch instructions |

## What a Task Looks Like

Every task is a single markdown file with YAML frontmatter:

```yaml
---
kind: task
name: 0001-add-input-validation
status: ready
assignee: developer
owner: user
created: 2026-03-01
---

# Add Input Validation

## Requirements

Validate email and password fields on the signup form.
Reject empty submissions and show inline errors.

## Verification

- [ ] Empty email shows error
- [ ] Invalid email format rejected
- [ ] Password minimum length enforced
```

Create this file, dispatch an agent, and it picks up the work. When it's done, the owner verifies and marks it complete. That's the entire loop.

## License

	MIT
