# Verify your setup

Use this checklist to confirm your dot's account setup, scheduled runs and optional
email trigger. You can run these checks from Windows,
macOS or Linux in a supported desktop browser; no terminal or local runtime is needed.

## Setup checks

- Execution uses the dot's cloud computer, with no personal-device dependency.
- The selected identity and observed target duration match each account binding.
- Browser and CLI authentication independently identify that account. The cloud
  reader checks the authenticated routing ID against the usage ID; missing or
  mismatched identities hold. A real read-only result passes before enabling sends.
- Included allowance is available, purchased credits are zero and reload is off.
- The saved scoped rule names the configured account and OpenAI at
  `https://chatgpt.com`, with the intended action behavior. Its text and behavior
  are read back from actual settings; a copied rule or save receipt does not
  replace normal review or a successful scheduled request.
- Guarded Page writes change only intended fields, preserve unrelated state and
  read back exactly; a stale write fails without overwriting.
- A Page size-limit/no-content error holds. A supported full or canonical-block
  read recovers the complete state and current hash; it never recreates the ledger
  or clears reservations, uncertainty or reminder history.
- A denied ledger read blocks account work. Any retry requires a fresh supported
  permission check confirming the same caller's access to that exact Page and
  normal review, with no applicable review denial. It is limited to one retry
  of that read; unclear access or another failure stays held. No sharing change,
  cached ledger or alternate reader is substituted.
- A later scheduled canary reads and updates that same Page without local receipts.
- If enabling the optional delayed service retry, qualify each account task with
  its own scheduled zero-account canary. Verify native deadline restoration
  before the single 15-minute wait, retained cell data and the later original
  full Page read. Do not inject an outage or treat one account's proof as another
  account's qualification. This does not establish restart durability or prove
  the two-error branch has executed during a real outage.
- Repeated state-only updates do not nest full previous health/ledger snapshots.
  Existing history, claims and uncertainty stay intact. The task prompt has one
  current wake mode rather than accumulated obsolete run instructions.
- Live storage has a working-size budget and verified private evidence references.
  If using source layers, exact reconstruction preserves all original fields;
  missing or hash-mismatched source holds. A migration retains the old source,
  keeps all affected tasks held through partial cutover, verifies access and
  current bindings, and preserves claims, unknowns and pending reminders.
  Closed-record rotation is verified before live duplicates are removed; a
  smaller Page alone does not prove that cold scheduled reads now succeed.
- Known large-ledger reads start with the supported full view in every mode.
  Exact request arguments and raw errors survive before content parsing; a missing
  content object cannot become a misleading exception or empty-state inference.
  Check the real size-error/full-read pair without assigning a new error code to
  an earlier unretained response. A read-shape correction grants no wider scope.
- Current health is timestamped and separate from prior success. An infrastructure
  failure remains a hold until its recovery is verified; a foreground read alone
  does not qualify unattended execution. Preserve earlier receipts and distinguish
  metadata recovery from a completed normal cycle.
- The saved account task is enabled, names the intended account and private ledger,
  and its actual next wake is visible in a native task receipt or settings.
- A mode change updates its deadline and read-only/send flags together. Use the
  same consistency check on a contradictory in-memory copy and confirm it is
  rejected without account work or changes to saved state. Read back the real
  state before the next wake. Ordinary-run flags do not waive fresh eligibility
  or permit warm-ups; superseded failed deadlines remain in history.
- An active run and its future fallback retain separate scopes. A state-only
  fallback has zero-request flags even while the original ordinary run remains
  active under its own provenance, gates, ownership and claim.
- Check the existing verified-reset event mode too: its contract retains its
  opportunity key and event deadline separately from the ordinary deadline.
  In-memory event fixtures never establish a real email, refill or send permission.
- After updating a native prompt or schedule, its authoritative current binding
  matches the latest actual native readback. Original run receipts remain
  historical; a new maintenance receipt does not leave a stale current hash.
- A real scheduled wake can use an exposed task reader for repeated full
  configuration checks. An unavailable suggested reader is not a capability
  failure if another supported reader's contract permits those checks. Actual
  access restrictions, API errors and review denials still hold.
- Each existing account timer retains a sparse native recurrence if saving its
  next wake fails. After a real scheduled state-only dispatch, verify that it
  stays enabled with the same recurrence before manually rearming it. A fallback
  occurrence with missing state, uncertain provenance or a hold makes no account,
  browser, CLI, model or inventory calls; it cannot treat an old deadline as
  permission to send.
