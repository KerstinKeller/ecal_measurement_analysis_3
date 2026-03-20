# ADR 0002: Expected frequency takes precedence over expected period

- Date: 2026-03-20
- Status: Accepted

## Context

Step 4.1 introduces period-error metrics derived from configured expected timing.
`AnalysisConfig` supports both `expected_freq_hz` and `expected_period_s`.
When both are provided, the implementation must choose deterministic precedence.

## Decision

Use the following precedence when deriving period-error metrics:

1. If `expected_freq_hz` is configured, compute expected period as `1 / expected_freq_hz`.
2. Otherwise, if `expected_period_s` is configured, use `expected_period_s` directly.
3. Otherwise, leave period-error columns null.

## Consequences

- The behavior is deterministic and testable when both fields are present.
- Frequency-based configuration is treated as the canonical source when available.
- Existing callers can provide only one field without ambiguity.
