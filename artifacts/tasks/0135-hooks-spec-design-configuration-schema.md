---
kind: task
name: 0135-hooks-spec-design-configuration-schema
type: spec
status: ready
assignee: architect
owner: user
parent: "[[0134-task-lifecycle-hooks]]"
created: 2026-03-14
---

# Hooks Spec — Design Configuration Schema And Execution Model

## Requirements

1. Design the hook configuration schema (settings file location, JSON structure, fields per hook entry)
2. Define the matcher format for status transitions (e.g., glob/regex on `old→new`, wildcard support like `*→done`)
3. Specify the environment variables passed to hook commands (task name, old status, new status, file path)
4. Define execution semantics: ordering, synchronous execution, failure behavior (abort transition), timeout handling
5. Document CLI integration points — where in `openstation status` the hook engine is invoked
6. Produce a spec artifact in `artifacts/specs/`

## Verification

- [ ] Spec artifact exists in `artifacts/specs/`
- [ ] Configuration schema is fully defined with examples
- [ ] Matcher format supports common patterns (specific transitions, wildcards, catch-all)
- [ ] Environment variable contract is documented
- [ ] Failure and timeout semantics are specified
- [ ] CLI integration points are identified
