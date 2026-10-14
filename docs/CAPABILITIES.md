# Capability matrix and limits

| Capability | Shipped status | Evidence / limit |
|---|---|---|
| Offline doctor/config checks | Supported | No network/account reads; synthetic tests |
| Configurable account aliases | Supported | 1–16 aliases; paths resolve from config location |
| Finite dry-run planning | Supported | Standard library; all CLI dispatch disabled |
| Normalized snapshot replay | Supported | Explicit synthetic fixtures; not an auth mechanism |
| Public reset timeline | Supported, opt-in | Previously verified keyless REST GET; cache/freshness/size bounds |
| Official read-only account adapter | Implemented, version gated | Direct probe-to-planner path; fake-executable protocol tests |
| Actual 0.159.2 account reads | Previously verified on a separate cloud host | Does not validate every host or model execution |
| Local 0.158.0 account startup | Environment dependent | Schema inspected; earlier restricted startup failed |
| Python platforms | Linux supported | Earlier packaging on 3.12.3; syntax requires 3.10+; not every minor version tested |
| Windows / macOS | WSL2 route / macOS unvalidated | Native Windows locking/stdio unsupported; WSL2 not independently tested |
| Default activity policy | `verified_inactivity` | Unknown activity holds; rounded zero usage is insufficient |
| Remaining-percent activity heuristic | Explicit opt-in, planner only | Target must have 100% remaining; other buckets may be partially used; no exhausted bucket or explicit active work |
| Target-window reset evidence | Conservative fixed-anchor contract | Two distinct reads must agree on the same future reset; only that target's expired anchor can trigger |
| Cross-device inactivity | Not proven by the heuristic | Official activity remains unknown; percentages can be rounded or race with new work |
| Purchased credits / auto reload | Conservative hold | Must prove zero credits and reload off; no paid fallback |
| Model requests | CLI disabled | No portable executor or live command |
| Nested cloud CLI model execution | Blocked on examined host | Fixed daemon root is masked by outer sandbox; stable 0.162.1 has the same check |
| Browser Work Luna Light, fast off | Narrow manual verification on October 14 | One completed exact-`OK` request, two matching fixed five-hour reset reads, archive verified |
| Post-request success checks | Fixture-testable contract | Completed exact `OK` plus two matching fixed-timer reads near request + duration |
| Banked-reset redemption | Unsupported | No consume endpoint allowed; no real reset inventory committed |
| Later unattended sessions / recurring requests | Pending, not enabled by repository | Manual success is insufficient; no schedules/workflows installed |
| Cloud persistence / distributed lock | Not implemented | Local POSIX lock covers one host only |
| Chat cleanup | Disabled, fixture-testable boundary | Exact completed disposable chat may be archived in an authorized workflow; archive retains data; no autonomous permanent deletion |

A fixture pass is evidence for parsing and decision behavior, not subscription
permission, account access, model cost, or production readiness. Profile flags
cannot enable shipped dispatch. `ordinaryUsageAllowed` must be true, backend
account identity must match configuration, all buckets must be complete and valid,
and model-list truncation holds. Duration identifies the configured target; neither
`primary`/`secondary` order nor a plan label establishes its identity.

The default policy still requires verified inactivity. Opting into the heuristic
changes only that activity gate: it does not relax freshness, identity, credit,
model, explicit-active-work, or fixed-anchor requirements. Empty state or a moving
reset estimate cannot create an opportunity. Public hints only request a personal
status refresh. For the full behavior, see [the safety contract](SAFETY_CONTRACT.md).

Any future executor needs separate supported no-spend/authentication controls,
account-specific model and timer validation, durable account/window deduplication,
and a persisted before-send marker. An exact response without the two required
post-request timer observations is uncertain. Crashes/timeouts remain held for
manual reconciliation, never automatic retry. Nothing here guarantees exactly-once
model execution or installs a live executor.
