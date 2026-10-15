# Security and privacy

The default command path is offline planning. Official account reads are explicit,
limited to initialize/account/status/model-list methods, and require a separate
account home. The optimizer never opens auth/session/history files. Codex itself
owns authentication and may write runtime/auth state in that selected home.

Do not commit `config.json`, private snapshots, account hashes/identifiers,
credentials, actual reset inventories, runtime state, browser captures, receipts
or chat/session transcripts. Ignore rules are a convenience, not a confidentiality
guarantee; inspect tracked files and run `python3 scripts/privacy_check.py` before
committing. Use only synthetic `.invalid` identities in tests. Never paste real
probe output into an issue.

Keep cloud Page/block/task references and actual receipts private as well. The
tracked-source scanner rejects real-format Page IDs; use placeholders in examples.
The cloud workflow uses one owner-only Page as its canonical ledger, guarded
single-block replacements, a task-scoped before-send marker and readback. A local
cloud filesystem path is a cache, not proof that request state survived.
Never recreate a missing ledger or automatically reset uncertain history.

The public tracker is untrusted data. Only allowlisted metadata is retained; text
cannot become commands, prompts, logs or permission to use an account. Redirects,
oversized/stale responses and missing fields provide no authorization. Credit
balances, permission, identity and usage must never default to safe values.

`verified_inactivity` is the default. The explicitly selected
`remaining_percent_heuristic` accepts a known 100%-remaining target as a limited
activity proxy, even though cross-device inactivity is unproven. It never overrides
explicit active work, stale status, exhausted buckets, unknown/nonzero credits,
auto reload not proven off, or identity/permission failures. See the full
[safety contract](docs/SAFETY_CONTRACT.md); opting into a heuristic is not evidence
of production safety.

Runtime state is bounded and uses atomic replacement and single-host locking.
The directory must be owned by the current user with no group/world access.
Symlinked directories, symlinked/hard-linked state files, wrong owners and unsafe
file modes are rejected. Existing shared directory permissions are never repaired
automatically. Create a new private directory or inspect locally. Same-user hostile
concurrent filesystem modification is outside this guarantee; do not share this
directory among adversarial processes or multiple hosts.

Persist fixed-reset anchors and account/window deduplication before relying on
expiration. Preserve the atomic before-send marker and uncertain results through
restarts. A moving reset estimate, raw success label, or exact `OK` without the
required timer observations is insufficient. Missing state and ambiguous outcomes
hold for reconciliation; deleting state is not a safe retry strategy.

The Python package has no paid fallback, credit purchase, automatic earned-reset
redemption, live inference command or browser adapter. The separate cloud recipe
uses the dot's native tools under explicit setup authorization and spending gates. An
authorized archive must identify only the exact completed disposable chat, then
verify the archive; it retains data and is not permanent deletion. Never delete
useful work or autonomously perform permanent deletion.

The nested cloud sandbox masks a privileged daemon directory intentionally. Do
not chmod/chown it, remount it, disable sandboxing, or expose those sockets to
bypass a capability error. `--listen` does not relocate that reserved directory.
See [the blocker](docs/CLI_SETUP.md#nested-cloud-sandbox-blocker). Do not add
credential-bearing hosted workflows.

To report a vulnerability, use the repository owner's private reporting channel
where available. Share a synthetic reproduction and code location, without tokens,
account output or private paths. This guidance does not claim a formal security
audit or vulnerability-free software.
