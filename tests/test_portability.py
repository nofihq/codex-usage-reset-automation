"""Offline regression coverage; every account/protocol payload is synthetic."""
from contextlib import redirect_stdout
from dataclasses import asdict, replace
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from optimizer.__main__ import load_config, main as tick
from optimizer.cli import doctor, main
from optimizer.core import decide
from optimizer.probe import (OfficialStatusAdapter, ProbeError, ReadOnlyClient, child_environment,
                             identity_hash, probe, sanitized_limits, status_from_report)
from optimizer.storage import Store
import test_optimizer as baseline
from test_optimizer import NOW, ROOT


class ConfigAndCLI(unittest.TestCase):
    def test_one_and_sixteen_aliases_and_duplicates(self):
        original=json.loads((ROOT/'examples/config.fixture.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'config.json'
            for count in (1,3,16):
                data={**original,'profiles':[{**original['profiles'][0],'account_id':f'account-{i}'} for i in range(count)]}
                path.write_text(json.dumps(data)); self.assertEqual(len(load_config(path)[1]),count)
            for rows in ([], data['profiles']+[data['profiles'][0]], [original['profiles'][0]]*2):
                path.write_text(json.dumps({**original,'profiles':rows}))
                with self.assertRaises(ValueError): load_config(path)

    def test_homes_relative_to_config_and_unique(self):
        original=json.loads((ROOT/'examples/config.fixture.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'config.json'
            original['profiles'][0]['codex_home']='accounts/plus'
            path.write_text(json.dumps(original))
            config,_,_=load_config(path)
            self.assertEqual(config['profiles'][0]['codex_home'],str(Path(temp)/'accounts/plus'))
            original['profiles'][1]['codex_home']='accounts/plus'
            path.write_text(json.dumps(original))
            with self.assertRaises(ValueError): load_config(path)

    def test_doctor_offline_and_invalid_config(self):
        with patch('subprocess.Popen', side_effect=AssertionError('No processes')), patch('subprocess.run', side_effect=AssertionError('No network')):
            result=doctor(ROOT/'examples/config.example.json')
            self.assertTrue(result['ok']); self.assertEqual(result['account_reads'],0)
            self.assertFalse(result['live_requests_enabled'])
            self.assertFalse(doctor('/missing-config-fixture')['ok'])

    def test_check_exit_and_no_state_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            out=io.StringIO()
            with redirect_stdout(out):
                code=main(['check','--config',str(ROOT/'examples/config.example.json')])
            self.assertEqual(code,0); self.assertEqual(json.loads(out.getvalue())['profile_count'],2)
            self.assertEqual(list(Path(temp).iterdir()),[])

    def test_live_flag_not_available(self):
        with redirect_stdout(io.StringIO()), patch('sys.stderr',io.StringIO()):
            with self.assertRaises(SystemExit) as error: main(['dry-run','--live'])
        self.assertEqual(error.exception.code,2)


class ConservativeGates(unittest.TestCase):
    def setUp(self):
        fixture=baseline.Decisions(); fixture.setUp()
        self.profile, self.status, self.previous=fixture.profile, fixture.status, fixture.previous

    def test_unknown_inactivity_and_credit_controls_hold_at_rounded_zero(self):
        for changes in ({'active_work':None},{'active_work':True},{'inactivity_verified':False},
                        {'purchased_credit_balance_zero':None},{'purchased_credit_balance_zero':False},
                        {'auto_reload_enabled':None},{'auto_reload_enabled':True}):
            self.assertEqual(decide(self.profile,replace(self.status,**changes),self.previous,[],{},NOW).action,'hold')


class OfficialAdapter(unittest.TestCase):
    def report(self):
        limits=sanitized_limits({'accountId':'synthetic-account-id','ordinaryUsageAllowed':True,
             'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':0,'windowDurationMins':10080,'resetsAt':NOW+604800},
                                          'secondary':{'usedPercent':0,'windowDurationMins':300,'resetsAt':NOW+18000},
                                          'credits':{'hasCredits':False,'unlimited':False,'balance':'0'}}}})
        return {'account_type':'chatgpt','observed_at':NOW,'limits':limits,'models_complete':True,'model_ids':['fixture-model']}

    def test_normalization_matches_identity_and_orders_by_duration(self):
        report=self.report(); status=status_from_report('work',identity_hash('synthetic-account-id'),report)
        self.assertEqual(status.account_id,'work')
        self.assertEqual({w.key for w in status.windows},{'codex:300','codex:10080'})
        self.assertIsNone(status.active_work); self.assertFalse(status.inactivity_verified)
        self.assertTrue(status.purchased_credit_balance_zero); self.assertIsNone(status.auto_reload_enabled)
        report['limits']['buckets'][0]['windows'].reverse()
        other=status_from_report('work',identity_hash('synthetic-account-id'),report)
        self.assertEqual({w.key for w in status.windows},{w.key for w in other.windows})

    def test_missing_false_mismatched_or_incomplete_holds(self):
        for expected in (None,identity_hash('another-account')):
            self.assertIsNone(status_from_report('work',expected,self.report()))
        for field,value in (('ordinary_usage_allowed',None),('ordinary_usage_allowed',False),('complete',False),('account_identity_hash',None)):
            report=self.report(); report['limits'][field]=value
            self.assertIsNone(status_from_report('work',identity_hash('synthetic-account-id'),report))
        report=self.report(); report['models_complete']=False
        self.assertIsNone(status_from_report('work',identity_hash('synthetic-account-id'),report))
        report=self.report(); report['limits']['buckets'][0]['windows'][0]['duration_minutes']=None
        self.assertIsNone(status_from_report('work',identity_hash('synthetic-account-id'),report))

    def test_nan_or_reset_inventory_never_leaks(self):
        raw={'accountId':'synthetic-account-id','email':'private@example.invalid','token':'secret-fixture',
             'rateLimitResetCredits':{'availableCount':123,'credits':[{'id':'private-reset-fixture'}]},
             'rateLimits':{'primary':{'usedPercent':float('nan')}}}
        output=json.dumps(sanitized_limits(raw),allow_nan=False)
        for value in ('private@','secret-fixture','private-reset-fixture','availableCount'): self.assertNotIn(value,output)

    def test_probe_protocol_with_fake_client_only(self):
        calls=[]
        class Fake:
            def __init__(self,home): self.home=home
            def call(self,method,params=None):
                calls.append((method,params))
                if method=='account/read': return {'account':{'type':'chatgpt','email':'private@example.invalid'}}
                if method=='account/rateLimits/read': return {'accountId':'synthetic-account-id','ordinaryUsageAllowed':None,'rateLimits':{}}
                if method=='model/list': return {'data':[{'model':'fixture-model'}],'nextCursor':None}
                return {}
            def send(self,payload): calls.append((payload['method'],None))
            def close(self): calls.append(('close',None))
        with patch('optimizer.probe.ReadOnlyClient',Fake): result=probe('/synthetic/isolated-home')
        self.assertTrue(calls[0][1]['capabilities']['explicitGatewayOauth'])
        self.assertEqual(calls[2],('account/read',{'refreshToken':False}))
        self.assertEqual(calls[3],('account/rateLimits/read',{'excludeResetCreditDetails':True}))
        self.assertEqual(result['model_requests_sent'],0)
        self.assertNotIn('private@',json.dumps(result)); self.assertIn(('close',None),calls)
        with patch('optimizer.probe.ReadOnlyClient',side_effect=AssertionError('No personal context')):
            self.assertEqual(probe()['account_read'],'not_attempted')

    def test_no_paid_environment_or_unreviewed_version(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'secret-fixture','CODEX_ACCESS_TOKEN':'secret-fixture'}):
            env=child_environment('/synthetic/home')
            self.assertNotIn('OPENAI_API_KEY',env); self.assertNotIn('CODEX_ACCESS_TOKEN',env)
        with patch('optimizer.probe.installed_version',return_value='99.0.0'), patch('subprocess.Popen',side_effect=AssertionError('No startup')):
            with self.assertRaises(ProbeError): ReadOnlyClient('/synthetic/home')

    def test_tick_uses_time_after_read_and_rejects_simulated_clock(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); config=json.loads((ROOT/'examples/config.example.json').read_text())
            for row in config['profiles']: row['expected_account_id_hash']=identity_hash('synthetic-account-id')
            path=base/'config.json'; path.write_text(json.dumps(config))
            out=io.StringIO()
            with patch('optimizer.probe.probe',return_value=self.report()), patch('optimizer.__main__.time.time',side_effect=[NOW-1,NOW+1,NOW+2]), redirect_stdout(out):
                code=tick(['--config',str(path),'--read-accounts','--state-dir',str(base/'state')])
            self.assertEqual(code,0)
            result=json.loads(out.getvalue())
            self.assertTrue(all('stale or from the future' not in d['reason'] for d in result['decisions']))
            out=io.StringIO()
            with redirect_stdout(out):
                code=tick(['--config',str(path),'--read-accounts','--now','2026-10-14T12:02:00Z','--state-dir',str(base/'other')])
            self.assertEqual(code,2); self.assertFalse((base/'other').exists())

    def test_tick_read_only_adapter_connection(self):
        with tempfile.TemporaryDirectory() as temp:
            out=io.StringIO()
            with patch('optimizer.probe.probe',return_value=self.report()), redirect_stdout(out):
                code=tick(['--config',str(ROOT/'examples/config.example.json'),'--read-accounts','--state-dir',temp])
            result=json.loads(out.getvalue())
            self.assertEqual(code,0); self.assertEqual(len(result['probes']),2)
            self.assertTrue(all(d['action']=='hold' for d in result['decisions']))
            self.assertFalse(result['live_requests_enabled'])


