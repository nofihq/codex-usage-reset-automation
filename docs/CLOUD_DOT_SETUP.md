# Cloud dot setup — single monitored account

Use your dot's cloud browser, private Pages and scheduler for one monitored
account. Your personal computer can be off after setup; no external runner or
additional hosting is needed within an existing eligible plan's allowances.
The Python CLI is a separate read-only planner, not the browser dispatcher.
See OpenAI's [cloud computer documentation](https://learn.chatgpt.com/docs/dots/computers-and-apps)
for the distinction between the dot's computer and an optional connected device.

## What you need

- Existing access to a dot, its cloud browser, cloud scheduling and private Pages.
  Check [current eligibility](https://learn.chatgpt.com/docs/dots#access).
  Plus alone is not currently listed as a dot-eligible plan. A Plus account can
  be the one monitored identity when the owner already has eligible dot access.
- An included-usage account that you own, with purchased credits at zero and
  automatic reload off. Unknown spending controls mean hold.
- Access to this repository. No local Python, Node, always-on laptop, external
  runner, new hosting account or API key is needed for the cloud workflow.

Use the ChatGPT mobile app, desktop app, or a desktop browser. Mobile web is not
supported by dots. The cloud performs the work; native Windows/macOS Python
runtime validation is a separate matter.

## Start with one account

Give your dot the repository URL and this instruction:

> Read the cloud setup and safety contract in this repository. Set up one
> monitored account in your cloud environment, using the 100%-remaining target
> policy only after explaining its rounding limitation. Use no connected personal
> computer, external hosting, purchased credits or API-key fallback. Verify my
> intended identity and sign me in privately if needed. Create one private Page
> ledger, test guarded writes/readback and a scheduled cross-run canary, and put
> its exact references in one saved cloud task. After all checks pass, initialize
> one disposable baseline request that asks only for OK, verify the completed
> response and two matching reset reads at least 60 seconds apart, then archive
> that exact disposable chat and schedule the next eligible check. Preserve any
> prior uncertain history; initialization is not permission to reset lost state
> or repeat an uncertain submission. Report the verified result and next wake.

The dot must inspect whether its actual tools support every step. Missing browser,
Page or scheduler support means hold; the repository does not grant these tools.

Sign in in the dot's cloud browser using the supported private sign-in flow.
School MFA and SMS may need you. Do not copy cookies, tokens or auth files.
Confirm the selected browser identity matches the account whose usage is read.

For the configured Plus target, verify the observed target is 300 minutes and
100% remains; the weekly bucket must also be available, though it need not be
100%. The default Python policy still requires verified inactivity. The selected
remaining-percent policy accepts an imperfect proxy and must be explicit.

## Require durable state before any request

Local cloud files can be missing or restored in a later scheduled run. A cloud
filesystem path is not sufficient proof that the submission ledger survived.

Use one private, owner-only Page containing one small canonical JSON block.
Save the Page ID, block ID and account binding in the saved cloud task. Never
commit these private values to this repository. Do not recreate a missing Page or
block automatically.

1. Read the block and retain its returned hash. Use a sequence guard only when
   the same read actually supplies one.
2. Replace that single block with its expected hash. Inspect every edit receipt.
   A conflicting or unknown save requires readback and reconciliation.
3. Verify a stale writer cannot overwrite the current block, and that rejected
   edits leave the canonical state unchanged.
4. Run a separate scheduled read/write canary against the same Page. Do not rely
   on the original process, local files or an in-memory copy. Keep this canary
   free of model requests and finish it without a recurring duplicate.
5. Before sending, atomically claim the account/window with a unique request
   marker and confirm that exact marker through a new Page read. Another writer,
   existing inflight/uncertain marker, missing state or changed identity holds.

Keep the current JSON small. Retain the latest completed request, current fixed
anchor, exact cleanup target and every unresolved outcome; omit raw transcripts,
screenshots and inventories. This does not promise a bound on the service's own
version history or chat retention.

## Validate the live result

A direct, owner-authorized initialization is separate from routine automatic
expiration checks. Preserve the provenance of any missing/reconciled old history.
Never treat 100% remaining alone as proof that no request was already sent.
Save an expiring, task/account/target-scoped permit with a request budget of one.
The scheduled worker consumes that permit into the durable marker before sending;
the controller and other workers stay read-only. Record the actual pre-send
readback proof before the request, including the marker/hash and observation time
or an authoritative execution-order reference. Missing proof must be caught
before sending, rather than discovered only in a later audit.

An eligible request asks only `Reply with only OK.` using the verified included
model. Require a completed response exactly `OK`, not a submission spinner.
Then make two distinct fresh account reads at least 60 seconds apart. Both must
identify the same target and exact fixed reset near request time + duration.
A moving `now + 5 hours` estimate is not a fixed reset or successful activation.

Retain a durable inflight/uncertain record on a timeout, crash, unknown save or
missing completion. Never resend an uncertain request automatically. An unresolved
cleanup target also holds another request.

Verify and archive only that completed disposable chat. Archiving retains data;
it does not delete the chat or prove disk space was reclaimed.
Require a later scheduled read-only check to retain the consumed permit, completed
result, fixed anchor, pre-send proof and exact cleanup evidence without sending
again. Then return the same task to normal expiration checks. The initialization
permit stays consumed; routine later opportunities use their own window marker.

## Keep it efficient

Update the same account's cloud task for the next verified reset plus two minutes.
Verify its saved prompt and next wake. Do not create another task each run.
Keep the schedule-owning controller responsible for rearming if a delegated
worker lacks permission to update that task. The worker returns the completed
result and verified anchor; the controller updates the existing task and reads
back its enabled state, prompt and next wake. A suggested wake time is not proof
that scheduling succeeded.
Routine automatic checks still require an expired verified fixed anchor and all
current account/spending gates. A future fixed timer means wait.

If a read fails with no known eligible boundary, rearm the same task with bounded
read-only backoff: 1, 2, 4, 8, then at most 12 hours. Notify on a meaningful result,
failure or required sign-in, not on every unchanged hold. A sign-in prompt needs
the owner; preserve state while waiting.

An ordinary timer wake is separate from detecting an unexpected global reset.
This recipe does not include a verified push connection from the public tracker
to the dot. Periodic feed checks can lag; they must not be advertised as immediate
alerts. Direct site notifications to the owner are a separate service. See
[the tested source capabilities](VALIDATION.md#global-reset-notifications).

There is no extra hosting or API bill required within an existing eligible plan's
included allowances. Work/Codex tasks still consume their normal allowance. One
short prompt and one OK minimize request count and requested output; total cloud
task overhead and the universally cheapest model have not been benchmarked.

The optional [Python/CLI path](CLI_SETUP.md) is for offline planning and
read-only metadata. It is not the cloud browser dispatcher. The experimental CLI
execution route stays disabled until its warm-up and quota behavior are verified.


Scheduled initialization, later state readbacks, and the following normal
five-hour cycle passed. See [validation evidence](VALIDATION.md) for the checks.
This establishes the observed unattended cycle, not months of operation or
forced-container-restart recovery.
