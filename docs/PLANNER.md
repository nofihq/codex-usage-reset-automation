# Read-only reset planner

Run `python3 cli/reset_plan.py` in the same pinned checkout as the
[status reader](CLOUD_TOOLS.md). Pass one JSON object on stdin and read one JSON
result. The planner does not read files, authenticate, contact the network, write
state, schedule work, notify or send a prompt. Use redacted reader results and
selected ledger fields, never credentials, email bodies or Page IDs. It returns
`state: planned` or a redacted hold with exit code 2.

| Operation | Inputs besides `operation` | Result |
| --- | --- | --- |
| `route_wake` | `now`, `intended_at`; `delivery`: intended/recurrence/unknown; `mode`: ordinary/reminder/recovery/state; `ledger`: fresh/temporary_error/unavailable; Boolean `has_hold` | Maximum scope for this wake. Pass actual native provenance; guessed provenance is unknown. |
| `observe` | `result`: status reader JSON; `target`: 300 or 10080 | Account window, remaining percent, and whether the numeric/backend usage gate passes. Browser/spending/claims still apply. |
| `verify_window` | `first`, `second`: reader JSON; `target`, `sent_at`, `completed_at` | Fixed reset and ordinary deadline, if two reads at least 60 seconds apart agree and fit the actual send/reply interval. |
| `plan_public_notice` | `kind`: subscription/forecast/global/banked; `message_id`: native Gmail message ID; `event_id`: stable source ID or null; Booleans `authenticated` and `native`; `receipts`: map of prior keys to claimed/accepted/unknown | Public notice claim keys, duplicate, or hold. Does not parse or authenticate mail or authorize account work. |
| `plan_reminders` | `now`, `normal_due_at`, saved `inventory`: the `rateLimitResetCredits` object or null; `receipts`: map of stage keys to claimed/accepted/unknown/suppressed; optional future `retry_at` | Due notices, receipt keys needing reconciliation, incomplete inventory flag, and earliest future wake. Call per account. |

Times use integer Unix seconds. For send/reply bounds use the observed UTC
seconds (round send down, completion up only if the first read is later; use
consistent whole-second bounds). Reader `checkedAt` retains its ISO timestamp.
Do not use the host's local time to infer expiry.

For a public notice, use the same guarded edit to claim all returned keys and
then record one outcome under those keys. Never use a guessed event ID. Without
one, deduplication is by exact native message ID. Hashes identify receipt keys;
they do not authenticate the source. Account handoff has its own guarded state.

Receipt keys are `expiry:grant:ordinal:stage` within a single account. Ordinals
preserve multiplicity for indistinguishable grants; they are not service IDs.
Persist stage keys across refreshes. Never map an owner-reported redemption to
one of multiple indistinguishable grants. If a same-timestamp grant group changes
and the identity of a prior warning or redemption becomes unclear, reconcile
the group before scheduling another notice. Claimed or unknown sends hold that
grant's later stages until reconciled. Do not put an overdue timestamp back into
the scheduler; process any due work allowed for the current wake first.

During setup verify the exact helper source alongside the reader. If the cloud
working files disappear, restore the pinned public code and check it before use.
A successful planner run is not evidence of a native schedule, notification
delivery, account refill or submission.
