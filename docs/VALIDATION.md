# Validation evidence — October 14, 2026

The repository contains a cloud dot setup recipe and a separate read-only Python
planner. The recipe uses the dot's native browser, private Pages and scheduler;
there is no bundled browser executor or live CLI command. Evidence below separates
real cloud behavior from offline code checks.

## Repository checks

The updated suite passes **106 tests on Linux with Python 3.12.3**. It covers the
91-test planning/protocol/fixed-reset baseline plus persisted metadata cadence,
real process restart and probe skipping, bounded runtime diagnostics, first-account
binding/provenance and private Page reference scanning. Native Windows/macOS
Python runtimes and other Python minor versions were not validated by these runs.

Relevant checks are:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/privacy_check.py
python3 scripts/verify_clean_clone.py
gitleaks git --redact --no-banner .
```

The clean-clone verifier uses the **committed** tree. Run it after committing the
reviewed changes so it exercises config copy, doctor/check, dry-run, synthetic
replay, privacy scan and installed zipapp behavior against that exact source.
These checks use synthetic inputs and send no account/model requests.

A real subprocess setup smoke test reproduced the old offline-demo-to-first-hash
failure. The fix completes the first binding and still rejects later hash changes,
removed established bindings, operational state migration and ambiguous state.
A fresh process also honors a saved metadata deadline and makes zero account-probe
attempts before it is due. These checks do not validate live dispatch.

The tracked-source scanner rejects private/generated paths, likely credentials,
non-synthetic emails and real-format cloud Page IDs. A synthetic Git-index test
verifies that private Page references are rejected without printing their values.
The scanner assists review; it is not proof that every possible secret is detected.

## Real cloud observations

The first scheduled attempt held when locally saved request/reset receipts were
missing. The Plus browser login survived and account usage was readable; no OK
was sent by that held run. File timestamps suggested restored/copied state, but
the exact cause of the missing files was not established. Local cloud files were
therefore removed from the role of authoritative request ledger.

A private Page with one canonical JSON block was tested through the native Pages
tool. Correct-hash replacements applied and read back exactly. A separate synthetic
single-block test used no title or sequence guard: a stale hash returned
`edit_conflict`, the winning state remained unchanged, and the identical candidate
applied after refreshing only its expected hash. The backend did not provide a
precise conflict diagnostic. No sequence guard was claimed when the read omitted it.

A separate scheduled cloud wake read, guardedly updated and exactly read back the
same private Page. This verified a later scheduled wake, not a forced fresh-container
restart. The old disposable chat was independently found completed with exact OK
and still archived. Missing historical raw reset receipts remained explicitly
missing; a controller report was labeled as chat-reported evidence.

A single task-scoped, expiring initialization permit was saved and read back. The
same saved Plus task then performed one scheduled recovery request using the
visible GPT-6 Luna model, lowest Light effort and fast mode off. The completed
response was exactly OK with no tools used. Two distinct numeric observations
**76.24 seconds apart** identified the same 300-minute target and unchanged reset.
The implied window start was within the send-to-completion observation interval.
Included allowance was available, credits were zero and automatic reload was off.
Only the exact new disposable chat was archived, and the permit remained consumed.

The later scheduled read-only wake retained that consumed permit, single-request
result, reset pair and archive evidence. It detected an omitted pre-send readback
timestamp. The original retained execution result supplied the actual matching
readback, 18.24 seconds before submission; the write/readback hashes and revisions
agreed. That provenance was persisted, and a further scheduled read-only wake
verified the corrected record with every required check passing and zero new model
requests. Missing old raw history stayed labeled missing; it was not fabricated.
The recovery therefore passed as a bounded unattended run with later durable-state
verification. The same task's enabled normal-due schedule was saved and read back
for the recorded reset plus two minutes, with the initialization permit consumed
and current-window submission blocked. Future routine checks require all fresh gates and an expired
verified anchor; long-term recurrence remains a separate observation.

These are environment-specific observations. They do not establish the universally
cheapest model, zero usage, all accounts' timer behavior, forced-restart recovery,
months of uninterrupted operation or exactly-once behavior under every failure.
Archiving retains data; it does not establish storage deletion.

## CLI installation and sandbox diagnosis

The official pinned `@openai/codex@0.159.2` installation was smoke-tested in an
isolated user-owned prefix. Its version-only probe reported reviewed true and
zero account reads. The earlier installation used Node.js 24.15.0/npm 12.0.2;
other Node versions were not individually tested. Official 0.159.2 cloud account,
rate-limit and model reads were previously verified on the separate cloud host.

The new credential-free runtime diagnostic was exercised with official 0.159.2
and 0.162.1 in empty private homes on the local Linux host. Direct sandbox smoke
passed; a nested sandbox failed with the daemon-directory category. Both direct
and nested checks failed on the examined dot host because its direct tool process
was already nested. These diagnostics read no account and sent no model request.
Version 0.162.1 is diagnostic-only, not added to the account-adapter allowlist.

See [CLI setup](CLI_SETUP.md#nested-cloud-sandbox-blocker) for the upstream issue
and official source. No permission change, sandbox bypass or supported top-level
CLI execution route was introduced. The experimental app-server environment option
was schema-inspected but remains execution-disabled because startup warm-up quota
behavior was not verified.

## Setup boundaries

Existing eligible dot access, private Pages, scheduling and the cloud browser are
prerequisites. Plus alone is not currently listed as dot-eligible. The client may
be a supported desktop browser or ChatGPT app; no Python/Node installation or
always-on personal computer is required for the cloud recipe. This does not
validate native Python on every OS or make new hosting/API billing free.

The repository creates no job merely by being cloned. The owner must authorize
setup, sign in privately and inspect the saved cloud task/result. Future routine
runs must keep the initialization permit consumed, use only expired verified
anchors, preserve uncertain submissions and honor all fresh spending/identity gates.
See [the cloud guide](CLOUD_DOT_SETUP.md) and [safety contract](SAFETY_CONTRACT.md).
