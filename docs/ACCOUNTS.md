# Separate official sign-in for each alias

Offline commands do not need Codex or authentication. Only use these optional
steps when you want to read **your own** subscription metadata. This project does
not automate sign-in. Use a separate new Codex home for every account; do not copy
an existing credential store or point an alias at your usual `.codex` home.

1. Install the official CLI using [OpenAI's CLI guide](https://learn.chatgpt.com/docs/cli).
2. Create a private home for the `plus` alias:

   ```bash
   mkdir -p "$HOME/.local/share/codex-optimizer/accounts"
   install -d -m 700 "$HOME/.local/share/codex-optimizer/accounts/plus"
   ```

3. Run official sign-in in a child process selecting that new home:

   ```bash
   env CODEX_HOME="$HOME/.local/share/codex-optimizer/accounts/plus" codex -c 'forced_login_method="chatgpt"' login
   ```

   Confirm the intended account in the browser. If it is already signed in to a
   different account, change browser identity during this interactive flow. Do
   not use API-key sign-in, personal access tokens, or pasted access tokens.

4. On a headless host, where available, use official device-code sign-in:

   ```bash
   env CODEX_HOME="$HOME/.local/share/codex-optimizer/accounts/plus" codex -c 'forced_login_method="chatgpt"' login --device-auth
   ```

   Device-code support can require a setting in the account/workspace. If it is
   unavailable, stop and resolve official sign-in on that host. Do not copy
   credentials from another device as a workaround. See [official authentication](https://learn.chatgpt.com/docs/auth#login-on-headless-devices).

5. Repeat with a **different** home ending in `pro`, confirming the second account
   interactively. Neither flow should select your normal Codex home.
6. In ignored `config.json`, set each `codex_home` to its matching directory and
   run `python3 -m optimizer check --config config.json`.
7. Run `python3 -m optimizer probe --config config.json --alias plus`. Find
   `limits.account_identity_hash`; after confirming the sign-in identity, put
   that 16-character value into this alias's `expected_account_id_hash`. Repeat
   for `pro`. Missing/null identity means hold; never substitute a guessed value.
8. `python3 -m optimizer dry-run --config config.json --read-accounts` obtains
   read-only metadata and connects it to the planner. No live requests can run.

Homes accept `~` and resolve relative paths against the configuration file's
parent, so moving the current working directory does not select a different
login. CLI status/feed input paths remain relative to the invocation directory;
use absolute paths outside the clone. Each alias needs distinct homes.

The [AppServer methods](https://learn.chatgpt.com/docs/app-server#auth-endpoints)
used are `account/read`, `account/rateLimits/read` and `model/list` after initialization.
The probe does not log raw server messages, email addresses, tokens or reset
inventories. It emits a short account hash, bounded windows, booleans and model
IDs. Do not upload actual output to the repository or an issue. Installed Codex
may write its own caches/runtime files in the selected home; optimizer read-only
means no model turn, login command, credit purchase or redemption is invoked.

A sandbox/socket permission error is a capability blocker. Do not change unrelated
socket ownership, relax mode 0700, disable sandboxing, or escalate inference.
Version gating rejects unknown releases; review the schema and synthetic tests
before updating the reviewed version list.
