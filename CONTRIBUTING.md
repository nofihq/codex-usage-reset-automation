# Contributing

Use Python 3.10+ on Linux, macOS or Windows. Linux Python 3.12.3 is the verified
development runtime; native Windows/macOS execution is still pending validation.
On Windows replace `python3` below with `py -3`.
No dependencies need installing. Start with:

```bash
python3 -m optimizer doctor --config examples/config.example.json
python3 -m unittest discover -s tests -v
python3 scripts/privacy_check.py
```

Add tests for changed parsing, conservative holds and protocol contracts. Keep
fixtures synthetic. Do not run tests against an owner's login or inspect auth
files/private sessions. Protocol tests use a fake local Codex executable.

Before changing the AppServer version allowlist, inspect that release's generated
schema in an empty temporary home and validate required capabilities. Version
inspection is not evidence of successful subscription access. Update the
capability matrix with actual evidence and remaining unknowns.

A contribution must preserve dry-run defaults, explicit identity/allowance checks,
unknown activity/spending holds, and no paid fallback or automatic redemption.
Do not add live dispatch/schedules as a packaging change. Commit only source,
synthetic tests, generic examples and documentation; review `git diff --cached`
without including local config or private captures.

No open-source license is selected yet. Contributions and redistribution need
owner agreement until the owner approves licensing; repository visibility alone
does not supply an open-source license.
