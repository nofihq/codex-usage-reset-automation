# Activity, reset evidence, and cleanup contract

This is the planning and fixture-testable request contract. The shipped CLI still
has **no live dispatcher or browser adapter**. Changing profile flags does not
enable a model request. Synthetic evidence must never be substituted for account
measurements.

## Choose the activity policy explicitly

`activity_policy` belongs to each profile:

- `verified_inactivity` is the default. It requires verified inactivity and an
  explicit `active_work: false`; rounded remaining percentages are insufficient.
- `remaining_percent_heuristic` is opt-in. It allows the exact target bucket's
  **100% remaining** (`used_percent: 0`) to stand in for unavailable inactivity
  evidence. Other complete, valid buckets may be partially used, but no bucket
  may be exhausted. `active_work: true` always holds.

The heuristic does **not** prove that another device, tab, or session is idle.
Reported percentages can be rounded, and status can race with work started after
it was read. Opting in accepts that limited proxy; it does not turn unknown
identity, permission, spending controls, or usage into safe values.

Set `trigger_window_minutes` explicitly for the bucket being monitored. The
provided Plus profile targets `300` (five hours); the Pro profile targets `10080`
(one week). These are configuration choices, not universal subscription promises.
Observed duration must match the configured target and verified bucket coverage;
upstream `primary`/`secondary` ordering and the plan's display name are not bucket
identity. Missing or ambiguous targets hold. Expected bucket coverage must be
nonempty and include the target; the five-hour heuristic also requires the weekly
bucket, even when only the five-hour bucket must be 100% remaining.

A profile fragment for deliberately opting into the heuristic is:

```json
{
  "activity_policy": "remaining_percent_heuristic",
  "trigger_window_minutes": 300
}
```

See [the disabled heuristic example](../examples/config.heuristic.json), or add
those keys to the relevant profile in a private config, preserving its other fields. Use `10080` only for a verified weekly target. Keep the default policy
unless you intend to accept the heuristic's limitations. Neither choice relaxes
model, authentication, usage-impact, reset-behavior, or no-paid-fallback gates.

## Establish a fixed timer before considering an expiration

1. Read fresh, verified status for the same account and exact target bucket.
2. Obtain a second, distinct later status read with the **same future reset
   timestamp**, same target identity and duration. The minimum interval is
   `fixed_reset_min_read_gap_seconds` (default 60 seconds). Replaying one snapshot
   twice is not independent evidence.
3. Persist the verified fixed-reset anchor in private durable state. A single
   observation, a public reset announcement, or a reset value that drifts with
   each read is insufficient.
4. Wait until that exact recorded reset has expired, including the safety margin,
   then obtain fresh complete status before planning an attempt.

Some idle API observations move their reset to approximately `now + 5 hours` on
each read. That moving estimate is not a fixed window and cannot establish an
anchor, justify a trigger, or prove a successful request. An unrelated bucket's
expired timer cannot authorize a request for the target bucket. A future fixed
target timer means wait; an empty account with no anchor does not bootstrap one
by sending a request. Missing state means hold, not permission to start over.

## Gates that always apply

Hold when any required fact is missing, invalid, stale, or from the future.
Account identity must match, ordinary subscription usage must be explicitly
allowed, the selected model must be available, purchased credits must be proven
zero, and auto reload must be proven off. Nonzero credits, auto reload on, explicit
active work, exhaustion in any bucket, or an unresolved earlier request all hold.
The only activity exception is the explicitly selected remaining-percent proxy
above. Public feed text never authorizes usage or redemption.

## Request and verification boundary

A future supported executor must preserve this transaction contract:

- Save an atomic **before-send inflight marker** before calling the model. If that
  write fails, do not send. Deduplicate durably for the account and exact window
  across ticks and restarts; use one host and the same private state directory.
  Recheck the real clock after saving and before sending; an expired decision
  must be refreshed. A changed expected account identity cannot reuse old state.
- Send only the disposable exact-`OK` request using a verified included-usage
  model. No tools, follow-up task, paid fallback, or automatic credit redemption.
- A reported request success is insufficient. Require a completed response whose
  entire result is exactly `OK`, plus two distinct post-request reads showing the
  same fixed target reset near the request time plus the target duration, within
  `reset_tolerance_seconds` (default 180 seconds). The reads must be at least the
  configured minimum interval apart and preserve identity, freshness, complete
  buckets, and spending gates.
- Missing completion, extra response text, a moving/mismatched timer, timeout,
  crash, or ambiguous usage is uncertain: retain the durable record and hold for
  manual reconciliation. Never retry an uncertain request automatically.
- Only a positively established no-usage failure can qualify for the single
  bounded retry. Do not erase attempts, rename aliases, or discard state to create
  another opportunity. Without upstream idempotency, exactly-once execution
  cannot be guaranteed.

The implemented transaction checks are tested with fake adapters. They are not
production executor validation or permission to activate an unattended schedule.

## Minimal usage and retention

An exact-`OK` response limits requested output; it does not establish the cheapest
model or guarantee zero usage. Reuse verified timers instead of sending redundant
requests. Keep metadata checks bounded, honor `next_check_at`, and avoid retaining
raw transcripts, screenshots, account inventories, or response payloads in logs.

For an authorized browser workflow, cleanup may archive **only the exact completed
disposable chat** after verifying it contains no unrelated work. Verify that the
archive succeeded; an uncertain target or incomplete request holds cleanup.
Pending or uncertain cleanup also holds another request, preserving the exact
chat record until it is reconciled. An uncertain archive is checked read-only on
later calls, never automatically repeated. The
repository supplies only a disabled, fixture-testable cleanup boundary; there is
no working browser cleanup implementation. Never delete a useful session
or autonomously perform permanent deletion. **Archiving is retention, not deletion**
and does not prove storage was reclaimed. This project has no zero-retention mode.
