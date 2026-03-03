---
kind: task
name: 0033-python-developer-agent
status: done
agent: author
owner: manual
created: 2026-03-03
---

# Adjust Developer Agent to Python Stack

## Requirements

Update the developer agent spec (`artifacts/agents/developer.md`)
to reflect the project's actual technology stack — Python instead
of Bun.js/TypeScript.

1. **allowed-tools** — replace Bun/npx bash patterns with Python
   equivalents:
   - Add `"Bash(python *)"` and `"Bash(python3 *)"`
   - Add `"Bash(pip *)"` and `"Bash(pytest *)"`
   - Remove `"Bash(bun *)"` and `"Bash(npx *)"`
2. **Description & capabilities** — rewrite to reference Python,
   pytest, pyenv, and standard library tooling instead of
   TypeScript, Bun.js, and ESM
3. **Technical expertise** — replace TypeScript/Bun sections with
   Python, pytest, argparse, pathlib, etc.
4. **Constraints** — update "prefer Bun.js" to "prefer pyenv-managed
   Python" and adjust test runner references to pytest

## Verification

- [ ] `allowed-tools` includes `python`, `python3`, `pytest` bash patterns
- [ ] `allowed-tools` no longer references `bun` or `npx`
- [ ] Description references Python stack, not TypeScript/Bun
- [ ] Agent can run `python3 -m pytest` in tier 2 mode
