# Codex Usage Reset Automation

A cloud-dot setup for checking Codex usage, sending one short `OK` when eligible,
and keeping the next reset check scheduled. It runs on the dot's cloud computer,
so your own device can be off.

**Use it from Windows, macOS or Linux through a supported desktop browser, or
from the ChatGPT mobile app.** No local CLI, Python, Node, server or API key is
needed on your device. Inside its cloud computer, the dot uses the official
Codex CLI and a small Python reader for exact usage/reset data. Its cloud browser
handles the `OK` request, account selection and spending checks. Mobile web is not
supported.

## What it does

- Checks the selected account and its actual usage windows.
- Saves reset times and duplicate protection in a private Page.
- Verifies a completed `OK`, checks its fixed reset twice, and archives that chat.
- Schedules the next account check and reacts to reset-alert emails through Gmail.

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

Cloning downloads the guides and prompts. Each person must configure their own dot,
logins, private Page and cloud tasks; none of the owner's account state is included.

## How it is organized

| File | Purpose |
|---|---|
| [Setup](docs/SETUP.md) | One account first, Gmail alerts, then an optional second account |
| [Cloud tools](docs/CLOUD_TOOLS.md) | Install and sign in to the usage reader inside the dot's computer |
| [Native CLI](docs/CLI.md) | Optional Windows, macOS and Linux usage-reader commands |
| [Verify](docs/VERIFY.md) | Check your own setup, scheduled run and email-trigger delivery |
| [Controller prompt](prompts/CONTROLLER.md) | Instructions for the cloud coordinator and account checks |
| [Security](SECURITY.md) | Credentials, private state and request safeguards |

Email is event-driven after delivery, but the source can delay emails. An enabled
trigger is not proof of live delivery. Keep ordinary account timers independent
of the email trigger. The included reader runs inside the dot's cloud computer;
it does not schedule tasks or send `OK` itself.
