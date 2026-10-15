"""Identity gates and real cross-platform subprocess transport, without accounts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cli import read_account_status as reader
from cli.windows_security import private_acl


def responses():
    return {
        'initialize': {},
        'account/read': {'account': {'type': 'chatgpt', 'email': 'test@example.invalid', 'planType': 'plus'},
                         'workspaceRouting': {'chatgptAccountId': 'fixture-binding'}},
        'account/rateLimits/read': {'accountId': 'fixture-binding', 'ordinaryUsageAllowed': True,
            'rateLimitsByLimitId': {'codex': {'limitId': 'codex',
                'primary': {'usedPercent': 0, 'windowDurationMins': 300, 'resetsAt': 2000000000},
                'credits': {'hasCredits': False, 'unlimited': False, 'balance': '0'}}}},
        'model/list': {'data': [{'model': 'gpt-6-luna'}], 'nextCursor': None},
    }


class FakeClient:
    def __init__(self, data=None):
        self.data = responses() if data is None else data
        self.methods = []

    def call(self, method, params):
        self.methods.append(method)
        return self.data[method]

    def initialized(self):
        self.methods.append('initialized')


class IdentityGates(unittest.TestCase):
    def test_correct_binding_and_private_fields_redacted(self):
        data = responses()
        data['account/rateLimits/read']['privateToken'] = 'secret-fixture'
        client = FakeClient(data)
        result = reader.collect(client, {'expectedEmail': 'test@example.invalid'})
        self.assertEqual(result['state'], 'metadata_verified')
        self.assertEqual(result['eligibility'], 'unknown')
        output = json.dumps(result)
        for private in ('test@example.invalid', 'fixture-binding', 'secret-fixture'):
            self.assertNotIn(private, output)
        self.assertEqual(client.methods, ['initialize', 'initialized', 'account/read',
                                         'account/rateLimits/read', 'model/list'])

    def test_identity_failures_stop_before_usage_read(self):
        for change in ('email', 'type', 'missing_email', 'missing_routing', 'missing_binding'):
            with self.subTest(change=change):
                data = responses(); identity = data['account/read']
                if change == 'email': identity['account']['email'] = 'other@example.invalid'
                if change == 'type': identity['account']['type'] = 'apiKey'
                if change == 'missing_email': identity['account'].pop('email')
                if change == 'missing_routing': identity.pop('workspaceRouting')
                if change == 'missing_binding': identity['workspaceRouting'] = {}
                client = FakeClient(data)
                with self.assertRaises(reader.Hold):
                    reader.collect(client, {'expectedEmail': 'test@example.invalid'})
                self.assertNotIn('account/rateLimits/read', client.methods)

    def test_usage_binding_failures_stop_before_model_catalog(self):
        for change in ('missing', 'mismatch', 'nested', 'legacy', 'limit'):
            with self.subTest(change=change):
                data = responses(); usage = data['account/rateLimits/read']
                if change == 'missing': usage.pop('accountId')
                if change == 'mismatch': usage['accountId'] = 'wrong'
                if change == 'nested': usage['rateLimitsByLimitId']['codex']['accountId'] = 'wrong'
                if change == 'legacy': usage['rateLimits'] = {'accountId': 'wrong'}
                if change == 'limit': usage['rateLimitsByLimitId']['codex']['limitId'] = 'wrong'
                client = FakeClient(data)
                with self.assertRaises(reader.Hold):
                    reader.collect(client, {'expectedEmail': 'test@example.invalid'})
                self.assertNotIn('model/list', client.methods)

    def test_missing_expected_identity_prevents_all_rpc(self):
        client = FakeClient()
        with self.assertRaises(reader.Hold): reader.collect(client, {})
        self.assertEqual(client.methods, [])

    def test_bad_numbers_cannot_become_zero_usage(self):
        for bad in (True, -1, 101, float('nan'), float('inf'), '0'):
            with self.subTest(value=repr(bad)), self.assertRaises(reader.Hold):
                reader.sanitize_limit({'primary': {'usedPercent': bad}})
        self.assertIsNone(reader.sanitize_limit({'primary': {}})['primary']['usedPercent'])

    def test_duplicate_json_keys_hold(self):
        with self.assertRaises(reader.Hold): reader.parse_json('{"id":1,"id":2}', 'invalid')

    def test_paged_catalog_remains_informational(self):
        data = responses(); data['model/list']['nextCursor'] = 'private-cursor'
        result = reader.collect(FakeClient(data), {'expectedEmail': 'test@example.invalid'})
        self.assertTrue(result['luna']['morePages'])
        self.assertEqual(result['eligibility'], 'unknown')
        self.assertNotIn('private-cursor', json.dumps(result))

    def test_non_metadata_method_rejected_before_io(self):
        client = object.__new__(reader.MetadataClient)
        for method in ('turn/start', 'thread/start', 'account/login/start', 'account/rateLimitResetCredit/consume'):
            with self.assertRaises(reader.Hold): client.call(method, {})


class PrivateStorage(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Native Windows DACL check')
    def test_windows_public_acl_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = reader.private_directory(Path(temp)/'fixture', create=True)
            # Only this empty disposable fixture is shared, never an account home.
            subprocess.run(['icacls', str(root), '/grant', '*S-1-1-0:(OI)(CI)R'],
                           capture_output=True, check=True)
            with self.assertRaises(ValueError): reader.private_directory(root)

    def test_private_directories_and_expected_identity_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = reader.private_directory(Path(temp)/'private', create=True)
            reader.private_directory(root)
            path = root/'expected.json'
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump({'expectedEmail': 'test@example.invalid'}, stream)
            with path.open('rb') as stream:
                self.assertEqual(reader.read_expectations(stream.fileno())['expectedEmail'], 'test@example.invalid')

    @unittest.skipIf(os.name == 'nt', 'POSIX permissions; Windows DACL has its own native check')
    def test_open_permissions_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root/'open'; path.mkdir(mode=0o755)
            with self.assertRaises(reader.Hold): reader.private_directory(path)
            path.chmod(0o700); link = root/'link'; link.symlink_to(path, target_is_directory=True)
            with self.assertRaises(reader.Hold): reader.private_directory(link)

    def test_windows_acl_policy_rejects_public_and_null_access(self):
        sid = 'S-1-5-21-1-2-3-1000'
        self.assertTrue(private_acl(sid, [(0, sid), (0, 'S-1-5-18'), (0, 'S-1-5-32-544')], sid))
        self.assertFalse(private_acl(sid, [(0, 'S-1-1-0')], sid))
        self.assertFalse(private_acl(sid, [], sid))
        self.assertFalse(private_acl('other', [(0, sid)], sid))
        self.assertFalse(private_acl('S-1-5-32-544', [(0, sid)], sid))
        self.assertTrue(private_acl('S-1-5-32-544', [(0, sid)], sid, file_owner=True))
        self.assertFalse(private_acl('other', [(0, sid)], sid, file_owner=True))


class Transport(unittest.TestCase):
    def test_unreviewed_cli_version_is_rejected_before_server_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = reader.private_directory(root/'home', create=True)
            runtime = reader.private_directory(root/'runtime', create=True)
            version = subprocess.CompletedProcess([], 0, stdout=b'codex-cli 999.0.0\n', stderr=b'')
            with patch.object(reader.subprocess, 'run', return_value=version), \
                 patch.object(reader.subprocess, 'Popen') as start:
                with self.assertRaisesRegex(reader.Hold, 'unsupported_cli_version'):
                    reader.MetadataClient(str(root/'native'), str(home), str(runtime), 1)
                start.assert_not_called()

    def run_transport(self, variant='normal'):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = reader.private_directory(root/'home', create=True)
            runtime = reader.private_directory(root/'runtime', create=True)
            fake = root/'fake.py'; log = root/'log.jsonl'
            fake.write_text('''import json,os,sys
from pathlib import Path
results=RESULTS
for line in sys.stdin:
    request=json.loads(line)
    with Path(LOG).open('a',encoding='utf-8') as stream: stream.write(json.dumps(request)+'\\n')
    if 'id' not in request: continue
    if VARIANT=='auth':
        response={'id':99,'method':'account/chatgptAuthTokens/refresh','params':{'private':'secret-fixture'}}
    elif VARIANT=='bad':
        print('broken secret-fixture',flush=True);continue
    elif VARIANT=='oversize':
        print('x'*1048577,flush=True);continue
    elif VARIANT=='timeout':
        import time;time.sleep(5);continue
    elif VARIANT=='rpc_error':
        response={'id':request['id'],'error':{'message':'secret-fixture'}}
    else: response={'id':request['id'],'result':results[request['method']]}
    print(json.dumps(response),flush=True)
'''.replace('RESULTS', repr(responses())).replace('LOG', repr(str(log))).replace('VARIANT', repr(variant)), encoding='utf-8')
            popen = subprocess.Popen
            observed = []
            def launch(command, **kwargs):
                observed.append((command, kwargs['env']))
                return popen([sys.executable, str(fake)], **kwargs)
            version = subprocess.CompletedProcess([], 0, stdout=b'codex-cli 0.159.2\n', stderr=b'')
            with patch.object(reader.subprocess, 'run', return_value=version), \
                 patch.object(reader.subprocess, 'Popen', side_effect=launch), \
                 patch.dict(os.environ, {'OPENAI_API_KEY': 'secret-fixture', 'CODEX_ACCESS_TOKEN': 'secret-fixture'}):
                client = reader.MetadataClient(str(root/'native-codex'), str(home), str(runtime), 1 if variant=='timeout' else 3)
                try:
                    try: result = reader.collect(client, {'expectedEmail':'test@example.invalid'})
                    except reader.Hold as error: result = {'state':'hold', 'reason':str(error)}
                finally: client.close()
            calls = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()]
            self.assertFalse(client.reader.is_alive())
            return result, calls, observed

    def test_actual_child_transport_and_auth_environment(self):
        result, calls, observed = self.run_transport()
        self.assertEqual(result['state'], 'metadata_verified')
        self.assertEqual([x['method'] for x in calls], ['initialize','initialized','account/read','account/rateLimits/read','model/list'])
        self.assertFalse(calls[2]['params']['refreshToken'])
        self.assertTrue(calls[0]['params']['capabilities']['experimentalApi'])
        self.assertNotIn('OPENAI_API_KEY', observed[0][1])
        self.assertNotIn('CODEX_ACCESS_TOKEN', observed[0][1])
        self.assertIn('forced_login_method="chatgpt"', observed[0][0])

    def test_errors_auth_requests_and_timeouts_stop_without_retry(self):
        for variant in ('auth', 'bad', 'oversize', 'timeout', 'rpc_error'):
            with self.subTest(variant=variant):
                result, calls, _ = self.run_transport(variant)
                self.assertEqual(result['state'], 'hold')
                self.assertEqual(len(calls), 1)
                self.assertNotIn('secret-fixture', json.dumps(result))


if __name__ == '__main__': unittest.main()
