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
- Guarded Page writes change only intended fields, preserve unrelated state and
  read back exactly; a stale write fails without overwriting.
- A Page size-limit/no-content error holds. A supported full or canonical-block
  read recovers the complete state and current hash; it never recreates the ledger
  or clears reservations, uncertainty or reminder history.
- A later scheduled canary reads and updates that same Page without local receipts.
- Repeated state-only updates do not nest full previous health/ledger snapshots.
  Existing history, claims and uncertainty stay intact. The task prompt has one
  current wake mode rather than accumulated obsolete run instructions.
- Current health is timestamped and separate from prior success. An infrastructure
  failure remains a hold until its recovery is verified; a foreground read alone
  does not qualify unattended execution. Preserve earlier receipts and distinguish
  metadata recovery from a completed normal cycle.
- The saved account task is enabled, names the intended account and private ledger,
  and its actual next wake is visible in a native task receipt or settings.
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
| Model selection | The fresh composer selects the authorized included model, minimum reasoning and Fast off; real restrictions hold, while hidden accessibility text alone is not a global lock |
| Request count | One attempt; no automatic retry or renewed initialization permit |
| Completion | Response exactly `OK`, visibly completed |
| Reset | Two read-only CLI status checks at least 60 seconds apart; same duration and reset, with no second prompt |
| Timing | Reset minus duration falls within the send-to-completion observation interval |
| Cleanup | That exact disposable chat is archived and can be identified as the completed chat |
| Next wake | Same account timer enabled for the verified reset plus two minutes, or an earlier read-only expiry reminder that preserves that normal deadline |
| Persistence | A later scheduled wake retains the result, reservation proof, anchor and cleanup |

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

Check recovery from a different enabled model in an empty composer, not only from
settings left by a foreground test. If preparing that starting state deliberately,
label it a test fixture; do not change account-wide defaults or fabricate a lock.
The scheduled check must verify the selected model and actual visible control state
without generating a request.
For an authorized global-reset start, verify independent reset confirmation,
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

Task enablement, automatic email delivery and device notifications are separate
checks. Record each result accurately; a saved trigger alone does not establish
delivery. Device notifications also require your ChatGPT notification settings.

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