- Verify that a genuine fallback with recovered ledger access can save and
  independently read back a separate future read-only recovery on the same timer.
  A known active window defers that recovery until its verified reset plus two
  minutes. Check the later recovery and ordinary run separately: a staged wake
  alone does not prove either executed. Preserve review holds, claims and reminders;
  the fallback makes no account or model calls.
- After a transient read failure, an original read-only eligibility run can
  finish its remaining authorized checks after full fresh control reconciliation,
  without repeatedly scheduling the same recovery. It sends no prompt. A fallback
  or failed ordinary wake still needs a separate future eligibility run; changed
  scope, holds and uncertain claims remain blocking.
- The private Page retains the pinned source commit, reader/companion hashes and
  CLI version. Test restoring missing code in a disposable directory, rejecting a
  changed file and preserving existing account bindings. A later scheduled read
  must verify the installation before using it; unexpected code changes hold.

## Account-run checks

Use the next eligible window for this check; do not send an extra request into an
already active window. A completed run must meet these conditions:

| Evidence | Pass condition |
|---|---|
| Before-send proof | A guarded account/window reservation and exact fresh readback before submission |
| Task fallback | Before reservation, the same task has a non-overlapping future state-only fallback, with enabled state, instructions, destination and schedule independently read back |
| Model selection | The fresh composer selects the authorized included model, minimum reasoning and Fast off; exact control/label relationships and rendered evidence distinguish real restrictions from unreferenced hidden text |
| Submit readiness | Settings popovers are closed normally, the intended header and exact prompt are verified, and Send is enabled; unfinished-tab continuity preserves the original claim/proof |
| Request count | One attempt; no automatic retry or renewed initialization permit |
| Completion | Response exactly `OK`, visibly completed |
| Reset | One owned, bounded execution completes both read-only CLI checks at least 60 seconds apart; same duration and reset, with no second prompt |
| Timing | Reset minus duration falls within the send-to-completion observation interval |
| Cleanup | That exact disposable chat is archived and can be identified as the completed chat |
| Next wake | Same account timer enabled for the verified reset plus two minutes, or an earlier read-only expiry reminder that preserves that normal deadline |
| Persistence | A later scheduled wake retains the result, reservation proof, anchor and cleanup |

An owner may separately authorize a bounded live test with an explicit exception
to the activity heuristic. Record its single-use scope and actual outcome apart
from ordinary operation; access, spending, review and duplicate protection still
apply. An unchanged active-window reset can verify the test's status reads, but
does not prove that the test started a new window or that production works.

Unknown completion, missing state, changed identity or ambiguous cleanup must
produce a hold. Do not clear the record to make a retry possible.
Verify that saved recovery permissions allow bounded read-only inspection of the
recorded blocker, while reminder-only wakes make no account or browser probes.
A later scheduled recovery must respect any remaining model lock without sending
a test prompt, even when the metadata reports available usage.

An explicit review denial stays unresolved until a supported correction or approval
path clears it. Service recovery, prompt cleanup and another saved wake are not
execution recovery. Check that blocked wakes preserve reminders without retrying
the denied action or sending duplicate unchanged-blocker notifications.

Check that temporary diagnostic limits remain scoped to their occurrence. A
pending correction must retain existing holds and cannot declare its own review
acceptance. Record the actual returned action result before any dependent change;
an accepted inspection does not resolve a different refused action. A missing
review endpoint must not become an invented clearance token or an endless demand
for the same owner approval.

For human sign-in handoffs, verify that holds and safe schedules were saved before
waiting. Distinguish native wake delivery from actual account execution during
that wait. After a timeout, check fresh signed-in identity, the original caller's
terminal state and its tab against the exposed authentication lifecycle. Preserve
unavailable approval-card status without inventing cancellation or an unknown
model request. Closed scopes stay closed; future work retains the same authorized
total budget, and any live operation or unknown submission remains blocking.

When the browser runtime requires a documentation refresh after context recovery,
verify that any required owner approval covers that exact action and future runs
as intended. Check the original caller's returned documentation and durable policy
readback; another caller's success does not clear its refusal. Documentation-only
approval must leave all account and model-request gates intact.

Check the scope of the accepted correction: diagnostic access and a one-time
qualification are not proof of permission for ordinary recurring operation.
Verify an actual scheduled ordinary run using its saved production instructions,
without a temporary qualification override, and its later durable readback.
Preserve all historical denials and every fresh-run gate.
A cycle that needs a coordinator's message to resume after the first status read
does not qualify as unattended completion, even if its eventual reset and archive
proofs pass. Verify the repaired whole cycle without that intervention.

