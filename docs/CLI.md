# Native usage reader

The default [dot setup](SETUP.md) runs entirely in the cloud. This optional local
reader checks usage when you invoke it; it does not schedule itself or send `OK`.
Use the same reader inside the dot for unattended cloud checks.

## Install

Install [Python 3](https://www.python.org/downloads/),
[Node.js](https://nodejs.org/en/download) and [Git](https://git-scm.com/downloads).
Python 3.10+ and Node.js 16+ are required; the native checks use Python 3.12 and
Node.js 22. Then clone the repository and install the pinned official CLI:

```sh
git clone https://github.com/nofihq/codex-usage-reset-automation.git
cd codex-usage-reset-automation
npm install --prefix .cloud-tools --no-audit --no-fund @openai/codex@0.159.2
```

### Windows PowerShell

```powershell
py -3 cli/read_account_status.py --init-private ../codex-reset-private
$env:CODEX_HOME = (Resolve-Path ../codex-reset-private/plus).Path
& ./.cloud-tools/node_modules/.bin/codex.cmd -c forced_login_method=chatgpt -c cli_auth_credentials_store=file login --device-auth
```

### macOS or Linux

```sh
python3 cli/read_account_status.py --init-private ../codex-reset-private
CODEX_HOME="$PWD/../codex-reset-private/plus" .cloud-tools/node_modules/.bin/codex \
  -c 'forced_login_method="chatgpt"' \
  -c 'cli_auth_credentials_store="file"' login --device-auth
```

Complete the official authorization privately as the intended account. Device
authorization must be enabled for that account; otherwise follow a supported
[official sign-in flow](https://learn.chatgpt.com/docs/auth) or stop. Never copy
tokens from another device or substitute an API key. Browser login is separate.

## Bind one account and read

Create `plus.expected.json` inside the new `codex-reset-private` directory:

```json
{"expectedEmail":"your-account@example.invalid"}
```

Replace the example with your signed-in email privately. On macOS/Linux run
`chmod 600 ../codex-reset-private/plus.expected.json`. On Windows the file must
inherit the private directory's restricted ACL; shared or unsupported permissions
produce a hold. Keep all account files outside the checkout.

Windows:

```powershell
py -3 cli/read_account_status.py --tools .cloud-tools --home ../codex-reset-private/plus --runtime ../codex-reset-private/runtime --expectations-file ../codex-reset-private/plus.expected.json
```

macOS/Linux:

```sh
python3 cli/read_account_status.py --tools .cloud-tools \
  --home ../codex-reset-private/plus \
  --runtime ../codex-reset-private/runtime \
  --expectations-file ../codex-reset-private/plus.expected.json
```

The reader selects the official native executable directly, including
`codex.exe` on Windows; it does not execute a batch file or require WSL. A checked
identity produces `state: metadata_verified` with `eligibility: unknown`.
Missing, mismatched or unsafe data produces `state: hold` and exit code 2.
Neither result submits a request. See [field mappings and browser gates](CLOUD_TOOLS.md#read-and-validate).

For another account, create a separate private CLI home and expectations file;
never reuse a binding or credential cache. Keep the normal cloud timer and Page
workflow for autonomous execution while your personal computer is off.

## Verify the installation

Require a real `metadata_verified` read for your own account before using its
numbers in a cloud task. The [native checks](../.github/workflows/native-cli.yml)
test Windows, macOS and Linux installation, executable selection, protocol handling
and local safeguards without credentials. Those checks do not sign in to your
account, verify browser sessions or send model requests. Use the
[setup verification checklist](VERIFY.md) for those account-specific checks.
