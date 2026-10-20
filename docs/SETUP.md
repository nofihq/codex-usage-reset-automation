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

Complete email or SMS verification privately in **Open computer**, then return
control to the dot. If the website asks for a **code from the terminal**, the dot
generates and enters that code from its own CLI process. You do not need a local
terminal, and should not paste verification codes into chat.

Saved sign-ins can still require verification later. Recovery must use the same
account's supported sign-in flow and hold requests until its identity is verified
again. This setup runs in the cloud, but it cannot guarantee permanent sign-in
without your involvement.
When adding another account, enter its intended email explicitly. A default SSO
button can reuse the other account. After verification, check the actual signed-in
identity and saved account selector before claiming recovery succeeded.

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
account/window duplicate protection. Keep this authoritative state in the Page
instead of relying on local cloud files.

Before any model request, require the dot to:

1. Read the block and use its returned hash for narrow edits that preserve all
   other state.
2. Verify a stale writer is rejected without changing the winning content.
3. Perform a separate scheduled read/write canary against that same Page.
4. Save and freshly read back an account/window reservation before sending.

Use one saved timer for this account. The task-owning controller must verify each
schedule update; a worker's suggested next time is not a saved schedule.

To review it in ChatGPT on the web, open **Scheduled** and expand **Your dot** in
the sidebar. Open the account task and check its enabled state and next run.
The general Upcoming list may be empty while the dot's tasks are listed separately.

## 4. Verify one eligible request

Authorize one initialization only after confirming the intended account and no
uncertain or competing request. Use a short-lived, account/task/target-scoped
permit with a budget of one. It stays consumed after use; lost state never renews it.
Do not initialize in an already active fixed window or to repair missing history.

Select an included model, minimum available reasoning effort and fast mode off.
Use a fresh disposable chat, no files, project, search or requested tools, and ask:

> Reply with only OK.

Send that prompt **once** and wait for a completed reply exactly `OK`. Then read
the account's usage/reset status through the CLI. Wait at least 60 seconds and
read that status again. These are two read-only checks, not two prompts or two
model requests. Both must show the same reset timestamp for the same window.
Archive that exact completed chat and verify it was archived.

The fixed reset should place the window's start within the send-to-completion
observation interval. A moving `now + duration` estimate fails.

Save the result and rearm the same account timer for the verified reset plus two
minutes. Verify a later scheduled read retains the result and prevents a duplicate.
Routine requests require an expired verified anchor and fresh eligibility checks.
Timeouts, unknown saves or unresolved cleanup hold for reconciliation, never resend.

## 5. Add Tibo reset email alerts

There are two ways the dot knows to check your accounts:

- **Your saved account timer:** wakes after your account's ordinary reset time.
- **A reset email:** wakes when Gmail receives a matching alert about a public
  reset announcement. This is useful when a refill happens outside your normal timer.

