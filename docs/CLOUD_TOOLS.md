# Cloud usage reader

These commands are for the **dot's cloud computer**, not your personal device.
Ask the dot to perform them in a private cloud working directory. The official
Codex CLI reads authenticated account metadata; the small reader validates and
redacts it. The cloud browser separately sends `OK` and checks spending controls.

## Install

The cloud computer needs Python 3.10+, Node.js and npm. The pinned CLI package
requires Node.js 16 or newer; use an available supported Node release. Have the
dot check these prerequisites first. A missing runtime is a setup blocker, not a
reason to use your personal computer or a paid runner.

From the repository checkout on the cloud computer:

```sh
node --version
npm --version
python3 --version
umask 077
python3 cli/read_account_status.py --init-private ../codex-reset-private
npm install --prefix .cloud-tools --no-audit --no-fund @openai/codex@0.159.2
.cloud-tools/node_modules/.bin/codex --version
```

Require `codex-cli 0.159.2`. This adapter pins an inspected protocol version;
do not silently upgrade it. Both generated protocol schemas and real read-only
behavior must be reviewed before changing the supported version.

The `.cloud-tools` installation is ignored by Git. Account homes and private
expectations live in the sibling `codex-reset-private` directory, outside the
checkout. Never commit, upload or copy account data between users or accounts. No local Python package, optimizer installer or background daemon is
required.

## Sign in

Browser sign-in and CLI sign-in are separate. Use one private CLI home per
monitored account. For the first account, the dot starts the official device flow:

```sh
CODEX_HOME="$PWD/../codex-reset-private/plus" .cloud-tools/node_modules/.bin/codex \
  -c 'forced_login_method="chatgpt"' \
  -c 'cli_auth_credentials_store="file"' login --device-auth
```

Complete the official authorization privately as the intended account, including
MFA. Never paste a token, password or credential file into chat. If device sign-in
is unavailable for the account, use a supported official sign-in flow or stop;
do not substitute an API key or copy browser cookies. The file credential store
keeps this CLI home separate from other accounts; only the official CLI reads it.

Use the same home and credential-store setting for metadata reads. Compare the
CLI's returned email/plan with the intended private account binding and verify
the cloud browser selects that identity too. Expiry or account switching requires
supported sign-in recovery and a new identity check before continuing.

## Read and validate

Have the dot create `../codex-reset-private/plus.expected.json`, restricted to
its owner, containing `{"expectedEmail":"YOUR_ACCOUNT_EMAIL"}`. Supply the real
identity privately; the public repository contains no account configuration.
Then the dot runs:

```sh
python3 cli/read_account_status.py --tools .cloud-tools \
  --home ../codex-reset-private/plus \
  --runtime ../codex-reset-private/runtime \
  --expectations-file ../codex-reset-private/plus.expected.json
```

`metadata_verified` means the identity binding passed; `eligibility` remains
`unknown`. A `hold` exits with code 2 and a fixed, redacted reason. Never treat
null fields as zero or as permission to send. The optional `--inventory` reads
banked-reset metadata when due and never redeems it.


The adapter calls only `initialize`, `account/read` with `refreshToken=false`,
`account/rateLimits/read`, and `model/list`. It never starts a thread, warms up a
model, sends a turn, consumes a banked reset or signs in automatically.

Bind root-level authenticated `workspaceRouting.chatgptAccountId` from
`account/read` to the usage response's `accountId` **before redacting either**.
Missing or conflicting identity holds. The experimental protocol fields must be
explicitly enabled; their presence in a schema alone is not a passing live read.

Numeric fields are `usedPercent`, `windowDurationMins` and `resetsAt` (Unix seconds).
Match the configured target by duration, not by `primary`/`secondary` position or
plan name. Unknown or malformed data holds. `model/list` is a catalog, not proof
that a model is included or a permission to submit a request.

The dot must still inspect visible credits, automatic reload, account selection
and model/effort settings in its cloud browser. A successful metadata read alone
does not authorize an `OK`. Save durable results and schedules in the guarded
Page rather than relying on cloud files surviving forever.

Official references: [CLI authentication](https://learn.chatgpt.com/docs/auth),
[app-server account methods](https://learn.chatgpt.com/docs/app-server#auth-endpoints),
and [the pinned protocol source](https://github.com/openai/codex/tree/rust-v0.159.2/codex-rs/app-server-protocol).

For optional native use outside the dot, see [Windows/macOS/Linux CLI setup](CLI.md).
The cloud workflow does not require that local installation.
