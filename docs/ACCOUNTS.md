# Sign in to one account

Offline commands do not need Codex or authentication. These optional steps read
**your own** subscription metadata. Start with the single-account `config.json`
from the README and [install the pinned CLI](CLI_SETUP.md) first. Run the commands
from the repository folder, in the terminal where you selected that CLI.

The example uses the nickname `plus`. You only need one account. Its credentials
stay in a separate Codex home, which is a folder where the official CLI stores
that account's login. Do not copy your existing login or select your usual
`.codex` home.

## 1. Start official sign-in for your alias

The single-account template already chooses a separate account home. The helper
creates that folder with private permissions (POSIX mode or native Windows ACL),
checks the reviewed CLI version, and launches the official interactive login.
It never reads/copies credentials, sends a model request, or edits dot schedules.

On Linux/macOS/WSL2:

```bash
python3 scripts/account_login.py --config config.json --alias plus
```

On native Windows (PowerShell):

```powershell
py -3 scripts/account_login.py --config config.json --alias plus
```

You run this helper explicitly; it does not perform unattended authentication.
Use a new, empty account folder for this first setup. Existing shared permissions
are rejected, not silently repaired.

Complete the browser sign-in and confirm that it is the account you want to
monitor. If the browser selected a different account, change the browser identity
during sign-in. Use ChatGPT sign-in; do not paste API keys or access tokens.

If you are on a host that cannot open a browser, use the
[device-code alternative](#sign-in-on-a-headless-host) instead of this command.

## 2. Read the account hash

On Windows use `py -3` instead of `python3` in the following commands.

```bash
python3 -m optimizer probe --config config.json --alias plus
```

Expected: `limits_read` and `models_read` are `"completed"`. Find the
`account_identity_hash` **inside the `limits` object**. It must be a 16-character
value. Before recording it, confirm that step 1 signed in to the intended account.
A hash alone does not identify the browser user.

On this first probe, `status_available: false` is expected because you have not
saved the expected hash yet. If the hash is null/missing, or either read is not
completed, see [troubleshooting](#troubleshooting); do not guess a hash.

## 3. Save the hash in your local config

Open `config.json` in a text editor. In the `plus` profile, replace this line:

```json
"expected_account_id_hash": null
```

with the same key and your actual hash in double quotes. For example, the
following is **synthetic**; do not copy its value:

```json
"expected_account_id_hash": "0123456789abcdef"
```

Keep the surrounding JSON and other settings as they are. Save the file, then run:

```bash
python3 -m optimizer check --config config.json
python3 -m optimizer probe --config config.json --alias plus
python3 -m optimizer dry-run --config config.json --read-accounts
```

Expected: `check` reports `ok: true`; the probe can report `status_available: true`
when identity, permission, windows and models are all available. The dry run
reports `live_requests_enabled: false`. A `hold` remains normal when required
information or a verified reset opportunity is missing. No model request runs.

Keep `config.json` and real probe output private. The config is ignored by Git;
check staged files before committing anything.

## Troubleshooting

| What you see | What to do |
|---|---|
| `codex: command not found`, a null version, or an unreviewed version | Repeat the PATH selection and version check in [CLI setup](CLI_SETUP.md). |
| `check` reports `ok: false` after editing | Check JSON syntax: double quotes around the hash, exactly 16 lowercase hexadecimal characters, and no missing/extra commas. |
| Probe says the selected context is not a ChatGPT subscription | Repeat the sign-in helper for that alias and confirm browser identity. |
| Account reads complete, but `limits.account_identity_hash` is null | The required usage identity is unavailable on that host/protocol. Stop at offline planning; do not substitute the top-level hash or invent one. |
| `status_available: false` after saving the correct hash | Identity, permission, complete windows or models may still be unavailable. Read the `limits` fields and `blocker` locally; unknown information holds. |
| Socket/permission error, startup failure, or timeout | This is a host capability blocker. Keep offline planning available; do not loosen sandbox or account-folder permissions. |
| Dry run reports `hold` | Read its `reason`. Missing information and unverified activity/spending controls intentionally hold; success does not require `would_request`. |
| Adding another alias causes a state/config error | Reconcile the existing aliases and state locally; do not delete uncertain records to force a run. |

If you ask for help, share the error category and command name, not credentials,
account hashes, real probe output, or private file paths.

## Sign in on a headless host

Where official device-code sign-in is available, use this instead of step 1:

```bash
python3 scripts/account_login.py --config config.json --alias plus --device-auth
```

Follow the displayed URL/code using a browser and confirm the intended account.
Device-code support can require an account/workspace setting. If unavailable,
resolve official sign-in on that host; do not copy credentials from another
computer. See [official authentication](https://learn.chatgpt.com/docs/auth#login-on-headless-devices).
On Windows replace `python3` with `py -3`. Then continue with step 2.

## Add a second account later

Keep your working `plus` profile and saved hash. In `config.json`, add the `pro`
profile from `examples/config.example.json` as a second object in the `profiles`
array, with a comma between the objects. Do not replace your configured file with
the template. Every account needs a distinct nickname and Codex home.

Let the helper create the second private home and sign in to the second account
(on Windows replace `python3` with `py -3`):

```bash
python3 scripts/account_login.py --config config.json --alias pro
python3 -m optimizer check --config config.json
python3 -m optimizer probe --config config.json --alias pro
```

Confirm the second browser identity, then save that probe's
`limits.account_identity_hash` in the `pro` profile using steps 2–3. Run
`python3 -m optimizer dry-run --config config.json --read-accounts` to read both.
Up to 16 profiles are supported. Leave existing aliases unchanged when reusing
state; changing/removing them can require manual reconciliation.

## Account-read boundaries

Homes accept `~` and resolve relative paths against the configuration file's
parent, so moving the current working directory does not select a different
login. CLI status/feed input paths remain relative to the invocation directory;
use absolute paths outside the clone. Each alias needs distinct homes.

The [AppServer methods](https://learn.chatgpt.com/docs/app-server#auth-endpoints)
used are `account/read`, `account/rateLimits/read` and `model/list` after initialization.
The probe does not log raw server messages, email addresses, tokens or reset
inventories. It emits a short account hash, bounded windows, booleans and model
IDs. Do not upload actual output to the repository or an issue. Installed Codex
may write its own caches/runtime files in the selected home; optimizer read-only
means no model turn, login command, credit purchase or redemption is invoked.

A sandbox/socket permission error is a capability blocker. Do not change unrelated
socket ownership, relax mode 0700, disable sandboxing, or escalate inference.
Version gating rejects unknown releases; review the schema and synthetic tests
before updating the reviewed version list.
