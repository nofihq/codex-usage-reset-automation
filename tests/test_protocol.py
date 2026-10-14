"""Exercise actual stdio transport using a synthetic local Codex executable."""
from helpers import private_temp
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from optimizer.probe import ProbeError, ReadOnlyClient, identity_hash, probe, status_from_report


class Protocol(unittest.TestCase):
    def fake_codex(self, temp, variant='normal'):
        root=Path(temp); executable=root/'fake_codex.py'; log=root/'requests.jsonl'
        results={'initialize':{}, 'account/read':{'account':{'type':'chatgpt','email':'private@example.invalid'}},
                 'account/rateLimits/read':{'accountId':'fixture-account','ordinaryUsageAllowed':True,
                     'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':0,'windowDurationMins':300,'resetsAt':2000000000},
                         'credits':{'hasCredits':False,'unlimited':False,'balance':'0'}}}},
                 'model/list':{'data':[{'model':'fixture-model'}],'nextCursor':None}}
        script='''#!/usr/bin/env python3
import json,sys,time
from pathlib import Path
if '--version' in sys.argv:
    print('codex-cli 0.159.2'); sys.exit(0)
results=RESULTS
for line in sys.stdin:
    msg=json.loads(line)
    with Path(LOG).open('a') as out: out.write(json.dumps(msg)+'\\n')
    if 'id' not in msg: continue
    method=msg['method']
    if VARIANT=='stall':
        time.sleep(60); continue
    if VARIANT=='refresh':
        print(json.dumps({'id':99,'method':'account/chatgptAuthTokens/refresh','params':{'token':'secret-fixture'}}),flush=True)
        continue
    if VARIANT=='malformed':
        print('not json',flush=True); continue
    if VARIANT=='oversized':
        print('x'*262145,flush=True); continue
    if method not in results: sys.exit(3)
    print(json.dumps({'id':msg['id'],'result':results[method]}),flush=True)
'''
        script=script.replace('RESULTS',repr(results)).replace('LOG',repr(str(log))).replace('VARIANT',repr(variant))
        executable.write_text(script); executable.chmod(0o700)
        home=root/'isolated-home'; home.mkdir(mode=0o700)
        return home,log,executable

    def test_real_transport_and_exact_method_sequence(self):
        with private_temp() as temp:
            home,log,executable=self.fake_codex(temp)
            with patch('optimizer.probe.codex_command',return_value=[sys.executable,str(executable)]): result=probe(home)
            self.assertEqual(result['models_read'],'completed')
            status=status_from_report('alias',identity_hash('fixture-account'),result)
            self.assertIsNotNone(status); self.assertIsNone(status.active_work)
            calls=[json.loads(row) for row in log.read_text().splitlines()]
            self.assertEqual([row['method'] for row in calls],['initialize','initialized','account/read','account/rateLimits/read','model/list'])
            self.assertTrue(calls[0]['params']['capabilities']['explicitGatewayOauth'])
            self.assertFalse(calls[2]['params']['refreshToken'])
            self.assertTrue(calls[3]['params']['excludeResetCreditDetails'])
            self.assertNotIn('private@',json.dumps(result))

    def test_refresh_bad_framing_and_oversize_stop_without_authentication(self):
        for variant in ('refresh','malformed','oversized'):
            with self.subTest(variant=variant), private_temp() as temp:
                home,log,executable=self.fake_codex(temp,variant)
                with patch('optimizer.probe.codex_command',return_value=[sys.executable,str(executable)]): result=probe(home)
                self.assertEqual(result['account_read'],'not_attempted')
                self.assertEqual(result['model_requests_sent'],0)
                self.assertEqual(len(log.read_text().splitlines()),1)
                self.assertNotIn('secret-fixture',json.dumps(result))

    def test_timeout_closes_child_and_pipe_reader(self):
        with private_temp() as temp:
            home,_,executable=self.fake_codex(temp,'stall')
            with patch('optimizer.probe.codex_command',return_value=[sys.executable,str(executable)]), patch('optimizer.probe.CALL_TIMEOUT',0.05):
                client=ReadOnlyClient(home)
                try:
                    with self.assertRaises(ProbeError): client.call('initialize',{})
                finally: client.close()
                self.assertIsNotNone(client.process.poll())
                self.assertFalse(client.reader.is_alive())

    def test_non_read_methods_prohibited_before_process_io(self):
        client=object.__new__(ReadOnlyClient)
        for method in ('turn/start','account/login/start','account/rateLimitResetCredit/consume'):
            with self.assertRaises(ProbeError): client.call(method,{})


if __name__=='__main__': unittest.main()
