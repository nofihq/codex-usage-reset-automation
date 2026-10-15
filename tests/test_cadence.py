"""Real restart/read-cadence tests using synthetic accounts and no login."""
from contextlib import redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from optimizer.__main__ import main,load_config
from optimizer.cadence import due,fingerprint,record,health_transition
from optimizer.core import Decision,Policy,Profile
from optimizer.storage import Store

ROOT=Path(__file__).resolve().parents[1]
NOW=2000000000


class Cadence(unittest.TestCase):
    def test_repeated_unavailable_reads_have_bounded_backoff_and_recovery(self):
        state={};policy=Policy();decision=Decision('plus','hold','unavailable',NOW+3600)
        next_times=[record(state,decision,False,NOW,policy,'hash')-NOW for _ in range(10)]
        self.assertEqual(next_times[:4],[3600,7200,14400,28800])
        self.assertTrue(all(value<=43200 for value in next_times))
        self.assertEqual(state['read_failures'],8)
        record(state,decision,True,NOW,policy,'hash')
        self.assertEqual(state['read_failures'],0)
        self.assertFalse(due(state,NOW+1,'hash'))
        self.assertTrue(due(state,NOW+3600,'hash'))
        self.assertTrue(due(state,NOW+1,'changed'))
        self.assertTrue(due(state,NOW+1,'hash',force=True))

    def test_health_alerts_only_on_change_and_deadline_is_bounded(self):
        account={}
        self.assertEqual(health_transition(account,False),'account_check_blocked')
        self.assertIsNone(health_transition(account,False))
        self.assertEqual(health_transition(account,True),'account_check_recovered')
        self.assertIsNone(health_transition(account,True))
        decision=Decision('plus','hold','future',NOW+10**9)
        self.assertEqual(record(account,decision,True,NOW,Policy(),'hash'),NOW+30*86400)

    def config(self,base):
        path=base/'config.json'
        data=json.loads((ROOT/'examples/config.single-account.json').read_text())
        data['profiles'][0]['codex_home']=str(base/'synthetic-account')
        path.write_text(json.dumps(data))
        return path

    def tick(self,args):
        out=io.StringIO()
        with redirect_stdout(out): code=main(args)
        return code,json.loads(out.getvalue())

    def test_saved_due_state_skips_real_subprocess_probe_after_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);config=self.config(base);state=base/'state'
            class Fake:
                report={'limits_read':'unavailable'}
                def __init__(self,*args): pass
                def read(self,alias): return None
            now=time.time()
            args=['--config',str(config),'--state-dir',str(state),'--read-accounts','--due-only']
            with patch('optimizer.probe.OfficialStatusAdapter',Fake),patch('optimizer.__main__.time.time',return_value=now):
                code,result=self.tick(args)
            self.assertEqual(code,0);self.assertEqual(result['account_probe_attempts'],1)
            self.assertEqual(result['alerts'],[{'alias':'plus','code':'account_check_blocked'}])
            # A fresh process has no mock, login or fake executable. If it probes,
            # it cannot get this skipped result. Persistent cadence survives restart.
            child=subprocess.run([sys.executable,'-m','optimizer','dry-run',*args],cwd=ROOT,capture_output=True,text=True,timeout=10)
            self.assertEqual(child.returncode,0,child.stderr)
            result=json.loads(child.stdout)
            self.assertEqual(result['account_probe_attempts'],0)
            self.assertEqual(result['alerts'],[])
            self.assertEqual(result['decisions'][0]['reason'],'Metadata read not due')
            self.assertFalse(result['live_requests_enabled'])

    def test_first_offline_alias_can_bind_hash_but_operational_state_cannot(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);path=self.config(base);state=base/'state'
            args=['--config',str(path),'--state-dir',str(state)]
            self.assertEqual(self.tick(args)[0],0)
            data=json.loads(path.read_text());data['profiles'][0]['expected_account_id_hash']='0123456789abcdef'
            path.write_text(json.dumps(data));self.assertEqual(self.tick(args)[0],0)
            data['profiles'][0]['expected_account_id_hash']='fedcba9876543210'
            path.write_text(json.dumps(data));self.assertEqual(self.tick(args)[0],2)

    def test_invalid_deadline_is_not_treated_as_due(self):
        for value in (True,float('nan'),-1,'soon'):
            with self.assertRaises(ValueError): due({'read_config_hash':'hash','next_status_read_at':value},NOW,'hash')

    def test_alias_upgrade_cannot_rebind_operational_or_unknown_state(self):
        for field in ('previous', 'fixed_resets', 'reset_candidates', 'attempt',
                      'inflight', 'uncertain', 'completed_disposable',
                      'handled_windows', 'handled_through', 'unknown_future_field'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                base=Path(temp); path=self.config(base); state_dir=base/'state'
                args=['--config',str(path),'--state-dir',str(state_dir)]
                self.assertEqual(self.tick(args)[0],0)
                store=Store(state_dir)
                with store.locked():
                    saved=store.load(); saved['accounts']['plus'][field]={}
                    store.save(saved)
                data=json.loads(path.read_text())
                data['profiles'][0]['expected_account_id_hash']='0123456789abcdef'
                path.write_text(json.dumps(data))
                self.assertEqual(self.tick(args)[0],2)

    def test_unbound_legacy_state_is_not_silently_adopted(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); path=self.config(base); state_dir=base/'state'
            args=['--config',str(path),'--state-dir',str(state_dir)]
            self.assertEqual(self.tick(args)[0],0)
            store=Store(state_dir)
            with store.locked():
                saved=store.load()
                saved['accounts']['plus']={'handled_windows':{}}
                store.save(saved)
            self.assertEqual(self.tick(args)[0],2)

    def test_hash_shaped_alias_does_not_allow_rebinding_an_established_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); path=self.config(base); state_dir=base/'state'
            data=json.loads(path.read_text())
            data['profiles'][0]['account_id']='0123456789abcdef'
            data['profiles'][0]['expected_account_id_hash']='0123456789abcdef'
            path.write_text(json.dumps(data))
            args=['--config',str(path),'--state-dir',str(state_dir)]
            self.assertEqual(self.tick(args)[0],0)
            data['profiles'][0]['expected_account_id_hash']=None
            path.write_text(json.dumps(data))
            self.assertEqual(self.tick(args)[0],2)
            data['profiles'][0]['expected_account_id_hash']='fedcba9876543210'
            path.write_text(json.dumps(data))
            self.assertEqual(self.tick(args)[0],2)

    def test_legacy_offline_alias_without_provenance_can_bind_once(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); path=self.config(base); state_dir=base/'state'
            args=['--config',str(path),'--state-dir',str(state_dir)]
            self.assertEqual(self.tick(args)[0],0)
            store=Store(state_dir)
            with store.locked():
                saved=store.load()
                saved['accounts']['plus']={'identity_binding':'plus'}
                store.save(saved)
            data=json.loads(path.read_text())
            data['profiles'][0]['expected_account_id_hash']='0123456789abcdef'
            path.write_text(json.dumps(data))
            self.assertEqual(self.tick(args)[0],0)
            with store.locked():
                saved=store.load()
                self.assertEqual(saved['accounts']['plus']['identity_binding_kind'],'account_hash')
            data['profiles'][0]['expected_account_id_hash']='fedcba9876543210'
            path.write_text(json.dumps(data))
            self.assertEqual(self.tick(args)[0],2)

    def test_due_only_without_account_mode_holds(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);path=self.config(base)
            code,_=self.tick(['--config',str(path),'--state-dir',str(base/'state'),'--due-only'])
            self.assertEqual(code,2);self.assertFalse((base/'state').exists())


if __name__=='__main__':unittest.main()
