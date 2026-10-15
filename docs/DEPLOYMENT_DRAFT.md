# Cloud dot workflow and optional read-only scheduling

Use [single-account cloud dot setup](CLOUD_DOT_SETUP.md) for the cloud workflow.
It runs in an existing eligible dot's cloud environment with a private Page ledger
and one saved task. A personal computer can be off; no external runner, API key,
new hosting account or credential-bearing GitHub workflow is required. Existing
plan eligibility and included allowances still apply. Plus alone is not currently
listed as dot-eligible; the monitored account and the dot owner's eligibility are
separate setup checks.

The repository installs no schedule, service or secret by itself. The dot must
inspect its available native tools, sign in privately, test the guarded Page and
a later scheduled read/write, then perform the explicitly authorized one-time
initialization. Routine later runs use the recorded fixed anchor and durable
account/window marker. Missing state or an uncertain submission holds for
reconciliation; the worker must never silently initialize again.

Rearm the same cloud task for the verified reset plus two minutes. Keep current
state small and retain unresolved outcomes. One short prompt and one OK limit
requested output, but the cloud task itself can consume Work/Codex allowance.
Archive only the exact disposable chat; archiving retains data. Neither total
cloud storage nor long-term uninterrupted login is guaranteed by this setup.

## Optional Python metadata tick

Every `dry-run` exits after one finite tick and sends no model request. An existing
system scheduler on a Linux machine you control can run that read-only command.
A sleeping or offline machine misses those local ticks; this is separate from
the cloud dot route. No timer unit, crontab, hosted runner or workflow is supplied.

Test an absolute config/state command interactively before scheduling it:

```bash
python3 -m optimizer dry-run --config /absolute/path/config.json --state-dir /absolute/private/state --read-accounts --due-only
```

Replace the example paths with your private locations. `--due-only` requires
`--read-accounts` and real time. It persists a deadline and configuration fingerprint
for each account; a fresh process skips its account probe until due. A configuration
change or a newly ingested public global-reset hint can request an earlier metadata
read. Such a hint never permits model usage.

Unavailable metadata uses bounded exponential backoff: the default starts at one
hour, doubles, and caps at twelve hours. Success resets the failure count and
records the decision's next deadline. JSON includes `account_probe_attempts` and
change-only `alerts`: `account_check_blocked` once on entry, and
`account_check_recovered` once on recovery. An unchanged skipped/blocked tick has
no repeated health alert. Explicit `probe` commands still run when requested.
These flags do not install a scheduler or add live dispatch.

Use one persistent private local state directory per configuration and one host
for that directory. POSIX `flock` is not a distributed lock. Do not copy subscription
credentials into runners or use caches/artifacts as an authoritative ledger.
The Python package supplies no Page transport or distributed multi-executor
adapter. The cloud recipe instead uses the dot's native Pages tool and a single
responsible sender with a guarded canonical block.

The examined cloud host still blocks nested CLI model execution. The credential-free
[runtime diagnostic](CLI_SETUP.md#nested-cloud-sandbox-blocker) helps identify that
failure; it does not enable a bypass. [Validation](VALIDATION.md) separates offline
code tests from the observed cloud workflow.
