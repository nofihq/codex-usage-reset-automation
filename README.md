# Codex Usage & Reset Optimizer

Use a cloud dot to check one account, make one short `OK` request when eligible,
verify the reset, and schedule the next check. The [cloud setup](docs/CLOUD_DOT_SETUP.md)
uses a private guarded Page for state across scheduled runs. **Your laptop can be
off; no external runner, API key or extra hosting is required within an existing
eligible plan's included allowances.** Use a supported desktop browser or ChatGPT
app on your device; the execution stays in the cloud.
Routine checks reuse the saved reset time and keep the active window protected
against redundant requests, even when the tiny request still rounds to 100% remaining.
**Verified in scheduled cloud operation:** one initialization and the following
normal five-hour cycle each completed exactly one `OK`, verified the fixed reset,
archived the exact chat, and saved the next wake. See [validation](docs/VALIDATION.md)
for the tested scope.

This repository also ships a dependency-free Python **read-only planner**.
Its `would_request` result never sends a request, and changing flags cannot enable
CLI dispatch. The cloud workflow uses the dot's native tools, not a packaged
browser adapter. It does not grant extra quota or bypass subscription limits.

## Start here: one cloud account

You need existing [eligible dot access](https://learn.chatgpt.com/docs/dots#access)
and its cloud browser, private Pages and scheduling tools. **Plus alone is not
currently listed as eligible for a dot**; it can be the single monitored account
when you already have eligible dot access. Do not buy hosting or enable API billing
for this setup. Work/Codex tasks consume their normal included allowances.

1. Open **Your dot** in the ChatGPT mobile/desktop app or a desktop browser.
   Mobile web is unsupported. No Git, Python or Node installation is needed on
   your personal device for this route.
2. Give it this repository URL and the copyable instruction in
   [the cloud setup guide](docs/CLOUD_DOT_SETUP.md#start-with-one-account).
3. Sign in privately in its **cloud** browser when needed, and confirm the one
   intended identity. School MFA may need you during setup or after expiry.
4. Require the guarded Page test and a later scheduled read/write canary before
   one authorized initialization request. Then verify exact `OK`, two fixed reset
   reads at least 60 seconds apart, that chat's archive, and a later state readback.
5. Inspect the saved next cloud wake. Reuse the same task; preserve uncertain
   submissions, and use read-only backoff instead of resending.

Archiving keeps the sidebar tidy and **retains the chat's data**. The workflow
minimizes request count and requested output; total task overhead is not a verified
zero-usage or universally least-cost claim. See [validation](docs/VALIDATION.md)
and [the safety contract](docs/SAFETY_CONTRACT.md).

## Optional: offline Python planner, no login needed

Prerequisites: Git and **Python 3.10+ on Linux**. Development and clean-clone tests
run on Python 3.12.3. Windows users need WSL2 and run these commands inside Linux.
Native Windows is unsupported; macOS is not validated. Codex is optional for this
first offline setup. Python 3.10/3.11 and newer releases have not each been tested.

Open a Linux terminal (or your WSL2 terminal on Windows). Check your tools:

```bash
git --version
python3 --version
```

Python must report 3.10 or newer. If either command is missing, install Git and
Python through your Linux distribution's package manager first. On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install git python3
```

Clone the repository (currently private; repository access is required), then
copy the **single-account** template. Run each line in the same terminal:

```bash
git clone https://github.com/nofihq/codex-usage-reset-automation.git
cd codex-usage-reset-automation
cp examples/config.single-account.json config.json
python3 -m optimizer doctor --config config.json
python3 -m optimizer check --config config.json
python3 -m unittest discover -s tests -v
python3 -m optimizer dry-run --config config.json
```

Expected: doctor/check return `ok: true`, tests pass, and the dry run reports `hold`
for the `plus` alias because account status is absent. **`hold` is expected here:**
it means the program is waiting for account information. Nothing contacts an account or
the public feed by default. The tick writes bounded private state under
`~/.local/state/codex-usage-reset-automation`; doctor/check write no state.

`config.json` is your local settings file; it is ignored by Git. The `plus` alias
is just a nickname, not an email or the real account ID. All verification gates
default to false, `model_id` is unset, and `activity_policy` defaults to
`verified_inactivity`. The single-account example explicitly targets the
300-minute bucket with `trigger_window_minutes`. You can stop here for offline
planning, or continue with the optional account setup below.

Add a second account later using [the multi-account instructions](docs/ACCOUNTS.md#add-a-second-account-later).

## Optional command installation

No pip, npm, virtualenv, administrator rights, or downloads are needed:

```bash
python3 scripts/install.py --prefix "$HOME/.local"
export PATH="$HOME/.local/bin:$PATH"
codex-usage-optimizer doctor --config "$PWD/config.json"
```

The installer builds one executable Python zipapp. Python must stay installed.
The executable works outside the clone; pass an absolute config path there.
It refuses to replace an existing command unless `--replace` is explicit.
Remove that executable to uninstall. Updating source requires rerunning the installer.

## Commands

| Command | Effect |
|---|---|
| `doctor [--config FILE]` | Offline Python/platform/config readiness; no credential inspection |
| `check --config FILE` | Validate configuration; no network or runtime state writes |
| `dry-run --config FILE` | One finite tick, missing status holds |
| `dry-run --status FILE ...` | Plan from an explicit normalized snapshot; private snapshots stay local |
| `probe --config FILE --alias plus` | Explicit official read-only metadata from that alias's isolated Codex home |
| `probe ... --check-version-only` | Codex version discovery in an empty temporary home; no account reads |
| `dry-run --read-accounts ...` | Connect official metadata directly to planning; live dispatch stays disabled |
| `dry-run --read-accounts --due-only ...` | Honor persisted account-read deadlines, bounded failure backoff and change-only health alerts |
| `python3 -m optimizer.runtime [--compare-nested]` | Credential-free Linux sandbox diagnostic; no auth or model-readiness claim |
| `dry-run --fetch-feed --user-agent VALUE ...` | Opt-in keyless public tracker GET |

Every command emits JSON. Global `--json` is accepted for scripting.
Exit `0` means the command completed, including a conservative `hold`; `2` means
invalid setup/input or a failed probe. Successful read-only probes can still lack
planning readiness: inspect `status_available` and `blocker`. Invalid input emits
a scrubbed `reason`, without raw exceptions, tokens or private paths. Argument
errors go to stderr. Run `python3 -m optimizer --help` for flags.

## Replay synthetic examples

Use a **fresh private state directory** for each replay. These are simulated
identities, models, credit controls and inactivity facts, not account measurements:

```bash
demo_state=$(mktemp -d)
python3 -m optimizer dry-run --config examples/config.fixture.json --status fixtures/status-before.json --feed-fixture fixtures/timeline.json --now 2026-10-14T10:00:00Z --state-dir "$demo_state"
python3 -m optimizer dry-run --config examples/config.fixture.json --status fixtures/status-after.json --feed-fixture fixtures/timeline.json --now 2026-10-14T12:02:00Z --state-dir "$demo_state"
```

Shipped fixture configuration keeps gates false, so these commands hold safely.
Tests separately enable **simulated** gates to exercise `would_request` and retries.
A repeated feed tick suppresses duplicate hints; moving time backward returns `2`.
Snapshot input is a separate explicit testing interface; official reads do not
require hand-writing a snapshot.

## Read your own account — optional

First [install the supported CLI version](docs/CLI_SETUP.md), then follow
[the single-account sign-in guide](docs/ACCOUNTS.md). The CLI guide gives exact
commands for **0.159.2**, keeps it separate from your usual installation, and
checks the version before sign-in. Codex and Node.js/npm are needed only for
this optional account-reading step.

Once you have signed in and saved the account hash, run from the clone:

```bash
python3 -m optimizer probe --config config.json --alias plus --check-version-only
python3 -m optimizer probe --config config.json --alias plus
python3 -m optimizer dry-run --config config.json --read-accounts
python3 -m optimizer dry-run --config config.json --read-accounts --due-only
```

Expected: read-only metadata, with `live_requests_enabled: false`. A `hold` can
still be normal; use the [troubleshooting table](docs/ACCOUNTS.md#troubleshooting)
to distinguish missing setup from an intentionally conservative decision.

The optimizer never reads credential files itself, copies logins, or accesses
session history. Official Codex owns its selected auth store and may perform its
normal internal auth/runtime work. The adapter sends `refreshToken:false` and
`explicitGatewayOauth:true`, stopping if the server asks the client to perform
an unsupported authentication action. Account hashes are sensitive local metadata;
keep them and private output out of Git.

`expected_account_id_hash` must match the hash of the backend usage account.
Confirm the correct browser identity during sign-in before recording this hash;
a hash alone does not tell you whose account was selected. Unknown identity or
`ordinaryUsageAllowed` holds. Windows are keyed by **duration**, not by whether
upstream calls them `primary` or `secondary`.

Zero usage can be rounded; 100% remaining does not prove inactivity. No reliable
cross-device active-work indicator was verified. The official adapter keeps that
activity unknown. The default `verified_inactivity` policy holds without verified
inactivity; the opt-in `remaining_percent_heuristic` instead requires the exact
target bucket to report 100% remaining. Other buckets may be partially used, but
none may be exhausted, and explicit active work always holds. Purchased credits
must be proven zero and auto reload off; missing fields remain unknown.

A candidate also needs a persisted, verified fixed reset for the **same target
bucket**, observed unchanged in two distinct reads, and that reset must expire
before another attempt is considered. Idle API clocks drifting with `now + 5h`
are not anchors. The supplied Plus target is 300 minutes; the Pro target is 10080
minutes. Fresh target timers skip redundant requests. See the full
[activity, timer, request, and cleanup contract](docs/SAFETY_CONTRACT.md).
The [heuristic example](examples/config.heuristic.json) is opt-in and keeps all
live-request gates disabled; no scheduler or dispatcher is activated.

The October 14–15 cloud tests verified scheduled initialization and the following
normal cycle. Each completed one exact `OK`, confirmed a fixed five-hour reset in
reads at least 60 seconds apart, and archived its exact chat. The normal cycle
reused the guarded private Page, kept initialization consumed, and rearmed the
same saved task. See [the evidence and limits](docs/VALIDATION.md).
No browser adapter or live CLI dispatch is shipped in the Python package.

## Public reset hints and cloud options

The independent [tracker](https://codex-reset.com/) can suggest a personal status
refresh, never prove a personal refill or credit inventory:

```bash
python3 -m optimizer dry-run --config config.json --fetch-feed --user-agent 'CodexUsageOptimizer/0.2 (+https://example.invalid/project)'
```

Replace the example contact URL with your project's URL. Requests are bounded,
reject redirects/stale data, honor caching/Retry-After, and retain only structured
hints. Initial ingestion establishes a baseline. Polling defaults to four hours.

**Public-feed polling is not an immediate reset alert.** For direct notifications,
the [source site documents browser push, Telegram, Discord and email alerts](https://codex-reset.com/developers).
Receiving a site alert does not automatically wake this workflow's dot. The
source's MCP server was tested as read-only, without event-subscription support;
no automatic site-alert-to-dot connection is shipped or verified here. A normal
scheduled cycle is verified separately from global-event triggering. See
[validation](docs/VALIDATION.md#global-reset-notifications).

[Cloud dot setup](docs/CLOUD_DOT_SETUP.md) is the cloud route. Its saved task uses
the dot's environment and a private Page, so a personal device need not stay on.
It requires existing eligible access rather than a guaranteed free standalone
hosting service. The repository installs no schedules or GitHub workflows by
itself. [Optional read-only scheduling](docs/DEPLOYMENT.md) covers the Python
planner. Nested CLI model execution remains blocked on the examined cloud host;
see [the diagnosis](docs/CLI_SETUP.md#nested-cloud-sandbox-blocker).

## Keep usage and storage small

The shipped dry run sends no model requests. Its intended disposable request asks
for exactly `OK`, with no tools or other work; that limits output but is not a
verified least-cost model ranking or a promise of zero usage. Do not send repeated
requests to establish a timer when the evidence is missing. Honor `next_check_at`
and retain only the small state needed to prevent duplicate work.

Local optimizer state and logs are bounded as described below. Cloud Page state
is separate; retain only current receipts and unresolved outcomes, and keep its
private references out of Git. Service-side version history is not covered by
the local file bounds. Codex's own caches
and browser/server-side chats are separate and are not covered by those bounds.
Only a completed, identified disposable chat may be archived in an authorized
workflow. Archiving retains the chat; it does not delete it or prove disk space
was freed. The cloud recipe verifies archive-only cleanup; the Python cleanup
adapter remains disabled. Permanent deletion is never unattended.

## Privacy, storage, and contributions

Local `config.json`, runtime directories, snapshots, auth files and captures are
ignored. State uses a user-owned private directory and rejects symlinks and unsafe
permissions. State is capped at 128 KiB, logs at four 64 KiB files, with retention
and one-host locking. Multiple cloud hosts require an unimplemented distributed
lock/state adapter. Changing aliases while reusing state holds for reconciliation.
Do not delete uncertain request records to force retries.

See [security guidance](SECURITY.md), [contribution steps](CONTRIBUTING.md), and
[verification evidence](docs/VALIDATION.md). All test inputs are synthetic. No
open-source license has been selected; the owner must approve one before an
open-source release. The repository is currently private.
