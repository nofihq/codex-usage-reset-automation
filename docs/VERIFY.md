# Verify your setup

Use this checklist for your own dot. Ask it for evidence of each completed step,
not a general “everything works” statement. You can run these checks from Windows,
macOS or Linux in a supported desktop browser; no terminal or local runtime is needed.

## Setup checks

- Execution uses the dot's cloud computer, with no personal-device dependency.
- The selected identity and observed target duration match each account binding.
- Browser and CLI authentication independently identify that account. The cloud
  reader checks the authenticated routing ID against the usage ID; missing or
  mismatched identities hold. A real read-only result passes before enabling sends.
- Included allowance is available, purchased credits are zero and reload is off.
- Guarded Page writes read back exactly; a stale write fails without overwriting.
- A later scheduled canary reads and updates that same Page without local receipts.
- The saved account task is enabled, names the intended account and private ledger,
  and its actual next wake is visible in a native task receipt or settings.

## Account-run checks

Wait for an eligible opportunity; do not create another request just to test an
already active window. For a completed run, require:

| Evidence | Pass condition |
|---|---|
| Before-send proof | A guarded account/window reservation and exact fresh readback before submission |
| Request count | One attempt; no automatic retry or renewed initialization permit |
| Completion | Response exactly `OK`, visibly completed |
| Reset | Two fresh numeric reads at least 60 seconds apart; same duration and reset |
| Timing | Reset minus duration falls within the send-to-completion observation interval |
| Cleanup | That exact disposable chat is archived and can be identified as the completed chat |
| Next wake | Same account timer enabled for the verified reset plus two minutes |
| Persistence | A later scheduled wake retains the result, reservation proof, anchor and cleanup |

Unknown completion, missing state, changed identity or ambiguous cleanup must
produce a hold. Do not clear the record to make a retry possible.

## Email-trigger checks

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

The first genuine reset after enablement verifies the live delivery path. Until
then, report configuration as enabled with delivery unmeasured. Device push
notifications require separate notification settings and actual delivery proof.

## Check another device

Open the same dot from a Windows or macOS desktop browser, or the ChatGPT mobile
app. Ask for a read-only report of the same saved Page, task bindings and next
wakes. They must refer to the same cloud setup; switching devices must not create
new timers, ledgers, sign-ins or model requests. Mobile web is unsupported.
