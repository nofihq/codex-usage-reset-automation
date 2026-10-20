# Codex Usage Reset Automation

A cloud-dot setup for checking Codex usage, sending one short `OK` when eligible,
and keeping the next reset check scheduled. It runs on the dot's cloud computer,
so your own device can be off.

After setup, saved cloud tasks handle usage checks, eligible requests and reminders
automatically. No always-on device, extra hosting or API key is required. Duplicate
events stay quiet; meaningful results, failures and required actions are reported.

The goal is to start an eligible new usage window with a tiny request rather
than wait until you next need to work. The dot checks the reset time returned by
your account; it does not create extra allowance or reset usage itself.

**Use it from Windows, macOS or Linux through a supported desktop browser, or
from the ChatGPT mobile app.** No local CLI, Python, Node, server or API key is
needed on your device. Inside its cloud computer, the dot uses the official
Codex CLI and a small Python reader for exact usage/reset data. Its cloud browser
handles the `OK` request, account selection and spending checks. Mobile web is not
supported.

## What it does

| Part | Job |
|---|---|
| Official CLI + Python reader | Read and validate account identity, usage and numeric reset times |
| Dot's cloud browser | Verify the selected account and spending controls, send the eligible `OK`, then archive its exact chat |
| Private Page + cloud tasks | Preserve duplicate protection and schedule the next check |

The CLI is used only for reads in this workflow. Browser and CLI sign-in are
separate; follow the private authorization steps for each. If a session expires,
the dot must stop and request sign-in instead of guessing or retrying a request.

### One prompt, then two usage checks

1. When the account passes its checks, send **one** prompt: `Reply with only OK.`
2. After the reply finishes, read the account's usage and reset time through the CLI.
3. At least 60 seconds later, read that status again. Both reads must show the same
   reset time for the same usage window. **This does not send another prompt.**
4. Archive the completed chat and schedule the next check for that reset time
   plus two minutes. Save the result so another wake cannot send a duplicate.

An earlier banked-expiry reminder wake is read-only and keeps that normal
account deadline intact.

For example, if both status reads show a reset at 7:00 p.m., the next check is
scheduled for 7:02 p.m. The pause between reads checks that the reset time stays
fixed instead of moving forward every time it is read.

### Tibo reset emails

The optional email setup follows [Codex Reset](https://codex-reset.com/), an
independent community tracker of reset announcements associated with Tibo
([@thsottiaux](https://x.com/thsottiaux)). These are community-service emails,
not emails sent directly by Tibo or OpenAI.

- **Global reset:** a reported automatic usage refill. The dot checks each
  configured account, such as Plus and Pro, to see what actually changed before
  considering an `OK`. An email alone never permits an extra request.
- **Banked reset:** a reset saved in your account for you to redeem later.
  Receiving one does not refill usage immediately. The automation never redeems
  it or sends an `OK` just because a banked-reset email arrived.
- **Forecast or promise:** a possible future reset, not a completed refill.
  It must not trigger an `OK`.

Your normal account timer still works without these emails. See
[email setup and message types](docs/SETUP.md#5-add-tibo-reset-email-alerts)
for signup, Gmail and notification details. Email can arrive late; it is not an
instant-alert guarantee.

### Banked-reset expiry reminders

Configure a **72-hour early warning and a 24-hour follow-up** for available banked
resets, using the expiry shown by your account. This gives you at least a day's
planned notice when the expiry is known early enough. The same cloud task handles
these read-only reminders for each account; no extra `OK` or automatic redemption.
Read inventory once during setup, then use the saved expiries without daily checks.
A verified new banked-grant email or your direct request can cause another inventory
read. Reminders say when availability was last checked and are conditional on the
reset still being unused.
The dot must warn immediately if it discovers an expiry too late for one-day
notice. See [reminder setup and checks](docs/SETUP.md#6-add-banked-reset-expiry-reminders).

### What it checks and records

| Information | Meaning |
|---|---|
| Account and plan | Confirms the browser and CLI refer to the account you configured |
| Usage used and remaining | Reads `usedPercent`; remaining is `100 − usedPercent` |
| Window length | Reads the actual duration, such as 300 minutes or 10,080 minutes |
| Reset time | Reads the server's timestamp; time until reset can be calculated from it |
| Spending controls | Checks included usage, purchased-credit balance and automatic reload before sending |
| Banked resets | One setup `--inventory` read records count, status, grant time and known expiry; refresh only after a verified new grant event or your request, with no daily checks |
| Run result | Saves the request attempt, completed reply, two reset checks and exact-chat archive result |
| Next check | Saves and verifies the next wake for each account |
| Expiry reminders | Saves per-account banked expiry, warning times and notification status to avoid repeated alerts |
| Email handling | Records handled events and available source, inbox and wake times to avoid duplicates and measure delivery delay |

These checks do not measure an exact token cost or prove how much usage the
automation saves. A short reply keeps output small; normal plan usage still applies.

The workflow uses your normal included allowance; it does not add quota.
Archiving hides a chat from Recents and retains its data.

## What you need

- [Eligible dot access](https://learn.chatgpt.com/docs/dots#access), with a cloud
  browser, private Pages and cloud tasks. Plus alone is not currently listed as
  dot-eligible; it can still be a monitored account owned by someone with access.
- An account you own, with included usage available, purchased credits at zero
  and automatic reload off.
- A connected Gmail account if you want reset-email triggers.

No extra hosting or API billing is required. Work/Codex tasks still use their
normal plan allowances. The small prompt limits output; it does not make total
usage zero or establish the cheapest possible model.

## Set up one account

1. Open **Your dot** in a supported app or desktop browser.
2. Give it this repository URL and paste:

   > Follow this repository's cloud setup guide. Set up one account in your cloud
   > environment, with private sign-in, a guarded Page ledger and one saved account
   > timer. Explain the 100%-remaining activity heuristic before using it. Set up
   > the Gmail reset-email trigger if available. Use no connected personal computer,
   > paid credits or API-key fallback. Verify each setup step and report any missing
   > permission, tool or live-delivery proof. Do not repeat an uncertain request.

3. Follow [the setup guide](docs/SETUP.md) to sign in and subscribe to alerts.
4. Complete [the verification checklist](docs/VERIFY.md). Add another account only
   after the first account works.

You can read everything on GitHub; cloning is optional:

```sh
git clone https://github.com/nofihq/codex-usage-reset-automation.git
cd codex-usage-reset-automation
```

Cloning downloads the reader, guides and controller instructions. Follow the setup
guide to connect your own accounts and create your private Page and cloud tasks.
Personal account state and credentials are not included.

## How it is organized

| File | Purpose |
|---|---|
| [Setup](docs/SETUP.md) | One account first, Tibo global/banked-reset emails, then an optional second account |
| [Cloud tools](docs/CLOUD_TOOLS.md) | Install and sign in to the usage reader inside the dot's computer |
| [Native CLI](docs/CLI.md) | Optional Windows, macOS and Linux usage-reader commands |
| [Verify](docs/VERIFY.md) | Check your own setup, scheduled run and email-trigger delivery |
| [Controller prompt](prompts/CONTROLLER.md) | Instructions for the cloud coordinator and account checks |
| [Security](SECURITY.md) | Credentials, private state and request safeguards |
