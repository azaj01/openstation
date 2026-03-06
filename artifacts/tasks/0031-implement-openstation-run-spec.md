---
kind: task
name: 0031-implement-openstation-run-spec
status: done
assignee: developer
owner: project-manager
created: 2026-03-01
---

# Implement openstation-run.sh spec updates

Apply the collection + execution restructuring from `docs/openstation-run.md`
to the actual `openstation-run.sh` shell script.

## Requirements

1. The spec (`docs/openstation-run.md`) has been restructured around
   two orthogonal concerns: **task collection** and **task execution**.
   Update `openstation-run.sh` to match any structural or naming
   changes implied by the spec.

2. Ensure the script's internal comments and function grouping
   reflect the collection → execution pipeline:
   - Collection helpers: `find_task_dir()`, `assert_task_ready()`,
     `find_ready_subtasks()`
   - Execution helpers: `find_agent_spec()`, `parse_allowed_tools()`,
     `build_command()`, `get_field()`

3. Verify that all CLI flags, exit codes, and tier constraints
   documented in the spec are implemented correctly in the script.

4. Ensure `--max-tasks` caps queue consumption in task collection
   mode as specified.

5. Agent collection mode must use `exec` (replaces shell); task
   collection mode must use subshells (iterates queue).

## Verification

- [ ] Script comment blocks group functions into collection and execution sections
- [ ] All exit codes match spec (0–5)
- [ ] `--dry-run` prints command(s) without executing for both collection strategies
- [ ] `--max-tasks` limits subtask iteration correctly
- [ ] Agent mode uses `exec`, task mode uses subshells
- [ ] `--tier 1` and `--tier 2` produce correct `claude` invocations
- [ ] Script passes `bash -n` syntax check
