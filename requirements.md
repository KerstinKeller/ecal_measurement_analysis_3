Primary requirements
Functional requirements

The system must:

ingest one measurement at a time from an eCAL HDF source

normalize records into a canonical schema

preserve both sender and receiver timestamps

compute message-level timing and counter-derived metrics

infer message loss from monotonic/wrap-aware counters

compute stream-level and bucket-level summaries

expose loss-event and anomaly-event tables

provide a local UI with overview + stream drill-down + event tables

scale reasonably for large time-series using resampling / datashading

Quality requirements

Every increment must be Ready for Review:

all tests pass

all linters pass

output is stable and documented

ADR updated if a non-trivial design decision was made

no TODOs for shipped behavior

TODOs are allowed only for future work

future work TODOs must be clearly marked and tracked

Delivery model

This project is implemented by an AI coding agent working incrementally from TASKS.md. The agent must always:

take the next open step

follow test-driven development

keep changes scoped to that step

update documentation and ADRs when required

stop only when the step is fully Ready for Review

Technical stack
Required stack

Python 3.11+

pandas

numpy

Panel

HoloViews

hvPlot

Tabulator via Panel

pytest

Optional / planned packages

Use when the corresponding task calls for them:

pyarrow for Parquet caching

typer for CLI

dataclasses or pydantic for config/schema objects

stdlib logging or loguru

datashader / hvPlot resampling for large timelines

Tooling expectations

The repository should include and enforce:

tests via pytest

lint/format tooling

stable dependency management

reproducible local developer workflow

Preferred tooling unless repository conventions already define otherwise:

pytest

ruff

black or ruff format

optional mypy later if introduced intentionally

Do not add tool sprawl without reason.

Architectural principles

The implementation must follow a layered architecture with strong separation of concerns.

Layer A — Measurement adapter

Responsibility:

interact with the eCAL HDF measurement API

list streams

iterate/read messages

normalize raw measurement data into a project-internal raw record shape

Rules:

only this layer should depend on the exact eCAL HDF API details

binary payload parsing belongs here or in a helper used here

dashboard/UI code must not know measurement API details

Layer B — Canonical transform

Responsibility:

convert normalized raw records into canonical base tables

preserve observed-message semantics

sort and organize records per stream as required for analysis

Rules:

base table contains only observed messages

missing messages must not be synthesized into fake base-table rows

inferred loss should be represented separately in a loss-event table

Layer C — Summary engine

Responsibility:

compute stream-level summaries

compute time-bucket summaries

compute event tables

Layer D — View model / selection engine

Responsibility:

represent selected streams, topic filters, time windows, anomaly filters, and current drill-down state

map shared UI state into filtered subsets

Layer E — UI

Responsibility:

local Panel app only

overview page

stream detail views

event tables

linked filtering behavior

Package structure

The intended package structure is:

measurement_inspector/
  cli.py
  app.py

  config/
    defaults.py
    schema.py

  io/
    ecal_reader.py
    record_models.py

  model/
    base_table.py
    derived_metrics.py
    counter_logic.py
    summaries.py
    anomalies.py

  views/
    overview.py
    stream_detail.py
    latency.py
    loss.py
    frequency.py
    tables.py
    widgets.py

  state/
    selection.py
    filters.py

  util/
    time.py
    logging.py
    cache.py

  tests/
    test_counter_logic.py
    test_derived_metrics.py
    test_summaries.py

The actual repository may add small support modules, but must preserve this separation of concerns.

Canonical data model
Normalized raw message record

Each raw message record produced by the adapter must normalize to:

stream_id

topic

send_ts

recv_ts

counter

size_bytes

This is the minimal normalized ingestion contract.

Canonical base table

The canonical base table contains one row per observed message.

Required columns:

Identity

stream_id

topic

Raw fields

send_ts

recv_ts

counter

size_bytes

Core derived fields

latency_s

send_dt_s

recv_dt_s

counter_delta

lost_msgs

is_gap

Frequency / period

send_freq_hz

recv_freq_hz

send_period_error_s

recv_period_error_s

Throughput

send_bitrate_bps

recv_bitrate_bps

Stability diagnostics

