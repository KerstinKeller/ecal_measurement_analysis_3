# ADR 0001: Counter wrap normalization uses a half-modulus threshold

## Status
Accepted

## Context
Step 3.1 introduces counter delta and inferred loss logic. When wrap handling is enabled,
negative raw deltas can mean either:

- true wrap-around (forward monotonic motion across the modulus boundary), or
- non-monotonic behavior (duplicate/reorder/backward jump).

Treating every negative delta as wrap can hide real reorder/backward behavior.

## Decision
When `counter_wrap=True`, normalize a negative raw delta as wrap only when
`abs(raw_delta) > modulus / 2`.

- `modulus` comes from `counter_modulus` when configured, otherwise `2 ** counter_bits`.
- Large negative jumps are interpreted as wrap-forward increments (`raw_delta + modulus`).
- Small negative jumps remain negative and are flagged as `is_counter_nonmonotonic=True`.
- Duplicates (`delta == 0`) are also flagged non-monotonic.

## Consequences
- Wrap scenarios such as `255 -> 2` with 8-bit counters are inferred as forward motion.
- Backward/reorder scenarios such as `15 -> 13` with 16-bit counters remain explicitly visible.
- Behavior is deterministic and test-covered for no-loss, loss, duplicate, backward-jump,
  wrap-enabled, and wrap-disabled cases.
