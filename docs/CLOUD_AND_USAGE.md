# Cloud access, minimal usage and small storage

The project aims to keep useful reset windows moving with as little overhead as
possible. Today's release saves verified window reset times and usage percentages,
plans finite read-only checks, and keeps state small. The scheduled Plus test must
establish timer behavior before the repository grows a live OK executor or dot setup.

## Your Windows account and the cloud

Review of the existing dot conversation found this reported working path:
cloud CLI for account/status reads, then cloud browser Work for manual test
messages. The dot reported that neither personal computer was needed. CLI-only
message sending hit a cloud runtime error; browser Work was the successful path.
The tiny tests did not change the displayed whole-percentage weekly usage, which
means the cost was below display precision, not that the messages were free.
Test windows were already active, so these runs did not prove first-use timer
anchoring. Test chats were reported archived.

This is separate environment-specific evidence, not a shipped cloud dispatcher.
No private account IDs, output, credentials, chat links or reset inventory are
included here. The pending Plus run and existing dot schedules are unchanged.

The operating system used to view a cloud task does not determine the cloud
runtime's operating system. You can access cloud results from Windows, macOS or
Linux; the cloud host still needs its own working authentication and runtime.
OpenAI's [dot task documentation](https://learn.chatgpt.com/docs/dots/tasks-and-memory#assigned-work)
explains that cloud coding tasks can run with the computer offline, while tasks
on a connected computer require that computer online with the app open.

## What "free" means

The Python monitor uses free tooling and has no third-party Python dependencies.
It does not require a paid API key, purchase credits, or fall back to a paid model.
The tested personal cloud route used existing subscription/cloud access instead
of provisioning a paid always-on VPS.

A ChatGPT subscription, dot/cloud availability and usage allowances still apply.
The repo does not provide hosting or promise an unlimited free cloud service.
A local scheduler only runs while its host is online. A cloud deployment can keep
working with your laptop off if its execution, credentials and durable state all
stay in the cloud. That reusable deployment remains deferred; see
[deployment options](DEPLOYMENT_DRAFT.md).

## Minimal usage by design

- Offline checks and dry-run planning make zero model requests.
- Optional account probes use official read-only methods; they do not start a turn.
- Actual window reset times are saved in private state. The planner returns the
  next check time rather than asking a model to inspect an active window repeatedly.
- Public reset hints are deduplicated; enabled feed polling defaults to four hours.
- Active usage or exhausted weekly buckets hold hypothetical disposable requests.
- Future OK execution must use a verified model/effort and measure actual before/
  after impact. Its total overhead includes dot supervision and browser context;
  a two-letter reply alone does not establish negligible subscription usage.

The finite tick does not enforce personal-probe cadence for an external scheduler.
Model quota impact of metadata reads has not been independently measured here.
Never equate rounded zero usage with inactivity or a guaranteed zero-cost request.

## Small storage and chat cleanup

Optimizer state is capped at 128 KiB. Logs rotate across four 64 KiB files with
seven-day retention, about 384 KiB total steady optimizer data, plus a temporary
state file during an atomic write. Only structured data is retained; raw public
feed history and session transcripts are not saved by the monitor.

Official CLI binaries, caches, account-home data and cloud chats have their own
storage outside these bounds. Do not advertise this as zero disk usage.

Archiving disposable chats can keep the sidebar tidy. It **does not delete the
chat or reclaim its stored data**; OpenAI's
[chat archiving documentation](https://help.openai.com/en/articles/8809935-deleting-and-archiving-chats-in-chatgpt)
states that archived chats remain in the account until deleted. The repo currently
creates no model chats and implements no automated archiving. Cleanup stays with
the existing personal workflow until the Plus run is verified. A future supported
ephemeral request path would be preferable for avoiding new local transcripts.
