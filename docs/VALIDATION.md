# Validation evidence — October 14, 2026

This project is a dry-run planner with explicit read-only metadata support and
fixture-testable request/cleanup boundaries. It is **not a production-ready
unattended dispatcher**. Evidence below separates repository tests, earlier setup
checks, a narrow manual browser observation, and blocked/unverified behavior.

## Repository verification scope

The October 14 safety-update suite passes **91 tests** on Linux with Python
3.12.14. The prior packaging baseline passed 57 tests on Python 3.12.3. The
tracked-source privacy scan covers all 32 source/example/documentation files,
and whitespace checks pass. These checks do not read an owner's account, send
a real request, or manipulate a real chat. They cover:

- Configuration, aliases, explicit target-window selection, default verified
  inactivity, and opt-in remaining-percent activity behavior.
- Missing/stale/future status, identity/permission failures, partially used
  non-target buckets, exhausted buckets, explicit active work, and spending gates.
- Distinct fixed-reset reads for the same target, minimum observation separation,
  persisted anchors, expiration, moving idle estimates, and missing/legacy state.
- A fake request boundary: durable before-send marker, account/window deduplication,
  completed exact `OK`, two agreeing post-request resets near request + duration,
  bounded proven-no-usage retries, and uncertain outcomes held for reconciliation.
- A disabled cleanup boundary using synthetic completed disposable-chat evidence;
  no actual browser archive or permanent deletion is performed by the suite.
- Read-only adapter framing through a fake local Codex executable: allowed method
  sequence, explicit gateway OAuth capability, no proactive refresh, bounded
  responses, unsupported auth requests, and malformed framing.
- Private state permissions, symlinks/hard links, atomic writes, limits, locks,
  retention, bounded logs, and installed zipapp behavior.

Run these checks against the final checkout before publication:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/privacy_check.py
python3 scripts/verify_clean_clone.py
```

`verify_clean_clone.py` tests the **committed** checkout. Run it after including
reviewed changes in a local commit so that it covers those changes. It reproduces
config-copy, doctor/check, dry-run, synthetic replay, privacy scan, and installation
without network or authentication. Passing it establishes the documented offline
path on the tested Linux/Python runtime, not a successful cloud deployment.

## Earlier installation and account evidence

The beginner CLI installation was smoke-tested with the official
`@openai/codex@0.159.2` package in an isolated user-owned prefix. Its version-only
probe reported `reviewed: true` and `account_reads: 0`, using Node.js 24.15.0 and
npm 12.0.2. That check did not sign in or validate live account behavior; other
Node.js versions were not individually tested.

The public keyless tracker previously completed a bounded REST fetch. Official
0.159.2 cloud account/rate-limit/model reads and isolated sign-ins were previously
verified on a separate host. Earlier 0.158.0 schema inspection used an empty
Codex home; restricted local AppServer startup failed. None of these observations
establishes that model execution works in every account or environment.

## Narrow manual browser verification

On October 14, a manual environment-specific browser Work check used **Luna
Light with fast mode off**. One disposable request completed with exactly `OK`.
Two subsequent status reads showed the same fixed five-hour reset, and archiving
that exact disposable chat was verified. This supports that single observed
sequence only. It does not prove the model is universally least-cost, that usage
was zero, or that all accounts share the same timer behavior.

No account identifier, email, chat content, private link, receipt, inventory,
authentication material or capture is included in this record. The repository
has no working browser adapter. Archiving retains data rather than deleting it.
A later unattended-session execution remains pending; the manual check is not
proof of recurring automation, cross-device inactivity, or zero retention.

## Verified cloud CLI blocker

Portable CLI model dispatch on the examined nested cloud host remains blocked.
The fixed daemon path requires `0700`, while the outer sandbox masks it with a
read-only mode-`000` mount. Stable 0.162.1 retains this mechanism; it was reviewed
for diagnosis, not admitted to the metadata adapter's version allowlist. The
[CLI setup diagnosis](CLI_SETUP.md#nested-cloud-sandbox-blocker) links the public
issue and official source. No supported override or sandbox bypass is included.

A successful response alone cannot establish timer anchoring. Idle API reset
estimates that drift with each read are not fixed anchors. The new two-read checks
are exercised synthetically; the one manual fixed five-hour observation does not
validate unattended expiration-to-request behavior across later sessions.

## Privacy and remaining limits

Committed account, credit, reset, and model examples are synthetic. Keep local
configuration, account hashes, actual inventories, receipts, captures and sessions
out of source control. The tracked-source privacy scanner assists manual review;
it is not proof that all possible secrets or private facts were detected.

The repository enables no schedule or live request. Real executor integration,
recurrent unattended requests, cross-device inactivity detection, distributed
state/locking and automatic browser cleanup remain unvalidated or unimplemented.
See [CAPABILITIES.md](CAPABILITIES.md) and [SAFETY_CONTRACT.md](SAFETY_CONTRACT.md).
