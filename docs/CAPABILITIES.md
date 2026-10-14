# Capability matrix and limits

| Capability | Shipped status | Evidence / limit |
|---|---|---|
| Offline doctor/config checks | Supported | No network/account reads; synthetic tests |
| Configurable account aliases | Supported | 1–16 aliases; paths resolve from config location |
| Finite dry-run planning | Supported | Standard library; all dispatch disabled |
| Normalized snapshot replay | Supported | Explicit synthetic fixtures; not an auth mechanism |
| Public reset timeline | Supported, opt-in | Previously verified keyless REST GET; cache/freshness/size bounds |
| Official read-only account adapter | Implemented, version gated | Direct probe-to-planner path; protocol and normalization tested with a fake executable |
| Actual account reads in cloud Codex 0.159.2 | Previously verified in a separate environment | Official sign-ins/read methods supported; not repeated during repository packaging |
| Local 0.158.0 account startup | Environment dependent | Local schema inspected; earlier restricted runtime startup failed |
| Python platforms | Linux supported | Packaging tested on Python 3.12.3; syntax requires 3.10+; other minor versions not individually tested |
| Windows | WSL2 path only | Native Windows locking/stdio unsupported; WSL2 not independently tested here |
| macOS | Unvalidated | POSIX implementation exists, but CLI reports unsupported until validated |
| Model requests | Disabled | No portable executor or live CLI command |
| Browser Work Luna Light fast off | Earlier manual cloud success | Environment-specific; no browser adapter, unattended timer, or portable CLI dispatch provided |
| First-request timer anchoring | Unverified | Never infer from a moving reset clock |
| Cross-device active-work detection | Unverified | Always unknown for official reads; rounded zero usage cannot prove idleness |
| Purchased credit/auto reload prevention | Conservative hold | Missing authoritative fields remain unknown; no paid fallback |
| Banked-reset redemption | Unsupported | No consume endpoint allowed, no actual reset inventory saved |
| Recurring autonomous requests | Unverified, not enabled | No schedules/workflows installed |
| Cloud persistence / distributed lock | Not implemented | Local POSIX lock covers one host only |
| Chat cleanup | Not implemented | Prefer ephemeral CLI if a future supported executor exists; archive disposable browser chats as fallback; deletion requires its own confirmation |

A passed fixture test is evidence for parsing/decision behavior, not subscription
permission or account access. Profile verification flags cannot enable shipped
model dispatch. `ordinaryUsageAllowed` must be explicitly true and backend account
identity must match configuration for official metadata to enter planning. Every
reported bucket must be present and valid; missing/truncated model lists hold.
Window duration identifies weekly/short windows independently of upstream order.

A fresh active window skips a redundant OK request. Exhaustion in any bucket,
including weekly, holds. Reset announcements only prompt a fresh status read;
they never change personal clocks or authorize usage. At present official reads
cannot establish absence of cross-device work or complete spending controls, so
the planner holds hypothetical requests even if every config flag is set true.

A future executor would need separate validated no-spend controls, explicit
inactivity evidence, model availability, supported timer behavior and bounded
before/after measurement. It must preserve durable inflight/uncertain records and
must not automatically retry a timeout or delete chats to bypass confirmations.
No executor is included in this release.
