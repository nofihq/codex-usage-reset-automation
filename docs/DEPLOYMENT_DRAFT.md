# Optional scheduling and free cloud setup options

The repository installs **no schedule, service, workflow, cloud resource or secret**.
Every `dry-run` exits after one finite tick. You may later manage a schedule with
an existing free system scheduler on a Linux machine you control. Keep the
command in dry-run/read-only mode and use one persistent private state directory
for the configuration. Do not schedule a model invocation.

For a machine you already have, cron or a systemd user timer can run an installed
command with absolute config/state paths. Test that command interactively first;
a scheduler's PATH and working directory differ from your shell. Poll at most
hourly for personal metadata, respect `next_check_at`, and leave public-feed
polling at four hours. The current finite tick does not enforce personal-account
read cadence for an external scheduler. A sleeping/offline machine misses ticks.
No timer unit or crontab is supplied or modified.

For a free cloud option, evaluate an **existing** Linux host covered by a provider's
free allowance. Verify eligibility and cost controls in that account before
creating anything. This project does not create a host or guarantee any cloud
service stays free. Cloud metadata needs supported official subscription sign-in
on that host, separate account homes, and retained private state. Use interactive
or supported device-code sign-in there; no credential copying from other devices.

GitHub Actions can run offline tests and synthetic checks on a fresh clone within
an eligible allowance. [GitHub billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
describes included usage and account-specific billing. No workflow is shipped.
**Do not import subscription credentials into Actions** or use ephemeral runner
caches/artifacts as authoritative account/idempotency state. It is not the
recommended host for authenticated subscription monitoring in this release.

Only one host may use a state directory. POSIX `flock` is not a distributed lock.
For multiple hosts a separate durable state adapter, lease/compare-and-swap,
concurrency tests and uncertainty recovery would be required; none is implemented.
A cloud adapter would also need supported subscription auth, identity matching,
explicit included-usage permission, and authoritative zero-credit/auto-reload and
inactivity evidence before any hypothetical executor could be considered.

Nothing in this document changes subscription limits, creates quota, guarantees
first-use timer behavior, or enables live dispatch. Keep any existing personal
schedules outside this project's setup and unchanged.
