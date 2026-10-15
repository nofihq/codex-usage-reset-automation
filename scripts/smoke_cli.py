"""Real official CLI handshake in an empty private home; no account or model use."""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cli.read_account_status import Hold, MetadataClient, collect, native_binary, private_directory


def main():
    methods = []
    class RecordingClient(MetadataClient):
        def call(self, method, params):
            methods.append(method)
            return super().call(method, params)

    binary = native_binary(sys.argv[1] if len(sys.argv) > 1 else '.cloud-tools')
    with tempfile.TemporaryDirectory(prefix='codex-empty-auth-') as temp:
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
    if methods != ['initialize', 'account/read']:
        raise RuntimeError('Unexpected method sequence')
    print(json.dumps({'ok': True, 'checks': ['native official binary', 'empty-home handshake',
                      'unauthenticated identity hold'], 'model_requests': 0, 'sign_ins': 0}))


if __name__ == '__main__': main()
