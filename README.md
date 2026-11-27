# Plus five-hour cloud automation

Dot uses your saved ChatGPT Plus session in its cloud browser to start an idle
five-hour Work/Codex window with one tiny request, then schedules its next check.
Your own computer can be off.

## Set it up

Ask your Dot to install [the activation instructions](prompts/CONTROLLER.md) as
one native cloud task called **Plus five-hour activation**.

1. Sign into your existing Plus account through the private cloud sign-in flow.
   Save the login in the supported private password manager when offered.
   Connect the Gmail mailbox that actually receives that account's login codes,
   so Dot can recover a future expired session through the private sign-in form.
2. Read Plus **Settings → Usage** and its current five-hour reset.
3. Schedule the task for that reset plus two minutes, repeating every five hours.
4. Run an eligible manual test and verify the reply, new reset and saved next wake.
   If the window is already running, verify its timer and wait for the next idle
   opportunity.

Reuse an existing task that does this work. Remove obsolete account-switching,
Pro, ledger and diagnostic automations for this project.

The task uses the saved Plus browser session and keeps a short attempt/result in
its own run conversation. It needs no local installation, CLI, Page ledger,
external server or API key.

## Each activation

Dot verifies the Plus account, the actual five-hour window, remaining weekly
allowance, ordinary included model access, zero purchased credits and auto-reload
off. It uses an enabled included Work model at minimum effort with Fast off.

When the window is idle, Dot sends `Reply with only OK.` once. It confirms the
completed `OK`, reads the new reset twice at least a minute apart, archives the
completed disposable chat, and saves the next wake at reset plus two minutes.
An active window gets another check at its reset. Rounded 100% alone does not
prove idle because newly active usage may round to zero.

An uncertain submission is reconciled from that original chat and Usage before
another request. A sign-in or schedule failure is reported and the task keeps
its existing repeat for recovery. Actual platform review and access restrictions
still apply.

## Tibo/global and banked resets

If wanted, add the existing native Gmail listener using
[the reset-email instructions](prompts/RESET_EMAILS.md). Verify its exact sender
filter for `alerts@notify.codex-reset.com` and keep its native New emails trigger.
This is the [Codex Reset community tracker](https://codex-reset.com/).

| Source stage | Action |
| --- | --- |
| Forecast or promise | One heads-up that a reset is possible |
| Confirmed global report | Check Plus Usage and re-anchor only if its real reset changed |
| Banked announcement | One heads-up that a grant is expected |
| Banked availability | Verify actual Plus grants and update expiry warnings |
| User uses a banked reset | Use the newly verified Plus reset time |

A source report about another plan does not establish Plus eligibility. Receiving
a banked grant does not activate a window. The automation never redeems grants
or buys credits.

Use [one expiry task](prompts/EXPIRY_WARNINGS.md) for available Plus grants, with a
72-hour warning and 24-hour follow-up. Keep its next exact date on the same
one-time task and rearm it after each run. If expiry is displayed to the minute,
schedule one minute early. Warnings include the last verification time and
“if still unused.” Preserve delivered and uncertain stages when inventory changes.

## Verify the cloud setup

- Read back the enabled task, account, full instructions and actual next run.
- Observe one completed eligible `OK` and a new fixed reset consistent with it.
- Observe a real scheduled wake on the same task.
- Test the expiry task's next-date update on that same task, then verify that its
  real warning date and instructions are restored.
- Dry-run forecasts, globals, banked grants, independent redemption, duplicates,
  exhausted weekly allowance and uncertain sends without fabricating source events.
- Check native email delivery and device notifications separately from dry tests.

A saved task or simulated scenario proves setup or logic. Live activation,
dispatch and notification delivery each need an observed result.

Keep credentials and private account/run data out of this public repository.
