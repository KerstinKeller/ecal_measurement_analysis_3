You are implementing this repository incrementally.

Your job is to take the **next open step** from `TASKS.md` and complete it in a **test-first** way while following `AGENTS.md`.

## What you must do

1. Read `AGENTS.md` and `TASKS.md`.
2. Identify the **next open step** in `TASKS.md`.
   - If a step is marked `[-]`, continue that step.
   - Otherwise take the first step marked `[ ]`.
3. Restate the selected step briefly, including:
   - its goal
   - the required test-first scope
   - any documentation / ADR obligations
4. Implement the step **tests first**.
5. Implement the production code needed to satisfy the step.
6. Run the relevant quality gates.
7. Update documentation and ADRs if required.
8. Bring the increment to **Ready for Review**.

## Non-negotiable development rules

- Work only on the selected step.
- Do not implement future steps early.
- Do not leave TODOs for shipped behavior.
- Do not hide partial implementations behind placeholders unless the step explicitly allows it and tests/documentation make that behavior explicit.
- Keep the design aligned with `AGENTS.md`.
- Prefer small, explicit, testable code.

## Definition of Ready for Review

A step is only complete when all of the following are true:

- All tests pass
- All linters pass
- Output stable and documented
- ADR updated if any non-trivial decision was made
- No TODOs for shipped behavior
  - allowed only for future work
  - clearly marked and tracked

## Required execution order

Follow this order exactly:

### 1. Analyze the step
Summarize:
- selected TASKS.md step
- files likely to change
- risks or design choices
- whether an ADR is likely needed

### 2. Write tests first
Add or update tests for the step before implementing behavior.

Also explain briefly:
- what behaviors the tests cover
- why these tests define completion for the step

### 3. Implement the behavior
Make the minimum production changes needed for the tests to pass.

### 4. Run quality gates
Run the repository’s relevant checks, at minimum:
- tests
- linters
- formatters if applicable

Include the exact commands you ran.

### 5. Update docs and ADRs
Update:
- README or module docs if user/developer-visible behavior changed
- ADR if a non-trivial design decision was made

### 6. Report Ready-for-Review status
Provide a concise summary with:
- what was implemented
- tests added/updated
- docs updated
- ADR added/updated or “not needed”
- commands run
- confirmation that the step is Ready for Review

## Output format

Use this structure in your response:

1. **Selected step**
2. **Test-first plan**
3. **Changes made**
4. **Quality gates run**
5. **Docs / ADR updates**
6. **Ready for Review summary**

## Additional guidance

- If the repository state does not match `TASKS.md`, explain the mismatch and make the smallest justified correction.
- If blocked by a non-trivial design issue, do not guess silently:
  - make the smallest sound decision
  - document it
  - add/update an ADR if warranted
- If a change to `AGENTS.md` or `TASKS.md` is necessary, keep it minimal and justify it explicitly.

Your objective is not just to write code. Your objective is to complete exactly one increment so it can be committed immediately.