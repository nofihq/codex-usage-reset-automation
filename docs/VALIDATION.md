# Validation evidence

Verified October 15, 2026. The cloud dot recipe passed scheduled initialization,
later durable-state checks, and the following normal five-hour cycle. The Python
package is a separate read-only planner; it ships no browser executor or live
model command.

## Scheduled cloud operation

The single-account workflow used the dot's cloud browser, one private Page with
a guarded canonical JSON block, and one saved cloud task. No connected personal
computer, external runner, API-key billing or additional hosting was used.

| Check | Scheduled initialization | Following normal cycle |
|---|---|---|
| Date, America/New_York | October 14 | October 15 |
| Request | One exact `OK` completed | One exact `OK` completed |
| Model/settings | GPT-6 Luna, Light, fast off; no requested tools/files/project | Same |
| Spending gates | Included allowance available, zero credits, reload off | Same; intended Plus identity confirmed fresh |
| Durable reservation | Guarded Page write and matching readback before send | New window marker; exact readback 56.41 seconds before send |
| Fixed reset | Same 300-minute target in two reads 76.24 seconds apart | Same target/reset in two reads 69.98 seconds apart |
| Window timing | Implied start within send-to-observed-completion interval | Same |
| Cleanup | Exact completed disposable chat archived and verified | Same |
| Next wake | Same saved task, verified reset plus two minutes | Same; enabled schedule update confirmed by task-owning controller |
| Duplicate protection | Initialization permit consumed | Permit stayed consumed; one new per-window attempt, no automatic retry |

The normal check was saved for 2:37:23 a.m. Eastern. Its preflight observations
began at 2:38:44 a.m.; it sent at 2:41:25 a.m. and observed completed `OK` at
2:42:10 a.m. Cloud wakes and browser work are not exact-time execution guarantees.
The two reset reads were at 2:42:12 and 2:43:22 a.m.; both identified a fixed
7:41:42 a.m. reset. Exact archive verification completed at 2:44:07 a.m.
The same enabled task was saved for 7:43:42 a.m., two minutes after that reset.
These timestamps describe the completed verification, not a permanently current
schedule or a claim that the later wake has already run.

A fresh audit at 4:31 a.m. Eastern read the canonical Page and confirmed the normal
result, matching reservation proof, consumed initialization permit, reset pair,
archive evidence and next schedule receipt. It sent no new model request.
The saved scheduler receipt records that the schedule-owning controller handled
the delegated worker's update restriction. A worker's proposed next time alone
would not have counted as a successful rearm.

## Durable-state and failure checks

- Correct-hash single-block replacements applied and read back exactly.
- An isolated synthetic Page test used only the expected block hash: a stale
  writer received `edit_conflict`, the winning content stayed unchanged, and the
  same candidate applied after refreshing the expected hash. No sequence guard
  was claimed when the editing read did not return one.
- A separate scheduled wake read, guardedly updated and read back the same Page.
  Later scheduled read-only checks preserved the completed result, consumed permit,
  original before-send proof and cleanup record without another model request.
- An earlier scheduled attempt held without sending when local receipt files
  were missing. The authoritative ledger was moved to the private Page. The exact
  filesystem-loss cause and missing historical raw receipts remain unproven;
  old history is explicitly labeled rather than reconstructed as raw evidence.
- The initialization audit detected an omitted readback timestamp. The original
  retained tool result supplied matching hash/revision/time, 18.24 seconds before
  send; a later scheduled check verified the corrected provenance. The normal
  cycle persisted its fresh readback proof directly.

## Global reset notifications

The normal Plus cycle above verified timer-driven operation. It did not verify
an immediate public-reset trigger or delivery of a phone/desktop push alert.
An operational audit found a public-feed schedule with an overnight gap; it must
not be described as an immediate notification service. Shortening polling does
not establish event-driven delivery.

The source [documents direct browser push, Telegram, Discord and email alerts](https://codex-reset.com/developers).
Those are notifications to their subscribers, not proof that a dot wakes. The
source also states that ingestion can lag; exact-minute delivery is not promised.

On October 15, a credential-free metadata test of the source's documented MCP
endpoint returned protocol `2025-06-18` and only `tools` capabilities. Both
`server/discover` and `events/list` returned JSON-RPC `-32601` method-not-found.
These tests sent no model requests and created no subscription. The source's
private POST/push routes are explicitly outside its public API contract.

OpenAI [supports dot triggers through MCP Events](https://developers.openai.com/plugins/build/mcp-events),
which requires source-side MCP 2.0 event discovery, subscriptions and signed
webhook delivery. That source support was absent in the endpoint tested here.
No source-alert-to-dot bridge or device-push delivery is claimed as verified.
An event, if received through a supported route, would still require fresh
account-specific verification and must never authorize another request in an
active verified window or repeat an uncertain submission.

## Repository verification

The suite passes **106 tests on Linux with Python 3.12.3**, covering planning,
protocol handling, fixed resets, uncertain requests, persisted metadata cadence,
process-restart probe skipping, bounded runtime diagnostics, first-account binding
and privacy scanning. Native Windows/macOS Python and other minor versions were
not validated by these runs.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/privacy_check.py
python3 scripts/verify_clean_clone.py
gitleaks git --redact --no-banner .
```

The clean-clone verifier exercises the committed source: config copy, doctor/check,
dry-run, synthetic replay, privacy scan and an installed zipapp outside the clone.
These checks send no account/model requests. The tracked-source scan and redacted
Git-history scan found no credentials; scanners cannot prove absence of every
possible secret. Real identities, Page references, chat URLs and private receipts
are excluded from the repository.

## Optional CLI verification

The isolated official `@openai/codex@0.159.2` installation and version-only probe
were smoke-tested. The installation used Node.js 24.15.0/npm 12.0.2; other Node
versions were not individually tested. Official account, rate-limit and model
reads were previously verified on the separate cloud host.

The credential-free runtime diagnostic was exercised with official 0.159.2 and
0.162.1 in empty private homes. Direct local Linux sandbox smoke passed; nested
execution failed with the daemon-directory category. The examined dot host's tool
process was already nested, and both checks failed there. Version 0.162.1 is
diagnostic-only, outside the account-adapter allowlist. These diagnostics made no
account/model requests and introduced no sandbox bypass.

See [CLI setup](CLI_SETUP.md#nested-cloud-sandbox-blocker). The experimental
app-server environment option remains execution-disabled because startup warm-up
quota behavior was not verified. It is not needed for the tested cloud route.

## Scope

Existing eligible dot access, private Pages, scheduling and a cloud browser are
required. Plus alone is not currently listed as dot-eligible. A supported app or
desktop browser can control the cloud workflow without local Python/Node or an
always-on personal device. Cloning the repo creates no job: authorize setup,
sign in privately and inspect the saved result.

The observed autonomous recurrence passed. This does not establish months of
uninterrupted operation, forced fresh-container recovery, every account/OS timer
behavior, universally cheapest model choice, zero usage or exactly-once execution
under every failure. Archive keeps chats out of Recents while retaining their
data. Routine checks still require expired verified anchors, fresh identity and
spending gates, durable deduplication and reconciliation of uncertain outcomes.
See [setup](CLOUD_DOT_SETUP.md), [capabilities](CAPABILITIES.md) and the
[safety contract](SAFETY_CONTRACT.md).
