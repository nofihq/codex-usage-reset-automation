#!/usr/bin/env python3
"""Explicit interactive official sign-in, isolated per alias on each desktop OS."""
import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from optimizer.__main__ import load_config
from optimizer.platforms import codex_command, private_directory, supported
from optimizer.probe import REVIEWED_VERSIONS, child_environment, installed_version


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--alias', required=True)
    parser.add_argument('--device-auth', action='store_true')
    args = parser.parse_args(argv)
    try:
        if not supported() or installed_version() not in REVIEWED_VERSIONS:
            raise ValueError('Unsupported CLI/runtime')
        config, _, _ = load_config(args.config)
        row = next(row for row in config['profiles'] if row['account_id'] == args.alias)
        home = private_directory(row['codex_home'])
        command = codex_command()+['-c', 'forced_login_method="chatgpt"', 'login']
        if args.device_auth:
            command.append('--device-auth')
        # Human completes official sign-in; no auth file is opened or copied here.
        return subprocess.call(command, env=child_environment(home), cwd=home)
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        print('Sign-in setup unavailable. Check CLI version, alias and private account folder locally.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