latency_diff_s

is_counter_nonmonotonic

is_send_time_nonmonotonic

is_recv_time_nonmonotonic

Optional anomaly flags

is_latency_anomaly

is_send_period_anomaly

is_recv_period_anomaly

Semantic rules

base table = observed messages only

inferred losses belong in a separate loss-event table

sender and receiver timestamps must both be preserved

receiver time is the default UI time axis unless explicitly overridden

Counter semantics

Counter handling must be configurable.

Required config fields

counter_bits

counter_wrap

counter_modulus (optional explicit override)

duplicate_policy

reorder_policy

Required behavior

For each stream:

sort by recv_ts for observer-view analysis unless a specific task says otherwise

compute counter deltas relative to the previous observed row

if wrap-aware, normalize using modulus arithmetic

infer lost_msgs = max(delta - 1, 0) only for monotonic forward motion

detect and flag:

duplicates

backward jumps

ambiguous jumps

Debuggability rule

Preserve both when useful:

counter_delta_raw

counter_delta_norm

This is especially important for debugging wrap/reorder behavior.

Timestamp strategy

Both timestamps are required.

Default analysis axis

Use recv_ts as the default x-axis in the UI because it reflects what the observer actually saw.

Interpretation guidance

The system must allow users to distinguish:

sender irregularity

downstream / network / receiver irregularity

Examples:

large send_dt_s with normal latency suggests sender-side issue

stable send_dt_s with large recv_dt_s or latency spikes suggests downstream issue

Required summary outputs

At minimum the project must support the following tables.

1. Stream summary table

One row per stream.

Suggested columns:

stream_id

topic

msg_count

first_recv_ts

last_recv_ts

duration_s

total_lost_msgs

gap_count

loss_rate_est

latency_p50_s

latency_p95_s

latency_p99_s

max_latency_s

mean_send_period_s

mean_recv_period_s

send_period_std_s

recv_period_std_s

max_recv_period_error_s

size_mean_bytes

size_p95_bytes

2. Time-bucket summary table

One row per stream and time bucket.

Suggested columns:

bucket_start

stream_id

msg_count

lost_msgs_sum

latency_mean_s

latency_p95_s

recv_period_mean_s

recv_period_std_s

bitrate_sum_bps

anomaly_count

3. Loss-event table

One row per inferred loss event.

Suggested columns:

stream_id

topic

prev_recv_ts

curr_recv_ts

prev_counter

curr_counter

lost_msgs

recv_gap_s

send_gap_s

latency_before_s

latency_after_s

4. Anomaly-event table

One row per anomaly event.

Suggested columns:

stream_id

topic

recv_ts

anomaly_type

severity

value

threshold

row_index

Required views

The first complete product should provide the following conceptual views.

Measurement overview

Purpose:

immediate triage

Includes:

KPI cards

stream summary table

top-loss streams

top-latency streams

stream vs time-bucket anomaly density heatmap

Stream detail overview

Purpose:

inspect one stream deeply

Includes:

arrival density / rate over time

latency over time

counter gap markers

size over time

receive period error over time

send period error over time

Loss analysis

Purpose:

inspect inferred loss behavior

Includes:

gap event markers

histogram of lost_msgs

histogram of receive gaps

table of largest gap events

Timing / frequency view

Purpose:

distinguish sender-side vs downstream issues

Includes:

send_dt_s

recv_dt_s

send_period_error_s

recv_period_error_s

Latency view

Purpose:

inspect absolute delay and variability

Includes:

latency timeline

histogram

ECDF or percentile view

latency change timeline

Event table / raw inspection

Purpose:

inspect exact rows behind a selected region

UI behavior principles

The UI must support shared filtering state.

Shared selections include:

selected streams

selected topics

selected time range

selected anomaly types

selected bucket size

selected rows / brushed regions

Expected cross-filter behavior:

selecting a stream filters all plots

selecting a time region filters tables

anomaly filters toggle markers and event subsets

changing bucket size updates aggregates and heatmaps

Performance principles

The system should be designed for scale from the beginning, but without premature complexity.

Data handling

read stream-by-stream where possible

convert timestamps once