class PrivateStorage(unittest.TestCase):
    def test_shared_directory_rejected_without_chmod(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'shared'; path.mkdir(mode=0o777); path.chmod(0o777)
            with self.assertRaises(ValueError): Store(path)
            self.assertEqual(path.stat().st_mode & 0o777,0o777)
            self.assertEqual(list(path.iterdir()),[])

    def test_symlinked_directory_and_state_paths_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); safe=base/'safe'; safe.mkdir(mode=0o700)
            link=base/'link'; link.symlink_to(safe,target_is_directory=True)
            with self.assertRaises(ValueError): Store(link)
            sentinel=base/'sentinel'; sentinel.write_text('unchanged')
            for name in ('state.json','lock','events.log','state-unsafe.tmp'):
                path=safe/name; path.symlink_to(sentinel)
                with self.assertRaises(ValueError): Store(safe)
                self.assertEqual(sentinel.read_text(),'unchanged'); path.unlink()

    def test_wrong_owner_and_hard_link_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch('optimizer.storage.os.geteuid',return_value=os.geteuid()+1):
                with self.assertRaises(ValueError): Store(temp)
            path=Path(temp)/'state.json'; path.write_text('{}'); path.chmod(0o600)
            os.link(path,Path(temp)/'second-link')
            with self.assertRaises(ValueError): Store(temp)

    def test_new_directory_is_private(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'state'; store=Store(path)
            self.assertEqual(path.stat().st_mode & 0o777,0o700)
            with store.locked(): store.save(store.load())
            self.assertEqual((path/'state.json').stat().st_mode & 0o777,0o600)


class Install(unittest.TestCase):
    def test_zipapp_from_unrelated_directory_and_error_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            result=subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--prefix',temp],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            command=str(Path(temp)/'bin/codex-usage-optimizer')
            result=subprocess.run([command,'doctor','--config',str(ROOT/'examples/config.example.json')],cwd=temp,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr); self.assertTrue(json.loads(result.stdout)['ok'])
            result=subprocess.run([command,'check','--config','/missing-fixture-config'],cwd=temp,capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            result=subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--prefix',temp],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)


if __name__=='__main__': unittest.main()
