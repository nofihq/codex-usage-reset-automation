# Read-only reset planner

Run `python3 cli/reset_plan.py` in the same pinned checkout as the
[status reader](CLOUD_TOOLS.md). Pass one JSON object on stdin and read one JSON
result. The planner does not read files, authenticate, contact the network, write
state, schedule work, notify or send a prompt. Use redacted reader results and
selected ledger fields, never credentials, email bodies or Page IDs. It returns
`state: planned` or a redacted hold with exit code 2.

| Operation | Inputs besides `operation` | Result |
| --- | --- | --- |
| `route_wake` | `now`, `intended_at` for this occurrence; `delivery`: intended/recurrence/unknown; `mode`: ordinary/reminder/recovery/state; `ledger`: fresh/temporary_error/unavailable; Boolean `has_hold` | Maximum account scope and `check_saved_reminders` for the bound coordinator. Pass actual native provenance; guessed provenance is unknown. |
| `observe` | `result`: status reader JSON; `target`: 300 or 10080 | Account window, remaining percent, and whether the numeric/backend usage gate passes. Browser/spending/claims still apply. |
| `verify_active_window` | `first`, `second`: fresh reader JSON for the same bound account; `target`: 300 or 10080 | Fixed reset and read-only deadline when two reads at least 60 seconds apart agree and the later read shows usage in that window. |
| `verify_window` | `first`, `second`: reader JSON; `target`, `sent_at`, `completed_at` | Fixed reset and ordinary deadline, if two reads at least 60 seconds apart agree and fit the actual send/reply interval. |
| `verify_browser_window` | `first`, `second`: exact Usage label observations below; `target`; optional paired `sent_at`, `completed_at` | The same fixed reset check using the signed-in Usage page. Without send/reply times, this can establish a read-only deadline for an active window. |
| `plan_public_notice` | `kind`: subscription/forecast/global/banked_announcement/banked; `message_id`: native Gmail message ID; `event_id`: stable source ID or null; Booleans `authenticated` and `native`; `receipts`: map of prior keys to claimed/accepted/unknown; optional `legacy_keys`: exact receipt keys for the same notice | Public notice claim keys, duplicate, or hold. Does not parse or authenticate mail or authorize account work. |
| `plan_reminders` | `now`, `normal_due_at`, saved `inventory`: the `rateLimitResetCredits` object or null; `receipts`: map of stage keys to claimed/accepted/unknown/suppressed; optional future `retry_at` | Due notices, receipt keys needing reconciliation, incomplete inventory flag, and earliest future wake. Call per account. |

Times use integer Unix seconds. For send/reply bounds use the observed UTC
seconds (round send down, completion up only if the first read is later; use
consistent whole-second bounds). Reader `checkedAt` retains its ISO timestamp.
Do not use the host's local time to infer expiry.

Use `verify_active_window` when the account has already started the window
through normal use. Its result can anchor a read-only wake on the existing timer.
Keep the send claim and eligibility checks in the controller.

For `verify_browser_window`, each observation contains the bound account match
as `identityMatchesExpected: true`, `source: "usage_exact_reset_label"`, the
matched row's `windowDurationMins` and `remainingPercent`, the exact label's
`resetsAt` in Unix seconds, and `checkedAt` as the capture time in ISO format with
a time zone. Read the countdown's ordinary visible tooltip or its browser-provided
title in **Settings → Usage**. Bind it to the right row and require an absolute
date, seconds, and time zone. A rounded countdown is insufficient. Verify the
account and fresh render both times. Timing evidence does not establish backend
ordinary-usage permission or affect a saved claim or hold.

A verified fallback can check saved reminders while account work stays held.
`check_saved_reminders` permits checking due times only. Sending a notice still
requires ownership of the existing receipt key, guarded readback and normal review.

For a public notice, use the same guarded edit to claim all returned keys and
then record one outcome under those keys. Never use a guessed event ID. Without
one, deduplication is by exact native message ID. Hashes identify receipt keys;
they do not authenticate the source. Account handoff has its own guarded state.

During migration, supply `legacy_keys` only when both handlers claim the same
notice through those keys in the same guarded Page. Claim and finalize all
returned keys together. Keep claimed, accepted and unknown legacy receipts and
leave account handoffs held until their own bindings are verified.

Use `banked_announcement` for a heads-up before a banked grant is reported
available and `banked` for the landing report. Use the same stable rollout ID
when the source supplies one. Preserve legacy banked keys and exact message
receipts. When an older receipt's stage is ambiguous, reconcile it against the
original message before processing another report for that rollout.

Receipt keys are `expiry:grant:ordinal:stage` within a single account. Ordinals
preserve multiplicity for indistinguishable grants; they are not service IDs.
Persist stage keys across refreshes. Never map an owner-reported redemption to
one of multiple indistinguishable grants. If a same-timestamp grant group changes
and the identity of a prior warning or redemption becomes unclear, reconcile
the group before scheduling another notice. Claimed or unknown sends hold that
grant's later stages until reconciled. If the available count is smaller than
the listed available grants, reconcile the inventory before setting warnings.
Do not put an overdue timestamp back into
the scheduler; process any due work allowed for the current wake first.

During setup verify the exact helper source alongside the reader. If the cloud
working files disappear, restore the pinned public code and check it before use.
A successful planner run is not evidence of a native schedule, notification
delivery, account refill or submission.
