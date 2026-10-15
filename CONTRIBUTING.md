# Contributing

Keep this repository focused on the cloud setup, controller prompt and verification
steps. User setup must not require a local CLI or an always-on personal computer.
Do not add account data, private run journals or claims based on unobserved outcomes.

Use placeholders in examples. Before submitting, review the diff and run these
maintainer checks with Python 3 and Git:

```sh
python3 scripts/verify_clean_clone.py
```

On Windows, use `py -3` instead of `python3` if that is your Python launcher.
These development checks inspect source and temporary clones only. They do not
sign in, read accounts, create cloud tasks or send model requests.

A change to cloud instructions needs a review against [the verification checklist](docs/VERIFY.md).
Keep request reservation, uncertainty handling, identity/spending gates and exact
archive cleanup intact. Clearly distinguish a saved configuration, a simulated
check and a real scheduled/event-triggered result. Never commit private receipts
as evidence.
