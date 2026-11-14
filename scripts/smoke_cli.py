"""Real official CLI handshake in an empty private home; no account or model use."""
import argparse
import json
import platform
from pathlib import Path
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cli.read_account_status import (
    Hold, MetadataClient, collect, native_binary, private_directory, startup_process,
)


def smoke(binary, scratch):
    methods = []
    class RecordingClient(MetadataClient):
        def call(self, method, params):
            methods.append(method)
            return super().call(method, params)

    temporary = startup_process(
        lambda: tempfile.TemporaryDirectory(prefix='codex-empty-auth-', dir=scratch),
        'smoke_scratch',
    )
    with temporary as temp:
        root = private_directory(Path(temp)/'private', create=True)
        home = private_directory(root/'home', create=True)
        runtime = private_directory(root/'runtime', create=True)
        client = RecordingClient(binary, str(home), str(runtime), 20)
        try:
            try:
                collect(client, {'expectedEmail': 'smoke@example.invalid'})
                raise RuntimeError('An empty home must not have an account')
            except Hold as error:
                if str(error) != 'missing_chatgpt_identity':
                    raise
        finally:
            client.close()
        # Exercise the actual beginner-facing entry point, not only imports.
        entry = Path(__file__).resolve().parents[1]/'cli'/'read_account_status.py'
        setup = subprocess.run([sys.executable, str(entry), '--init-private', str(root)],
                               capture_output=True, text=True, timeout=30)
        if setup.returncode or json.loads(setup.stdout).get('state') != 'private_directories_ready':
            raise RuntimeError('Private-directory CLI setup failed')
        expected = root/'expected.json'
        descriptor = os.open(expected, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump({'expectedEmail': 'smoke@example.invalid'}, stream)
        result = subprocess.run([sys.executable, str(entry), '--binary', binary,
                                 '--home', str(root/'plus'), '--runtime', str(runtime),
                                 '--expectations-file', str(expected)],
                                capture_output=True, text=True, timeout=30)
        if result.returncode != 2 or json.loads(result.stdout) != {
                'state': 'hold', 'reason': 'missing_chatgpt_identity'}:
            raise Hold('unexpected_empty_home_result')
    if methods != ['initialize', 'account/read']:
        raise RuntimeError('Unexpected method sequence')
    print(json.dumps({'ok': True, 'os': platform.system(), 'architecture': platform.machine(),
                      'checks': ['native official binary', 'private setup command', 'CLI entry point', 'empty-home handshake',
                      'unauthenticated identity hold'], 'model_requests': 0, 'sign_ins': 0}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', nargs='?', help='npm installation prefix')
    parser.add_argument('--binary', type=Path, help='existing pinned native Codex executable')
    parser.add_argument('--scratch', type=Path, help='existing approved private scratch directory')
    args = parser.parse_args()
    if args.binary is not None and args.prefix is not None:
        parser.error('pass an installation prefix or --binary')
    try:
        binary = str(args.binary.absolute()) if args.binary is not None else native_binary(
            args.prefix or '.cloud-tools'
        )
        scratch = None if args.scratch is None else private_directory(args.scratch.absolute())
        return smoke(binary, scratch)
    except Hold as error:
        print(json.dumps({'ok': False, 'reason': str(error), 'model_requests': 0, 'sign_ins': 0}))
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
        print(json.dumps({'ok': False, 'reason': 'smoke_failed', 'model_requests': 0, 'sign_ins': 0}))
    return 2


if __name__ == '__main__':
    sys.exit(main())
