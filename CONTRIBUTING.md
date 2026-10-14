# Contributing

Use Linux and Python 3.10+; earlier packaging was verified on Python 3.12.3.
No dependencies need installing. Start with:

```bash
python3 -m optimizer doctor --config examples/config.example.json
python3 -m unittest discover -s tests -v
python3 scripts/privacy_check.py
```

Keep fixtures synthetic. Do not run tests against an owner's login or inspect auth
files/private sessions. Protocol tests use a fake local Codex executable. A passing
suite does not validate production account access or unattended execution.

Changes must preserve the [safety contract](docs/SAFETY_CONTRACT.md). Test both the
default verified-inactivity policy and the explicit remaining-percent heuristic.
Cover partial non-target usage, target selection, exhausted buckets, explicit
active work, missing/stale data, identity mismatches, and nonzero or unknown credit
controls. Unknown cross-device activity is permitted only by the selected
heuristic; never describe it as proven inactivity.

Test fixed-reset evidence using distinct read times for the same target. Repeated
snapshots, moving `now + duration` estimates, unrelated expired buckets, missing
anchors and future anchors must not create opportunities. For the fake transaction
envelope, test the before-send durable marker, account/window deduplication,
completed exact `OK`, two matching post-request timers, and uncertain outcomes.
Never clear uncertain state to make a test or retry succeed.

Before changing the AppServer version allowlist, inspect that release's generated
schema in an empty temporary home and validate required capabilities. Version
inspection is not evidence of successful subscription access. Update the
capability matrix with actual evidence and remaining unknowns. The stable 0.162.1
sandbox diagnosis does not make that release an approved adapter version.

Preserve dry-run defaults, all spending/identity gates, and no paid fallback or
automatic redemption. Do not add live dispatch, browser adapters or schedules as
a packaging change. Do not bypass the nested sandbox blocker by changing daemon
permissions, remounting, disabling isolation, or substituting a listener address.
Any cleanup contract must target only the exact completed disposable chat;
archiving retains data, and permanent deletion must never be autonomous.

Commit only source, synthetic tests, generic examples and documentation. Review
`git diff --cached`; exclude local config, real account identifiers, private
captures, chat contents, receipts, credentials and actual reset inventories.

No open-source license is selected yet. Contributions and redistribution need
owner agreement until the owner approves licensing; repository visibility alone
does not supply an open-source license.
