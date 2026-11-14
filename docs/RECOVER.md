# Repair an existing Dot setup

Use this if a task says the Page ledger is unavailable, repeatedly wakes in
fallback, or alerts arrive without account results. Work on Dot's cloud computer.
This repair needs no access to your Linux, Windows or Mac files.

1. In **Scheduled → Your dot**, inspect the existing account timers and Gmail
   task. Keep their identities. Record the observed mode, next wake and latest
   result. Do not click Run now to see if a prompt goes through.
2. Keep both account tasks in service-only mode until their existing canonical
   Page is readable and guarded state is verified. Inspect the exact error.
   A retryable service failure gets one bounded retry and retains the native
   repeat. A size issue uses a supported full or exact-block read. Missing or
   denied access needs a supported owner repair; preserve the original Page and
   every unresolved request. A foreground read alone does not prove timer access.
3. Update the pinned source and replace stale task instructions with the shorter
   [controller](../prompts/CONTROLLER.md). Preserve account bindings, anchors,
   claims, consumed permits, holds, pending expiries and native deadlines. Do not
   overwrite a legacy ledger with a generated blank one. Retain the source
   intact if any data cannot be migrated. A stopped timer stays stopped unless
   its owner resumes it.
4. Give the Gmail handler its separate owner-only alerts Page. Copy its
   public-event deduplication records with verified readback before cutover. If
   the old state cannot be read, keep the existing event task and direct source
   alerts; do not assume old events were never sent. Prove a new native delivery
   independently of the account tasks. Personal reconciliation still needs
   fresh account state.
5. Verify a real scheduled read and guarded test on one account. Then verify a
   separate recovery wake and an eligible ordinary cycle, with one exact
   reply and the next deadline read back. Start with the five-hour timer if that
   is the first configured account. Add or restore the weekly timer separately.
   Never run an extra request solely to prove recovery.
6. Verify saved expiry reminders with simulated dates and check real notification
   delivery separately. No fake live grant, changed expiry or banked redemption.

## Isolate the cloud runtime

If the original timer cannot be edited safely, a single standalone native Dot
test can distinguish a broken cloud runtime from a broken account workflow.
Schedule it once, with the result in the Dot conversation. Do not reuse the
account's schedule, Page, browser session or CLI credentials. At the actual
scheduled wake, have the task confirm it is on Dot's cloud computer, print a
harmless marker using the terminal, and check only for Python and the pinned CLI
entry point. No sign-in, model request or account read. Preserve the actual
error if execution fails, and do not report a saved schedule as a passed test.
If the saved task inherits its execution environment and the run cannot verify
that it is cloud-only, stop before executing a command.

If the test passes, return to the original account timer and verify its own
read-only execution and private account binding. A standalone test does not
inherit the account timer's permissions or clear an earlier refusal.

If a scheduled run has no terminal, check whether the supported attach action
for Dot's existing cloud computer is available in that run. The browser panel's
Ready label is not shell evidence. Qualify the attachment and one harmless
command from the original timer itself; a foreground success cannot prove it.
An overdue or early run is not a reason to press Run now or send a catch-up
request. Check its original native dispatch and outcome first.

The native executable's version command and the app-server have different
startup requirements. The app-server initializes its local SQLite state even
for a metadata-only session. In an already-authorized, owner-only writable
scratch directory, test with `python3 scripts/smoke_cli.py --binary PINNED_BINARY
--scratch APPROVED_PRIVATE_DIRECTORY` after verifying the binary fingerprint.
The script uses a new empty CLI home under that directory and returns a redacted
result. A missing or read-only runtime calls for a supported execution mode or
runtime repair before testing an authenticated account.

## Repair request

A practical repair request to paste into Dot:

> Use the recovery guide from the reviewed repository revision to inspect my
> existing reset tasks. Work cloud-only. Preserve the original ledger, holds,
> permits, timers and pending reminders. First verify a real scheduled state-only
> wake on the existing five-hour task. Keep the Gmail alerts active where safe.
> Report the exact Page failure and whether the scheduled read passed. Do not
> submit a model prompt during repair or repeat an uncertain request.

If both account wakes reach the Page service but it keeps returning an error,
the platform still needs to restore access. Direct
[Codex Reset alerts](https://notify.codex-reset.com/) cover public announcements
while that is being repaired. They cannot see personal banked-reset expiries.
