
---

# TASKS.md

```md
# TASKS.md

## How to use this plan

This file defines the implementation order for the project. The project must be implemented **incrementally and test first**.

For every step:

1. implement the tests for the step first
2. implement the functionality required by the step
3. run all relevant tests and linters
4. update docs and ADRs if needed
5. mark the step done only when it is **Ready for Review**

### Ready for Review checklist

A step is Ready for Review only when:

- [ ] tests for the step exist and pass
- [ ] full test suite passes
- [ ] linters/formatters pass
- [ ] docs are updated
- [ ] ADR updated if a non-trivial decision was made
- [ ] no TODOs for shipped behavior

### Status markers

Use these markers consistently:

- `[ ]` not started
- `[-]` in progress
- `[x]` done

Only one step should normally be `[-]` at a time.

---

## Phase 0 — Repository foundation

### Step 0.1 [x] — Initialize repository structure and tooling
**Goal:** create the initial project skeleton, packaging, test runner, lint/format tooling, and documentation scaffolding.

**Tests first**
- Add a smoke test proving the test suite is wired correctly
- Add a package import smoke test for `measurement_inspector`

**Implementation**
- Create package skeleton matching AGENTS.md
- Add `pyproject.toml`
- Add test configuration
- Add lint/format configuration
- Add `README.md` with local dev instructions
- Add `docs/adr/README.md` explaining ADR conventions
- Add initial empty modules/files needed for the package structure

**Documentation**
- README: setup, test, lint, format commands
- ADR: only if a non-trivial tooling decision is made beyond standard defaults

**Ready for Review when**
- Repository installs cleanly on Python 3.11+
- `pytest` runs
- lint/format commands run
- package imports successfully

---

## Phase 1 — Core domain contracts

### Step 1.1 [x] — Define core config and record schemas
**Goal:** define the minimal typed contracts for config and normalized raw message records.

**Tests first**
- Tests for config defaults and validation
- Tests for normalized raw record construction
- Tests for required/optional fields and timestamp typing expectations

**Implementation**
- Implement `config/schema.py`
- Implement `config/defaults.py`
- Implement `io/record_models.py`

**Scope**
- Introduce:
  - analysis config object
  - normalized raw message record model
- Keep implementation light and explicit
- Do not implement eCAL reading yet

**Documentation**
- Document the config object and raw record shape in README or module docs
- ADR if choosing between dataclass vs pydantic is a non-trivial decision

**Ready for Review when**
- Schemas are stable and tested
- No runtime behavior beyond schema/model validation is missing

---

### Step 1.2 [x] — Define adapter protocol and synthetic fixture helpers
**Goal:** define the measurement adapter contract and create synthetic record fixtures for tests.

**Tests first**
- Tests that a fake adapter can satisfy the protocol behavior used by downstream code
- Tests for synthetic fixture builders producing valid normalized records

**Implementation**
- Implement adapter protocol in `io/ecal_reader.py`
- Add test fixture helpers for building synthetic streams/messages
- Add minimal fake adapter used in tests

**Scope**
- No real eCAL integration yet
- Focus on interfaces and test support

**Documentation**
- Document adapter contract
- ADR only if interface shape changes meaningfully from AGENTS.md

**Ready for Review when**
- Downstream steps can depend on stable fake adapters and fixtures

---

## Phase 2 — Canonical base table

### Step 2.1 [x] — Build canonical base table from normalized records
**Goal:** convert normalized records into the canonical observed-message base table.

**Tests first**
- Single-stream base table creation
- Multi-stream combined table creation
- Stable sorting behavior by default analysis order
- Observed-message-only semantics
- Required columns exist with correct dtypes where practical

**Implementation**
- Implement `model/base_table.py`
- Support one combined dataframe keyed by `stream_id`
- Preserve raw fields exactly
- Prepare derived columns as nullable/uncomputed where appropriate

**Scope**
- No counter inference yet beyond placeholders needed for schema
- No anomaly logic yet

**Documentation**
- Document base-table semantics clearly:
  - one row per observed message
  - no synthetic missing-message rows

**ADR**
- Required if any schema semantics differ from AGENTS.md

**Ready for Review when**
- Base table contract is stable and tested
- Observed-message semantics are explicit and enforced

---

### Step 2.2 [x] — Compute basic timing-derived columns
**Goal:** compute latency and timestamp-delta columns.

**Tests first**
- `latency_s = recv_ts - send_ts`
- `send_dt_s` per stream
- `recv_dt_s` per stream
- non-monotonic timestamp flag behavior
- correct handling of first-row nulls per stream

**Implementation**
- Implement timing derivations in `model/derived_metrics.py`
- Add flags:
  - `is_send_time_nonmonotonic`
  - `is_recv_time_nonmonotonic`
- Keep calculations per stream

**Scope**
- Only timing columns and related flags
- No expected-period error yet unless needed for clean design

**Documentation**
- Document timestamp derivative semantics and first-row null rules

**Ready for Review when**
- Timing metrics are correct on synthetic datasets
- Edge cases are covered by tests

---

## Phase 3 — Counter logic and inferred loss

### Step 3.1 — Implement counter delta and gap inference
**Goal:** implement stream-local counter delta computation and inferred loss counts.

**Tests first**
- no-loss sequence
- single-loss sequence
- multi-loss sequence
- duplicate counter behavior
- backward-jump behavior
- configurable modulus/wrap behavior
- first-row null/empty semantics

**Implementation**
- Implement `model/counter_logic.py`
- Compute:
  - `counter_delta`
  - optional `counter_delta_raw`
  - optional `counter_delta_norm`
  - `lost_msgs`
  - `is_gap`
  - `is_counter_nonmonotonic`
- Support config-driven wrap semantics

**Scope**
- Must remain debuggable and deterministic
- Reorder/duplicate behavior should at least be flagged, not hidden

**Documentation**
- Document inference rules and assumptions
- ADR required if behavior for duplicates/backward jumps is a design choice not obvious from AGENTS.md

**Ready for Review when**
- Counter logic matches tests for all core scenarios
- Ambiguous behavior is documented

---

### Step 3.2 — Build loss-event table
**Goal:** build a separate inferred loss-event table from the base table.

**Tests first**
- no gaps yields empty event table
- single and multiple gap events
- correct carry-over of prev/curr timestamps and counters
- correct derived receive/send gap values

**Implementation**
- Extend `model/summaries.py` or add helper module for loss-event extraction
- Create one row per inferred gap event

**Scope**
- Loss events only
- No anomaly event table yet

**Documentation**
- Document distinction between observed-message base table and inferred loss-event table

**Ready for Review when**
- Loss-event table is correct and clearly separated from base-table semantics

---

## Phase 4 — Expected period, rate, and throughput metrics

### Step 4.1 — Implement send/receive rates and period errors
**Goal:** derive frequency and period error metrics from delta columns and config.

**Tests first**
- constant-rate stream
- expected-rate error near zero for ideal stream
- sender irregularity reflected in send metrics
- receiver irregularity reflected in receive metrics
- null behavior where expected period/frequency is not configured

**Implementation**
- Extend `model/derived_metrics.py`
- Compute:
  - `send_freq_hz`
  - `recv_freq_hz`
  - `send_period_error_s`
  - `recv_period_error_s`

**Scope**
- Use explicit config semantics
- Avoid hidden assumptions when expected period is absent

**Documentation**
- Document precedence of `expected_freq_hz` vs `expected_period_s`
- ADR required if precedence is a design choice

**Ready for Review when**
- Rate and period error semantics are stable and tested

---

### Step 4.2 — Implement bitrate and latency-diff metrics
**Goal:** add throughput and latency-change diagnostics.

**Tests first**
- bitrate from `size_bytes` and dt columns
- latency difference computation
- null/edge behavior for first rows and zero/negative intervals

**Implementation**
- Extend `model/derived_metrics.py`
- Compute:
  - `send_bitrate_bps`
  - `recv_bitrate_bps`
  - `latency_diff_s`

**Scope**
- Keep division-by-zero handling explicit and tested

**Documentation**
- Document bitrate semantics and edge-case handling

**Ready for Review when**
- Throughput and latency-change diagnostics are stable and deterministic

---

## Phase 5 — Summary tables

### Step 5.1 — Implement stream summary table
**Goal:** compute one-row-per-stream aggregate summaries.

**Tests first**
- stream counts and durations
- total loss and gap counts
- latency quantiles
- period means/std
- size summary metrics
- single-stream and multi-stream cases

**Implementation**
- Implement stream summary in `model/summaries.py`

**Scope**
- Include fields from AGENTS.md that are already supported by implemented metrics
- If a summary column depends on not-yet-built metrics, defer that column until the prerequisite step is complete

**Documentation**
- Document included columns and how they are computed

**Ready for Review when**
- Summary columns are correct and documented
- Unsupported columns are not faked

---

### Step 5.2 — Implement time-bucket summary table
**Goal:** compute per-stream, per-time-bucket aggregates.

**Tests first**
- bucketing by receiver time
- bucket boundaries
- msg count aggregation
- loss aggregation
- latency aggregation
- anomaly count placeholder behavior if anomaly system not yet present

**Implementation**
- Implement bucket summaries in `model/summaries.py`
- Default to `recv_ts` buckets

**Scope**
- Use configurable bucket size
- Keep behavior explicit at boundaries

**Documentation**
- Document bucket alignment rules
- ADR if bucket alignment strategy is non-trivial

**Ready for Review when**
- Bucket logic is deterministic and tested
- Boundary behavior is documented

---

## Phase 6 — Anomaly logic

### Step 6.1 — Implement anomaly flags on base table
**Goal:** derive row-level anomaly flags from config thresholds.

**Tests first**
- latency anomaly flag
- send period anomaly flag
- receive period anomaly flag
- no false positives for nominal data
- null-safe behavior

**Implementation**
- Implement `model/anomalies.py`
- Set:
  - `is_latency_anomaly`
  - `is_send_period_anomaly`
  - `is_recv_period_anomaly`

**Scope**
- Only threshold-based flags
- No scoring model

**Documentation**
- Document threshold semantics

**Ready for Review when**
- Flags are correct and test-covered

---

### Step 6.2 — Implement anomaly-event table
**Goal:** generate one-row-per-anomaly event table.

**Tests first**
- one row per flagged anomaly
- correct anomaly types
- correct value/threshold capture
- multiple anomaly types in same stream

**Implementation**
- Add anomaly-event extraction to `model/anomalies.py` or `model/summaries.py`

**Scope**
- Severity may be simple and rule-based
- Keep output explicit and documented

**Documentation**
- Document anomaly-event schema

**Ready for Review when**
- Event extraction is complete for implemented anomaly types

---

## Phase 7 — CLI and pipeline orchestration

### Step 7.1 — Implement local analysis pipeline orchestration
**Goal:** create an internal pipeline that runs adapter → base table → derived metrics → summaries.

**Tests first**
- end-to-end pipeline test using fake adapter
- topic filter behavior
- stream filter behavior
- deterministic output shapes for synthetic datasets

**Implementation**
- Implement orchestration in `app.py` and/or service helpers
- Return an analysis result object containing produced tables

**Scope**
- No UI yet
- No real eCAL integration yet
- Must work entirely with fake adapter in tests

**Documentation**
- Document pipeline entry points and returned artifacts

**Ready for Review when**
- Synthetic end-to-end pipeline works without UI

---

### Step 7.2 — Implement CLI entrypoint
**Goal:** add the first usable CLI for running analysis on a measurement path.

**Tests first**
- CLI argument parsing
- expected config mapping
- basic invocation path
- help text smoke test

**Implementation**
- Implement `cli.py`
- Add console summary output
- Wire CLI args into config and pipeline

**Scope**
- It is acceptable at this step for the CLI to stop after analysis summary instead of starting UI
- Start small and stable

**Documentation**
- README usage examples
- CLI options documented

**ADR**
- Required if selecting a CLI framework is a non-trivial decision

**Ready for Review when**
- CLI is usable and documented
- Help output is stable

---

## Phase 8 — Real eCAL integration

### Step 8.1 — Implement real eCAL HDF adapter
**Goal:** connect the adapter contract to the real eCAL measurement API.

**Tests first**
- adapter contract tests using either mocks or a tiny controlled fixture if available
- normalization tests for stream listing and message iteration
- graceful error behavior when measurement path is invalid or eCAL support is unavailable

**Implementation**
- Implement `io/ecal_reader.py` real adapter
- Isolate all eCAL-specific logic here
- Add decoder helpers if needed
- eCAL python package is available as eclipse-ecal >= 6.1
- Use import ecal, and use ecal.measurement implementation, not native h5py.

**Scope**
- Keep fallback behavior explicit if the dependency is optional
- Do not leak eCAL details into the model/UI layers

**Documentation**
- Document required eCAL runtime/dependency expectations
- ADR required if integration constraints force a notable design choice

**Ready for Review when**
- Real adapter satisfies the established contract
- Error handling is explicit and documented

---

## Phase 9 — First local UI

### Step 9.1 — Build overview page
**Goal:** create the first local Panel overview page backed by computed tables.

**Tests first**
- view-model/helper tests for filtering and displayed KPI data
- smoke test that overview layout can be created from an analysis result

**Implementation**
- Implement `views/overview.py`
- Add:
  - KPI cards
  - stream summary table
  - top-loss/top-latency plots
- Create local Panel layout

**Scope**
- Keep UI logic thin by testing helper functions separately
- Use placeholder/simple charts before advanced linked brushing

**Documentation**
- README instructions for launching the local app

**Ready for Review when**
- Overview page renders locally from analysis results
- Core displayed values are test-backed

---

### Step 9.2 — Build stream detail page with linked time filtering
**Goal:** add stream drill-down with shared x-axis time views and event inspection.

**Tests first**
- view-model selection/filter tests
- helper tests for stream-specific subsets
- smoke test for detail layout creation

**Implementation**
- Implement `views/stream_detail.py`
- Add charts for:
  - latency over time
  - receive period over time
  - send period over time
  - counter gap markers
  - size over time
- Add event table integration

**Scope**
- Linked time filtering must work at the state/helper level
- Full linked brushing can be phased in as the plotting stack matures

**Documentation**
- Document drill-down workflow

**Ready for Review when**
- Single-stream inspection works locally and predictably

---

## Phase 10 — Specialized diagnostics views

### Step 10.1 — Build loss analysis view
**Goal:** provide dedicated diagnostics for inferred losses.

**Tests first**
- helper tests for largest-loss selection
- histogram source preparation tests
- filtering tests by stream/time selection

**Implementation**
- Implement `views/loss.py`
- Add:
  - gap event markers
  - loss histograms
  - largest-gap table

**Documentation**
- Document how inferred loss should be interpreted

**Ready for Review when**
- Loss diagnostics are driven from tested event-table helpers

---

### Step 10.2 — Build timing/frequency and latency views
**Goal:** provide dedicated views for timing diagnosis and latency analysis.

**Tests first**
- helper tests for chart/table inputs
- ECDF/histogram source preparation
- sender-vs-receiver diagnostic subset logic

**Implementation**
- Implement:
  - `views/frequency.py`
  - `views/latency.py`

**Documentation**
- Document interpretation patterns:
  - sender-side issue
  - downstream/receiver issue

**Ready for Review when**
- Dedicated views work off tested helper logic and analysis tables

---

## Phase 11 — State and interactions

### Step 11.1 — Implement shared selection state
**Goal:** create explicit shared state objects for selected streams, time range, anomaly types, and bucket size.

**Tests first**
- state transitions
- filter composition behavior
- serialization or reproducibility expectations if relevant

**Implementation**
- Implement `state/selection.py`
- Implement `state/filters.py`

**Scope**
- Keep state explicit and testable
- UI should consume this state rather than embedding hidden selection logic

**Documentation**
- Document state model and filtering rules

**Ready for Review when**
- Shared state is stable, testable, and used by views

---

## Phase 12 — Performance and caching

### Step 12.1 — Add Parquet cache support
**Goal:** cache transformed analysis tables for faster reload.

**Tests first**
- cache write/read round-trip
- cache invalidation key behavior
- graceful behavior when cache is disabled

**Implementation**
- Implement `util/cache.py`
- Add optional pipeline integration

**Scope**
- Cache format should be explicit and documented
- Do not silently serve stale cache

**Documentation**
- Document cache behavior and limitations
- ADR required if cache-key strategy is non-trivial

**Ready for Review when**
- Cache behavior is deterministic and documented

---

### Step 12.2 — Add scalable plotting strategy
**Goal:** support raw vs resampled/datashaded rendering based on selection size.

**Tests first**
- helper logic deciding render mode by row count
- stable thresholds/config behavior

**Implementation**
- Add plotting helper logic and integrate into views
- Introduce Datashader/hvPlot resampling where needed

**Scope**
- Keep threshold-based behavior explicit
- Test the mode-selection logic even if plot rendering itself is smoke-tested

**Documentation**
- Document rendering thresholds

**Ready for Review when**
- Large selections degrade gracefully without changing analysis correctness

---

## Phase 13 — Export and polish

### Step 13.1 — Export selected subsets
**Goal:** export selected rows or selected regions to CSV/Parquet.

**Tests first**
- export helper tests
- selected-subset export behavior
- stable column ordering where relevant

**Implementation**
- Add export helpers and optional UI/CLI hooks

**Documentation**
- Document export behavior and file formats

**Ready for Review when**
- Exports are deterministic and documented

---

### Step 13.2 — Final polish and hardening
**Goal:** make the product commit-ready as a coherent first release candidate.

**Tests first**
- add missing regression tests found during polishing
- full smoke test on main user flows

**Implementation**
- tighten docs
- remove dead code
- clean naming inconsistencies
- ensure final command paths work

**Documentation**
- finalize README
- ensure ADR set is complete
- ensure AGENTS.md and TASKS.md reflect actual implementation state

**Ready for Review when**
- main workflow is coherent end-to-end
- documentation matches reality
- repository is clean for handoff

---

## Execution rules for the agent

For every step:

1. Change the step status from `[ ]` to `[-]`
2. Write the tests for the step first
3. Implement only the functionality needed for the step
4. Run tests and lint/format checks
5. Update docs and ADRs if needed
6. Change the step status to `[x]` only when the step is fully Ready for Review

### Required step completion note

At the end of each completed step, record a concise note in the commit message or step log including:

- what was implemented
- what tests were added
- what commands were run
- whether an ADR was added/updated

### If blocked

If a step cannot be completed without changing the plan:

- do not silently broaden scope
- do not leave partial hidden behavior
- document the blocker
- update AGENTS.md / TASKS.md only if the design truly changed
- add/update an ADR if the change is non-trivial

---