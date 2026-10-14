# Validation evidence — October 14, 2026

Repository packaging was verified on Linux with Python 3.12.3 and Git, using only
existing free tooling. The original 36 tests passed before edits; 57 distinct
tests pass after packaging and conservative adapter/storage changes.

## Verification scope

- Offline configuration accepts 1–16 aliases, rejects duplicates, and resolves
  account homes relative to the configuration file.
- Doctor/check never inspect authentication, invoke account processes, or write
  runtime state. Invalid configuration produces a scrubbed JSON hold/error.
- Official adapter framing is exercised through a synthetic local executable,
  not the owner's CLI account: exact allowed method sequence, explicit gateway
  OAuth capability, no proactive refresh, model/status reads, bounded responses,
  unsupported server auth requests, and malformed framing.
- Normalization verifies expected usage-account identity, explicit permission,
  complete models and duration-based window identity. Missing controls or rounded
  zero activity remain unknown and hold.
- State tests cover private ownership/permissions, unchanged shared directories,
  symlinked/hard-linked files, atomic limits, locks, retention and bounded logs.
- Installed zipapp runs from an unrelated directory; errors retain nonzero exit
  codes; accidental overwrite is refused.
- A fresh Git clone is checked with the documented config-copy, doctor/check,
  single-account dry run, tests, synthetic replay, privacy scan and executable installation steps.
  `scripts/verify_clean_clone.py` reproduces these checks without network or auth.

The beginner CLI installation path was also smoke-tested separately: the official
`@openai/codex@0.159.2` npm package installed into an isolated user-owned prefix,
the binary reported `codex-cli 0.159.2`, and the optimizer's version-only probe
reported `reviewed: true` and `account_reads: 0`. This did not sign in, inspect
an existing account, or validate live metadata/automation behavior. Node.js
24.15.0 and npm 12.0.2 were used; other Node.js versions were not tested here.

Run from a committed checkout:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/privacy_check.py
python3 scripts/verify_clean_clone.py
```

Every account, usage, credit, reset and model example committed in the repository
is synthetic. No owner email, owner-specific home path, credential, private capture,
actual reset inventory or account session was included. Git commits use a generic
project identity. Private configuration and the preserved earlier source backup
are outside the tracked source set.

## Portability and cloud-benefit update

The current portability suite contains 65 tests: 63 pass on Linux, and two native
Windows ACL integration tests are skipped on Linux. It adds cross-process locking,
Windows ACL policy rejection, three-OS CLI readiness, safe npm-shim resolution,
explicit isolated interactive sign-in coverage, and timeout cleanup of the
child process and pipe reader. Native Windows/macOS execution
has not been run in this session; these implementations are not labeled validated.

Linux no longer gates macOS/Windows out of the CLI. Windows uses native private
ACL creation/validation and nonblocking byte-range locks; POSIX retains ownership,
permissions and flock checks. A bounded threaded pipe reader supports the account
protocol across OSes. The installer emits a Windows `.pyz`, and verification uses
the current Python interpreter rather than assuming a `python3` command exists.

The original personal dot conversation was inspected read-only. It reported cloud
CLI account reads and manual cloud-browser Work message tests without using the
personal computers, and reported archiving those test chats. No new account reads,
model requests, cloud deployment, chat cleanup or dot/schedule changes were made
for this update. Native OS integration, the pending Plus scheduled run and reusable
cloud automation remain unverified here. See [cloud and usage](CLOUD_AND_USAGE.md).

## Historical evidence and unverified behavior

The public keyless tracker adapter had previously completed a bounded REST fetch.
No new public-feed fetch was needed for packaging; tests use synthetic records.
Official 0.159.2 cloud account/rate-limit/model reads and isolated sign-ins had
previously been verified in a separate environment. The packaging pass inspected
0.158.0 schemas using an empty temporary home, and did not read real credentials,
private sessions or account usage. Local AppServer startup had previously failed
under restricted runtime filesystem conditions.

Earlier manual browser Work requests succeeded in an environment-specific cloud
browser. This is not evidence for a portable CLI executor. Cloud CLI inference
encountered socket-directory ownership/mode restrictions; no sandbox bypass is
implemented. First-use timer anchoring, cross-device inactivity, recurrent
unattended requests and browser cleanup remain unverified/unsupported here.

The tests and clone verification establish source portability within the stated
Linux runtime, not a successful cloud deployment or autonomous account dispatcher.
No schedules or live requests were activated during packaging. See
[CAPABILITIES.md](CAPABILITIES.md) for the full limits.