Check recovery from a different enabled model in an empty composer, not only from
settings left by a foreground test. If preparing that starting state deliberately,
label it a test fixture; do not change account-wide defaults or fabricate a lock.
The scheduled check must verify the selected model and actual visible control state
without generating a request.
Inspection completes in a separate read-only call before any selection. The exact
fresh composer is verified again after an accepted change and retained through
submission; another chat's model settings cannot qualify it. An already-correct
selection needs verification rather than another click. Every action still passes
normal review, and a refusal or unclear restriction holds.
When accessibility text contains a lock warning, verify current computed clipping,
geometry and whole-document ARIA references alongside the selected control and
unaltered screenshot. After normal menu closure, check the same composer's header,
warnings and banners again. The current review packet retains this source evidence,
not just a summary or a previous diagnostic. A restored draft is not an empty
composer or a completed request.
For an authorized global-reset start, verify authenticated source confirmation,
personal refill and a new single-use account/event permit. Old uncertainty must
remain recorded, and any send or unresolved request after the reset blocks a
duplicate. Accounts sharing a browser must run serially.

## Email-trigger checks

The trigger covers Tibo-related global resets and banked-reset updates from the
community email service. A global reset is a reported automatic refill; a banked
reset is saved for later use. Neither an email nor a forecast proves your account
has refilled. See [message types](SETUP.md#5-add-tibo-reset-email-alerts).

Subscription, task configuration and live delivery are separate checks:

1. Confirm the source subscription is active, not just that a confirmation arrived.
2. Verify the exact authenticated sender from real mail. Check the task's enabled
   event configuration and saved production prompt; report fields the service does
   not expose for independent readback.
3. A genuine new source email must cause a native automatic event turn. A manual
   mail read, synthetic replay or Run now is not a substitute.
4. Record receipt/wake times. Do not claim zero delay or exact-minute delivery when
   the source batches emails or timestamps are missing.
5. Replay a handled event: it must not repeat an alert, account reconciliation or
   model request. Confirmation/watch/banked mail must never send an `OK`.
6. A verified reset event checks each account's fresh identity, allowance and timer.
   An active fixed window remains protected even if usage rounds to 100%.
7. An authenticated completed-reset email from the trusted source must not wait
   for a second public announcement. It still cannot substitute for personal
   account checks or clear an unresolved review denial. Ambiguous or forged
   messages stay on hold.

Task enablement, automatic email delivery and device notifications are separate
checks. Record each result accurately; a saved trigger alone does not establish
delivery. Device notifications also require your ChatGPT notification settings.

Check routine notification wording against completed, skipped, blocked and unknown
request outcomes, plus source-only reset reports and saved expiry reminders.
Alerts should be short and identify the account and actual result; technical
evidence stays private. A source report must not say a personal reset was verified,
and an unknown submission must not say the request was definitely unsent. These
wording checks need no extra model requests or duplicate device notifications.

## Banked-expiry reminder checks

- Read actual available inventory and exact expiry for every configured account.
  Do not infer a personal expiry from a public banked-reset announcement.
- Verify this is a one-time setup read, with no daily inventory task or deadline.
  Further inventory reads require a new verified banked-grant event or owner request.
- Verify the saved early-warning deadline is 72 hours before expiry, with a
  24-hour follow-up. The first planned notice must be at least 24 hours early.
  Late discovery produces an immediate honest warning, not a claimed past delivery.
- Confirm the designated existing coordinator's actual next wake is the earliest
  of its normal account check or any account's pending warning.
  Read-only reminder wakes preserve normal deadlines and other account timers;
  they cannot send `OK` or redeem anything.
- Reminder-only wakes use saved expiry evidence, make no account probe, and label
  availability with its last verification time and "if still unused" wording.
- A permitted inventory refresh updates the current counts, verification times
  and grant statuses actually consumed by reminders. A result stored only in run
  history is insufficient. Absent grants suppress future warnings, with removal
  reason unknown; accepted receipts and owner-reported redemption stay intact.
- Simulate before/at/after warning boundaries, late discovery, unknown expiry,
  redeemed/removed grants, two accounts, repeated wakes and unknown notification
  outcomes. Accepted stages must not cause another alert or a wake scheduled in
  the past. A new banked-grant email can refresh inventory but cannot send `OK`.
- Check durable per-account/grant/expiry/stage notification state and receipt readback.
  A schedule or simulated pass is not proof a real reminder reached your device.

## Check another device

Open the same dot from a Windows or macOS desktop browser, or the ChatGPT mobile
app. Ask for a read-only report of the same saved Page, task bindings and next
wakes. They must refer to the same cloud setup; switching devices must not create
new timers, ledgers, sign-ins or model requests. Mobile web is unsupported.