use categorical dtype for low-cardinality string fields where beneficial

support Parquet cache files when the relevant step is implemented

Visualization

aggregated views first

raw point rendering only for manageable selections

large selections should use resampling or datashading

Suggested thresholds

under ~200k selected rows: raw interactive plots are acceptable

above that: use datashaded/resampled rendering

CLI expectations

The eventual CLI shape is:

measure-inspect /path/to/meas \
  --topic "camera/*" \
  --stream-id 42 \
  --counter-bits 16 \
  --expected-rate-hz 100 \
  --cache \
  --port 0

Expected option set over time:

measurement path

--topic

--stream-id

--counter-bits

--counter-wrap/--no-counter-wrap

--expected-rate-hz

--expected-period-ms

--cache

--cache-dir

--open-browser/--no-open-browser

--port

Do not add all options at once unless TASKS.md explicitly requires them in that increment.

Adapter contract

Hide eCAL API details behind a narrow adapter contract.

Example target shape:

class MeasurementAdapter(Protocol):
    def list_streams(self, measurement_path: str) -> pd.DataFrame: ...
    def iter_messages(
        self,
        measurement_path: str,
        stream_ids: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> Iterable[dict]: ...

Rules:

keep the contract narrow

normalize all raw rows before they enter modeling code

binary decoding belongs in the adapter or a decoder helper

if multiple payload types exist, use a simple decoder registry rather than leaking protocol knowledge into the rest of the codebase

Configuration model

A single config object should be passed through the analysis pipeline.

Suggested fields:

counter_bits

counter_wrap

expected_period_s

expected_freq_hz

latency_warn_s

period_error_warn_s

bucket_size_s

max_raw_points_before_rasterize

default_time_axis

Config must remain simple, explicit, and easy to test.

Testing strategy

This project is test driven.

Absolute rule

For every increment:

add or update tests first

verify tests fail for the missing behavior where practical

implement the behavior

make tests pass

run lint/format/type checks required by the repository

update docs/ADR if needed

Most important tests

Priority is correctness of metrics, not UI snapshot coverage.

Counter logic tests

no loss

single loss

multi-loss

wraparound

duplicate

backward jump

Derived timing tests

constant frequency

latency spike

stable send cadence with receive jitter

sender irregularity with stable latency

Summary tests

quantiles

bucketed aggregates

loss-event generation

Golden tests

Use small synthetic datasets for:

perfect stream

periodic drops

wraparound stream

latency burst stream

send-rate drift stream

Documentation expectations

The repository should contain and maintain:

README.md

AGENTS.md

TASKS.md

docs/adr/ for architecture decision records

ADR rule

An ADR must be added or updated if a step introduces a non-trivial decision, such as:

changing canonical schema semantics

changing counter inference rules

choosing CLI framework

choosing cache format

choosing state-management approach in the UI

Keep ADRs concise and append-only in spirit.

Coding rules for the agent

The agent implementing this project must follow these rules.

Scope discipline

only work on the next open step from TASKS.md

do not opportunistically add unrelated features

do not refactor broadly unless required to complete the current step

Test-first discipline

write tests before implementation

avoid skipping tests for core logic

UI logic should still be driven by testable view/model helpers where possible

Stability discipline

no placeholder behavior for shipped functionality

no hidden partial implementations

no TODOs for behavior claimed complete

Documentation discipline

update README/docs when user-visible behavior changes

update ADR for non-trivial design decisions

ensure examples match actual CLI/API behavior

Quality discipline

A step is not done until:

tests pass

linters pass

docs are updated

ADR is updated if needed

the increment is commit-ready

Definition of Ready for Review

This applies to every increment:

All tests pass

All linters pass

Output stable and documented

ADR updated if any non-trivial decision was made

No TODOs for shipped behavior

allowed only for future work

clearly marked and tracked

Increment execution contract

When working a TASKS.md step, the agent must produce:

test changes

implementation changes

documentation changes

ADR change if needed

a concise Ready-for-Review summary including:

what was added

what tests were added/updated

what commands were run

whether an ADR was added/updated

If the step cannot be completed without violating this contract, the agent must say so explicitly and stop rather than ship a partial hidden state.