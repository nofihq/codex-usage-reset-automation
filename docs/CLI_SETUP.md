# Install the supported Codex CLI

Skip this page if you only want offline planning. Account reading needs the
official Codex CLI. This project accepts **0.158.0 and 0.159.2**; the beginner
path below pins **0.159.2**. Other versions are rejected until their protocol
is reviewed. Installing the latest release does not guarantee compatibility.

Version 0.159.2 account read methods were previously verified in a separate cloud
environment. Local 0.158.0 schema was inspected, but account startup was blocked
by runtime restrictions. Installing successfully does not prove account access
will work on every host.

## 1. Check Node.js and npm

In a terminal on Linux/macOS/WSL2, or PowerShell on Windows, run:

```bash
node --version
npm --version
```

Both commands must work. The pinned package declares Node.js 16 or newer;
use a currently supported Node.js LTS release from the
[official Node.js download page](https://nodejs.org/en/download) if you need to
install or update Node.js. Choose your actual OS; use Linux instructions in WSL2.
Return here once both version commands succeed.

## 2. Install exactly 0.159.2 in its own folder

### Linux, macOS or WSL2 (Bash)

These commands download the official package into a user-owned folder. They do
not require `sudo`, change your npm configuration, or replace a CLI elsewhere:

```bash
npm install --global --prefix "$HOME/.local/share/codex-optimizer/cli-0.159.2" @openai/codex@0.159.2
export PATH="$HOME/.local/share/codex-optimizer/cli-0.159.2/bin:$PATH"
hash -r
codex --version
```

Expected output from the last command:

```text
codex-cli 0.159.2
```

The `export` selects this CLI in the **current terminal**. Keep using that terminal
for sign-in and probes. In each new terminal, run the same `export PATH=...` line
and `hash -r` again before continuing; no shell startup file is edited.

If `codex --version` reports another version, check the installed binary directly:

```bash
"$HOME/.local/share/codex-optimizer/cli-0.159.2/bin/codex" --version
type -a codex
```

The direct binary must report `codex-cli 0.159.2`. If a shell alias or function
overrides `codex`, use a fresh Bash terminal and repeat the PATH commands there.
If npm reports a permission error, check that the destination belongs to your
user; this installation should not need administrator rights.

### Native Windows (PowerShell)

Run these commands in PowerShell. npm's Windows installation puts its command
shim directly in the prefix folder, so this PATH differs from the Bash version:

```powershell
npm install --global --prefix "$env:LOCALAPPDATA/codex-optimizer/cli-0.159.2" @openai/codex@0.159.2
$env:PATH = "$env:LOCALAPPDATA/codex-optimizer/cli-0.159.2;$env:PATH"
codex --version
```

Expected: `codex-cli 0.159.2`. Keep using this terminal; repeat the PATH line in
new PowerShell windows. To inspect an unexpected version:

```powershell
& "$env:LOCALAPPDATA/codex-optimizer/cli-0.159.2/codex.cmd" --version
Get-Command codex -All
```

The optimizer invokes the official npm JavaScript launcher through Node directly,
so probes do not depend on executing a batch file or a PowerShell script.

## 3. Verify the optimizer sees the supported version

From the repository folder, with the single-account `config.json` from the README:

```bash
python3 -m optimizer probe --config config.json --alias plus --check-version-only
```

On Windows, use `py -3` instead of `python3` in that command.

Expected JSON includes `"codex_version": "0.159.2"`, `"reviewed": true`, and
`"account_reads": 0`. This check uses an empty temporary Codex home; you do not
need to sign in yet. If the version is null or unreviewed, resolve the installation
or PATH issue before proceeding.

Next: [sign in to your one account](ACCOUNTS.md).

The package installation is free and does not send model requests. For general
CLI background, see [OpenAI's CLI guide](https://learn.chatgpt.com/docs/cli).
Use the pinned commands above for this project's compatibility requirements.
