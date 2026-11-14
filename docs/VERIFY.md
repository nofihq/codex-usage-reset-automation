# Verify your Dot setup

Test one account first. A saved task, a foreground check and a real scheduled
run prove different things. Use the next eligible window for any real request.

## 1. Read-only setup and recovery

- Dot uses its cloud computer. Confirm that the pinned reader and
  [planner](PLANNER.md) are available after a later scheduled wake.
- Confirm the browser and authenticated CLI separately match the selected account.
  Verify the account actually returns the selected 300- or 10,080-minute window.
- Check that both account and optional alerts Pages are owner-only. A fresh full
  block and current hash support a guarded edit and exact readback. A stale
  write fails without replacing a winning write or touching unrelated fields.
- Observe a genuine scheduled state-only wake on the intended account task.
  It reads the Page and retains native recurrence without an account probe.
  A retryable read may retry once; a denied or missing Page holds.
- In a simulation, check that missing/truncated state, early and stale wakes,
  unknown native provenance and conflicting schedules cannot submit. A
  recovered native fallback stages a later read-only eligibility run; prove
  that later wake separately. Existing claims and review holds survive.
- Confirm task identity, mode, destination, enablement and actual next wake
  after any update. For existing tasks, follow [recovery](RECOVER.md) and keep
  the original state through cutover.

## 2. One eligible activation

- Use the exact authorized account, a live eligible opportunity and a fresh
  scoped claim. Verify the browser spending and model controls in the actual
  final composer: no purchased credits, reload off, included model, minimum
  reasoning and Fast off. Stop on real or ambiguous access restrictions.
- Observe one completed exact `OK`, two authenticated target reset reads at
  least 60 seconds apart, a fixed window start consistent with that request,
  and archive readback for the exact disposable chat. An uncertain outcome
  holds even if the wake or tool call is repeated.
- Verify the actual next ordinary deadline is the fixed reset plus two
  minutes. Verify the same native timer also retains its fallback recurrence.
  If an earlier expiry reminder is pending, verify that earlier wake and
  check the normal deadline remains in private state.
- Observe a later genuine ordinary run under the standing workflow. A
  one-time approval, saved preference or successful foreground request
  does not establish ordinary unattended operation.

## 3. Source and expiry alerts

- After verifying the subscription, exact authenticated sender and enabled
  filter, wait for a genuine matching email to wake the native Gmail task.
  Run now or manual mail reads do not prove automatic delivery.
- Test forecast, confirmed global, and banked classification with fixtures.
  A forecast does not consume the confirmation notice. A repeated message
  or stable same-stage event must not repeat the notice or account handoff.
  If the account Page is held but the alerts Page is readable, public notices
  still work and personal checks are explicitly unverified.
- Verify the personal inventory has real per-grant expiry timestamps.
  Simulate before/at/after the 72-hour and 24-hour deadlines, late discovery,
  unknown expiry, removed grants, indistinguishable grants, and uncertain
  alert delivery. Check both accounts if configured. A due reminder is read-only
  and must not overwrite the ordinary deadline or rearm a time in the past.
- When only the native repeat can be retained, check the saved warning threshold
  against the first calculated repeat after it. Verify an actual scheduled run
  processes the existing warning claim before account work. A calculated wake is
  distinct from a saved next-wake readback and an accepted notice.
- Check device push separately from a saved task or a posted Dot message.
  Record actual dispatch delay when observed. Do not change a real expiry,
  replay a public alert into production, or redeem a grant just to test.

## Check another device

Open the same Dot from another supported browser or the mobile app. Check that
the same tasks and results are visible, with no dependence on a personal device
being on. Seeing a result on another device does not prove it got a push alert.
