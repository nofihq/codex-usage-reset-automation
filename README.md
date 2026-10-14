# Codex Usage & Reset Optimizer

Monitor Codex usage windows, recognize public reset hints, and plan the next useful
status check. This small Python project ships **dry-run planning and opt-in
read-only account metadata**, with free tooling and no third-party dependencies.
It does not grant extra quota or bypass subscription limits.

**Current stage:** a portable monitoring scaffold, not clone-and-forget autonomous
inference. There is no live dispatch command, automatic reset redemption, paid
fallback, or installed scheduler. `would_request` is a synthetic planning result;
it never sends a model request. See the [capability matrix](docs/CAPABILITIES.md).

## Start in five minutes — no account login needed

Prerequisites: Git and **Python 3.10+ on Linux**. Development and clean-clone tests
run on Python 3.12.3. Windows users need WSL2 and run these commands inside Linux.
Native Windows is unsupported; macOS is not validated. Codex is optional for this
first offline setup. Python 3.10/3.11 and newer releases have not each been tested.

Clone the repository (currently private; repository access is required):

```bash
git clone https://github.com/nofihq/codex-usage-reset-automation.git
cd codex-usage-reset-automation
cp examples/config.example.json config.json
python3 -m optimizer doctor --config config.json
python3 -m optimizer check --config config.json
python3 -m unittest discover -s tests -v
python3 -m optimizer dry-run --config config.json
```

Expected: doctor/check return `ok: true`, tests pass, and the dry run reports `hold`
for both aliases because account status is absent. Nothing contacts an account or
the public feed by default. The tick writes bounded private state under
`~/.local/state/codex-usage-reset-automation`; doctor/check write no state.

For one account, copy `examples/config.single-account.json` instead. For more,
add profiles with distinct `account_id` aliases and distinct `codex_home` values
(up to 16). `account_id` is a local nickname, not an email or the real account ID.
All verification gates default to false, and `model_id` is unset.

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

Install the official Codex CLI using its [official installation instructions](https://learn.chatgpt.com/docs/cli).
The adapter accepts reviewed versions **0.158.0 and 0.159.2** and rejects other
versions until their protocol is reviewed. Version 0.159.2 read methods were
verified in a separate cloud environment; local 0.158.0 schema was inspected but
account startup was blocked by runtime restrictions. A newer version is not
assumed compatible merely because it installs.

Follow [per-account sign-in](docs/ACCOUNTS.md), then:

```bash
python3 -m optimizer probe --config config.json --alias plus --check-version-only
python3 -m optimizer probe --config config.json --alias plus
python3 -m optimizer dry-run --config config.json --read-accounts
```

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
cross-device active-work indicator was verified. The official adapter always keeps
activity unknown and cannot produce an allowed live request. Purchased credits
must be proven zero and auto reload off before any hypothetical future dispatch;
missing fields remain unknown. A fresh active window skips redundant requests;
an exhausted weekly bucket holds. First-use timer anchoring remains unverified.

## Public reset hints and cloud options

The independent [tracker](https://codex-reset.com/) can suggest a personal status
refresh, never prove a personal refill or credit inventory:

```bash
python3 -m optimizer dry-run --config config.json --fetch-feed --user-agent 'CodexUsageOptimizer/0.2 (+https://example.invalid/project)'
```

Replace the example contact URL with your project's URL. Requests are bounded,
reject redirects/stale data, honor caching/Retry-After, and retain only structured
hints. Initial ingestion establishes a baseline. Polling defaults to four hours.

[Optional scheduling and free cloud setup options](docs/DEPLOYMENT_DRAFT.md)
describes an externally managed single-host tick. No timers or GitHub workflows
are shipped or activated. Free hosting depends on provider/account eligibility;
there is no guaranteed free always-on cloud service here. Never import subscription
credentials into GitHub Actions. Browser Work execution is environment-specific
and is not included as a portable dispatcher.

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