The emails come from [Codex Reset](https://codex-reset.com/), an independent
community site that tracks Tibo's ([@thsottiaux](https://x.com/thsottiaux)) reset
announcements. They are not direct messages from Tibo or official OpenAI emails.
The [email service](https://notify.codex-reset.com/) covers global resets,
banked-reset updates and high-confidence forecasts. Their meanings differ:

| Email type | What it means | What the dot does |
|---|---|---|
| Confirmed global reset | A usage refill was reported as applied, rather than merely promised | Verify the source, then check every configured account's actual usage and reset time. An eligible account may proceed through the normal one-request checks; active windows remain protected. |
| Banked-reset update | A reset was announced or saved for later redemption; receiving it is not a usage refill | Keep it separate from a global reset. An account inventory read can check available count and expiry. Never automatically redeem it or send an `OK` because of this email. |
| Forecast, promise or “arriving soon” | A reset may happen later | Do not treat it as completed or send an `OK`. |
| Signup confirmation or welcome | Subscription setup, not a usage event | Verify the subscription only; send no `OK`. |

Follow these steps to connect the emails:

1. Manually subscribe to [Codex Reset email alerts](https://notify.codex-reset.com/)
   using the connected Gmail account. Complete its double opt-in yourself. The
   service [prohibits automated subscription requests](https://notify.codex-reset.com/terms).
2. Let the dot inspect only the source-related email to verify the actual sender
   and authentication. Confirmation alone does not prove the subscription is active.
3. Copy the sender address published on the email service's page and verify it
   against the real message. Create an **incoming Gmail message** event task for
   that exact sender. Keep one sender filter for both global and banked messages,
   without limiting it to the signup email's subject. The dot identifies the
   message type after waking, using the [controller instructions](../prompts/CONTROLLER.md).
4. Keep this event task separate from account timers: an event task cannot also
   have a time schedule. If replacing a poller, verify the replacement is enabled
   and its prompt is saved before disabling the old poller.
5. Verify a genuine email arriving after enablement causes an automatic wake.
   Reading mail manually or pressing Run now does not prove event delivery.

A genuine global-reset email can prompt fresh checks of both Plus and Pro when
both are configured; one email task serves all monitored accounts. Each account
still needs its own identity, allowance and duplicate checks. Do not assume a
public announcement proves a refill reached your particular account.

If you want one eligible `OK` after a confirmed global reset, tell the dot which
accounts are authorized. It must first confirm the reset and each account's refill,
then record permission for at most one request per account for that reset. Previous
history stays saved; a sent or uncertain request in the new reset period blocks
another send. The dot must verify the new fixed reset time afterward. A forecast
or an idle timer alone cannot start it.
The email task records the event and account checks; each account's existing task
handles any eligible request. Accounts sharing the browser take turns.

The first real global-reset email may verify automatic delivery and continue to
the account checks in that same run; the handler must not remain permanently in
setup-only mode. Banked-reset, forecast and confirmation emails never authorize
an `OK`.

The source batches email delivery, so this is not an instant-alert guarantee.
Ask the dot to record source, inbox and wake times where available and distinguish
missing timestamps from measured delay. Notify once about a meaningful confirmed
global reset, new banked-reset availability, completed result, failure or required
action. Label banked announcements as public reports unless your account confirms
the grant. Keep unchanged and duplicate events quiet. Device push notifications
also depend on your ChatGPT notification settings and need their own delivery check.

## 6. Add banked-reset expiry reminders

A banked-reset announcement and an expiry reminder are different notifications.
The announcement says a saved reset may be available. The expiry reminder warns
that a reset actually present in your account is approaching its use-by time.
Do not rely on the public email service to send that personal expiry reminder.

Ask the dot to use your first account's existing task as the reminder coordinator,
including reminders for any second account:

1. Read the account's banked inventory with the reader's `--inventory` option.
   Use the expiry returned for each available reset; do not assume every grant
   lasts 30 days. Unknown expiry means the dot must report that it cannot schedule
   a reliable expiry reminder.
2. Save an early warning for **72 hours before expiry**, plus a follow-up around
   **24 hours before expiry**. The first warning must be planned at least a full
   day ahead. If a reset is first discovered with 24–72 hours left, notify immediately.
   If less than 24 hours remain, notify immediately and say the one-day notice
   could not be met; do not pretend an earlier reminder was delivered.
3. Save this **one-time setup inventory** for each account. Do not schedule daily
   inventory checks. Read inventory again only after a verified new banked-grant
   availability email or your direct request. Ordinary usage checks and expiry
   reminder wakes do not request inventory.
4. Use that **same saved task** for read-only reminder wakes across the
   configured accounts. Its next wake is the earlier of its normal account check
   or any pending expiry warning. Keep every account's normal
   reset deadline saved separately so an early reminder cannot erase it. Other
   account timers keep their own normal schedules. A reminder must not wait behind
   a five-hour, weekly or failure-backoff schedule.
5. Save which account, grant, expiry and warning stage have already been notified.
   Preserve the count when several grants share timestamps. Read this state back
   before sending, keep the notification receipt afterward, and reconcile an
   unknown outcome instead of sending another alert blindly. A restart or repeated
   email must not repeat the same warning.

An expiry notification should name the account, last-verified reset count, exact
expiry in your time zone and time remaining, all based on the saved inventory.
Include when availability was last verified and say **if still unused**; without
another authorized read the dot cannot know whether you redeemed it elsewhere.
Suppress reminders for grants already known redeemed or removed. This is a
reminder for you to decide whether to use the reset: **no automatic redemption,
new inventory probe or `OK` prompt**.

If you redeem one yourself, tell the dot which account and expiry date. It can
stop warnings for a uniquely matching saved grant and record your report without
another inventory check. Ambiguous matches need clarification.

Verify the actual saved wake and warning policy, not just the dot's promise to
remember. Test due-time and duplicate handling with simulated dates; never change
the real expiry to make a test alert look genuine. A saved schedule proves setup,
not device delivery. Keep scheduled, sent and device-delivered evidence separate;
cloud or notification delays can still prevent timely delivery.

## 7. Add a second account

Keep the first account's state and timer. Sign in privately to the second identity,
verify its actual windows and spending controls, and assign a different nickname.
For example, a verified weekly Pro target uses 10,080 minutes.

Add a separate account binding and timer to the same guarded Page. Reuse the one
Gmail event handler to check both accounts, with separate account/window claims.
A hold on one account must not switch identities or bypass the other account's gates.
Do not clone an existing account's credentials, permit or completed-request marker.
Include both accounts in the banked-inventory and expiry-reminder policy.

Finish [verification](VERIFY.md) before calling the new account ready.
