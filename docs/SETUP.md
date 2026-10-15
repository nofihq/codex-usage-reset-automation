# Cloud setup

Start with one account. You will create one private Page, one account timer and,
optionally, one Gmail event task. All execution stays on the dot's cloud computer.
Windows, macOS and Linux use the same steps in a supported desktop browser;
the ChatGPT mobile app can be used too.

## 1. Check the dot's tools

Give your dot the [controller instructions](../prompts/CONTROLLER.md). Ask it to
confirm access to its cloud browser, private Pages, saved cloud tasks and the
account's usage information before doing anything that consumes usage. Follow
[Cloud tools](CLOUD_TOOLS.md) to install the official CLI and status reader on the
dot's computer. You do not install these on your Windows, Mac or other device.

For reset-email triggers, connect Gmail through ChatGPT's plugin settings and
confirm that incoming-message event tasks are available. Availability depends on
your plan and workspace settings. If a required tool is missing, resolve that
before continuing; there is no local-machine fallback in this workflow.

## 2. Sign in to one monitored account

Use the dot's supported private sign-in flow in its **cloud browser**. Complete
MFA yourself when needed. Give the account a nickname such as `plus`; do not use
an email address as a public configuration example.

Authorize the CLI separately using [the cloud sign-in steps](CLOUD_TOOLS.md#sign-in).
A saved browser login does not sign in the CLI. Verify that both contexts identify
the intended account, and that the reader binds authenticated routing identity
to the usage response before reporting numeric data.

Have the dot verify the selected identity, included allowance, zero purchased
credits and automatic reload off. It must select the intended account again on
every wake. Never paste credentials into chat or copy cookies or auth files.

Choose the target by its observed duration. A Plus five-hour target is **300
minutes**; a weekly target is **10,080 minutes**. Confirm the account actually
returns that window instead of inferring it from a plan name.

The remaining-percent heuristic allows checking an account whose target shows
100% remaining, with no exhausted bucket or explicit active work. Percentages
can be rounded: this is not proof that the account is idle. Use it only after
accepting that limitation. Unknown identity, allowance or spending controls hold.

## 3. Create durable state and the account timer

The dot creates one owner-only Page with a canonical JSON block. The saved task
keeps its private Page/block references and account binding. State must include
completed and uncertain requests, fixed reset anchors, cleanup targets and
account/window duplicate protection. Local cloud files are only a cache.

Before any model request, require the dot to:

1. Read the block and use the returned hash for a guarded replacement.
2. Verify a stale writer is rejected without changing the winning content.
3. Perform a separate scheduled read/write canary against that same Page.
4. Save and freshly read back an account/window reservation before sending.

Use one saved timer for this account. The task-owning controller must verify each
schedule update; a worker's suggested next time is not a saved schedule.

## 4. Verify one eligible request

Authorize one initialization only after confirming the intended account and no
uncertain or competing request. Use a short-lived, account/task/target-scoped
permit with a budget of one. It stays consumed after use; lost state never renews it.
Do not initialize in an already active fixed window or to repair missing history.

Select an included model, minimum available reasoning effort and fast mode off.
Use a fresh disposable chat, no files, project, search or requested tools, and ask:

> Reply with only OK.

Require a completed response exactly `OK`, two fresh numeric reset reads at least
60 seconds apart agreeing on the same target and fixed reset, and verified archive
of that exact chat. The fixed reset should place the window's start within the
send-to-completion observation interval. A moving `now + duration` estimate fails.

Save the result and rearm the same account timer for the verified reset plus two
minutes. Verify a later scheduled read retains the result and prevents a duplicate.
Routine requests require an expired verified anchor and fresh eligibility checks.
Timeouts, unknown saves or unresolved cleanup hold for reconciliation, never resend.

## 5. Add reset-email events

1. Manually subscribe to [Codex Reset email alerts](https://notify.codex-reset.com/)
   using the connected Gmail account. Complete its double opt-in yourself. The
   service [prohibits automated subscription requests](https://notify.codex-reset.com/terms).
2. Let the dot inspect only the source-related email to verify the actual sender
   and authentication. Confirmation alone does not prove the subscription is active.
3. Create an **incoming Gmail message** event task for that exact sender. Do not
   restrict it to the confirmation email's subject. Classify message types inside
   the handler, using the [controller instructions](../prompts/CONTROLLER.md).
4. Keep this event task separate from account timers: an event task cannot also
   have a time schedule. If replacing a poller, verify the replacement is enabled
   and its prompt is saved before disabling the old poller.
5. Verify a genuine email arriving after enablement causes an automatic wake.
   Reading mail manually or pressing Run now does not prove event delivery.

A genuine reset event prompts fresh checks of each monitored account. It does
not itself authorize usage. The first real reset email may qualify its event
provenance and continue through the account gates in that same run; the handler
must not remain permanently in setup-only mode. Confirmation, watch/forecast and
banked-reset messages must not trigger an `OK`.

The source batches email delivery, so this is not an instant-alert guarantee.
Ask the dot to record source, inbox and wake times where available and distinguish
missing timestamps from measured delay. Notify on a meaningful reset/result,
failure or required action; keep unchanged and duplicate events quiet.

## 6. Add a second account

Keep the first account's state and timer. Sign in privately to the second identity,
verify its actual windows and spending controls, and assign a different nickname.
For example, a verified weekly Pro target uses 10,080 minutes.

Add a separate account binding and timer to the same guarded Page. Reuse the one
Gmail event handler to check both accounts, with separate account/window claims.
A hold on one account must not switch identities or bypass the other account's gates.
Do not clone an existing account's credentials, permit or completed-request marker.

Finish [verification](VERIFY.md) before calling the new account ready.
