# Security and privacy

The default command path is offline planning. Official account reads are explicit,
limited to initialize/account/status/model-list methods, and require a separate
account home. The optimizer never opens auth/session/history files. Codex itself
owns authentication and may write runtime/auth state in that selected home.

Do not commit `config.json`, private snapshots, account hashes, credentials, actual
reset inventories, runtime state, browser captures or session transcripts. Ignore
rules are a convenience, not a confidentiality guarantee; inspect the tracked
file list and run `python3 scripts/privacy_check.py` before committing. Use only
synthetic `.invalid` identities in tests. Never paste real probe output into issues.

The public tracker is untrusted data. Only allowlisted metadata is retained; text
cannot become commands, prompts, logs or permission to use an account. Redirects,
oversized/stale responses and missing fields provide no authorization. Credit
balances, permission, identity and activity must never default to safe values.

Runtime state is bounded and uses atomic replacement and single-host locking.
On POSIX the directory must be owned by the current user with no group/world
access. Native Windows requires a private ACL granting access only to the current
user, SYSTEM and local administrators; ACL-less/shared filesystems are rejected.
Symlinked directories, symlinked/hard-linked state files, wrong owners and
unsafe file write modes are rejected. Existing shared directory permissions are
never repaired automatically. Create a new private directory or inspect locally.
Windows junctions/reparse points are also rejected. Existing Windows ACLs are
never repaired automatically. Same-user hostile concurrent filesystem modification is outside this guarantee;
do not share this directory among adversarial processes or multiple hosts.

No paid fallback, credit purchase, automatic earned-reset redemption or live
inference command exists. Unknown cross-device activity holds; rounded percentages
do not establish inactivity. Do not loosen sandbox/socket permissions to bypass a
capability error. Do not add credential-bearing hosted workflows.

To report a vulnerability, use the repository owner's private reporting channel
where available. Share a synthetic reproduction and code location, without tokens,
account output or private paths. This guidance does not claim a formal security
audit or vulnerability-free software.
