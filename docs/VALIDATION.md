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
