# Capability matrix and limits

| Capability | Shipped status | Evidence / limit |
|---|---|---|
| Cloud dot setup recipe | Single-account native-tool workflow | Existing eligible dot access required; no local device execution or extra hosting |
| Client OS independence | Cloud route through supported apps/desktop web | No native Python requirement on the user's device; mobile web unsupported |
| Offline doctor/config checks | Supported | No network/account reads; synthetic tests |
| Configurable account aliases | Supported | 1–16 aliases; paths resolve from config location |
| Finite dry-run planning | Supported | Standard library; all CLI dispatch disabled |
| Persisted metadata cadence | Opt-in `--read-accounts --due-only` | Real process-restart skip test; bounded failure backoff; change-only health alerts |
| First offline alias to account binding | Supported before observed/operational state | Identity provenance retained; established/ambiguous account changes hold |
| Normalized snapshot replay | Supported | Explicit synthetic fixtures; not an auth mechanism |
| Public reset timeline | Supported, opt-in | Previously verified keyless REST GET; cache/freshness/size bounds |
| Official read-only account adapter | Implemented, version gated | Direct probe-to-planner path; fake-executable protocol tests |
| Actual 0.159.2 account reads | Previously verified on a separate cloud host | Does not validate every host or model execution |
| Local 0.158.0 account startup | Environment dependent | Schema inspected; earlier restricted startup failed |
| Python platforms | Linux supported | Earlier packaging on 3.12.3; syntax requires 3.10+; not every minor version tested |
| Native Python on Windows / macOS | WSL2 route / macOS unvalidated | Separate from the OS-independent cloud recipe; no native-runtime validation claimed |
| Default activity policy | `verified_inactivity` | Unknown activity holds; rounded zero usage is insufficient |
| Remaining-percent activity heuristic | Explicit opt-in | Target must have 100% remaining; other buckets may be partially used; no exhausted bucket or explicit active work |
| Target-window reset evidence | Conservative fixed-anchor contract | Two distinct reads must agree on the same future reset; only that target's expired anchor can trigger |
| Cross-device inactivity | Not proven by the heuristic | Official activity remains unknown; percentages can be rounded or race with new work |
| Purchased credits / auto reload | Conservative hold | Must prove zero credits and reload off; no paid fallback |
| Model requests | CLI disabled | No portable executor or live command |
| Nested cloud CLI model execution | Blocked on examined host | Fixed daemon root is masked by outer sandbox; stable 0.162.1 has the same check |
| Linux runtime diagnostic | Credential-free, bounded | Empty home; version/sandbox tests only; no auth/model-readiness guarantee |
| Browser Work Luna Light, fast off | Narrow manual verification on October 14 | One completed exact-`OK` request, two matching fixed five-hour reset reads, archive verified |
| Post-request success checks | Fixture-testable contract | Completed exact `OK` plus two matching fixed-timer reads near request + duration |
| Banked-reset redemption | Unsupported | No consume endpoint allowed; no real reset inventory committed |
| Scheduled cloud recovery request | Observed on October 14 | One completed exact OK; two fixed 300-minute reset reads 76.24 seconds apart; exact archive |
| Guarded cloud Page state | Native-tool recipe, not Python transport | Single-block hash test and later scheduled read/write; no forced-restart or months-long guarantee |
| Routine next-window recurrence | Same-task normal-due rearming saved/read back | Subsequent cycles remain unobserved; cloning the repo installs no job |
| Distributed multi-executor dispatch | Unsupported | Python lock covers one host; cloud recipe designates one sender; no fleet validation |
| Chat cleanup | CLI boundary disabled; cloud archive observed | Only the exact completed disposable chat; archive retains data; no unattended permanent deletion |

A fixture pass is evidence for parsing and decision behavior, not subscription
permission, account access, model cost, or production readiness. Profile flags
cannot enable shipped dispatch. `ordinaryUsageAllowed` must be true, backend
account identity must match configuration, all buckets must be complete and valid,
and model-list truncation holds. Duration identifies the configured target; neither
`primary`/`secondary` order nor a plan label establishes its identity.

The default policy still requires verified inactivity. Opting into the heuristic
changes only that activity gate: it does not relax freshness, identity, credit,
model, explicit-active-work, or routine fixed-anchor requirements. Empty state or a moving
reset estimate cannot create an automatic opportunity. The cloud recipe's explicit
single-use initialization is separate. Public hints only request a personal
status refresh. For the full behavior, see [the safety contract](SAFETY_CONTRACT.md).

Any future executor needs separate supported no-spend/authentication controls,
account-specific model and timer validation, durable account/window deduplication,
and a persisted before-send marker. The cloud recipe supplies native-tool instructions,
not a bundled browser executor. An exact response without the two required
post-request timer observations is uncertain. Crashes/timeouts remain held for
manual reconciliation, never automatic retry. Nothing here guarantees exactly-once
model execution or installs a live executor.
