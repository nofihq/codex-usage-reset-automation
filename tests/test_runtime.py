"""No-login diagnostics: real bounded subprocesses and synthetic CLI responses."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from optimizer.runtime import Run, category, diagnostic_environment, run_bounded, runtime_check


class Runtime(unittest.TestCase):
    def test_child_environment_has_no_credentials_or_config_overrides(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'synthetic-secret','CODEX_ACCESS_TOKEN':'synthetic-secret',
                                    'CODEX_CONFIG_ROOT':'synthetic-private','HTTPS_PROXY':'synthetic-secret'}):
            env=diagnostic_environment('synthetic-empty-home')
        for key in ('OPENAI_API_KEY','CODEX_ACCESS_TOKEN','CODEX_CONFIG_ROOT','HTTPS_PROXY'):
            self.assertNotIn(key,env)
        self.assertEqual(env['CODEX_HOME'],'synthetic-empty-home')

    def test_actual_subprocess_output_is_bounded_and_timeout_is_killed(self):
        with tempfile.TemporaryDirectory() as temp:
            env=diagnostic_environment(temp)
            value=run_bounded([sys.executable,'-I','-S','-c','print("x"*1000000)'],temp,env)
            self.assertTrue(value.overflow); self.assertLessEqual(len(value.output),65536)
            value=run_bounded([sys.executable,'-I','-S','-c','import time;time.sleep(60)'],temp,env,timeout=0.1)
            self.assertTrue(value.timeout); self.assertIsNotNone(value.code)

    def test_nested_failure_is_sanitized_and_never_model_readiness(self):
        calls=[]
        def run(command,cwd,env):
            calls.append(command)
            self.assertTrue(Path(env['CODEX_HOME']).is_dir())
            self.assertEqual(list(Path(env['CODEX_HOME']).iterdir()),[])
            if command[-1]=='--version': return Run(0,b'WARNING: synthetic helper warning\ncodex-cli 0.162.1\n')
            if ':workspace' in command: return Run(1,b'private@example.invalid /private/path app-server socket directory must be mode 0700')
            return Run(0)
        with patch('optimizer.runtime.sys.platform','linux'):
            result=runtime_check(True,sys.executable,run)
        self.assertTrue(result['direct_sandbox_ready']); self.assertFalse(result['live_dispatch_enabled'])
        self.assertEqual(result['checks']['nested']['category'],'daemon_directory_blocked')
        self.assertNotIn('private@',str(result)); self.assertNotIn('/private/path',str(result))
        self.assertTrue(all(command[1] in ('--version','sandbox') for command in calls))

    def test_unknown_version_and_non_linux_do_not_run_smoke(self):
        calls=[]
        def run(command,cwd,env):
            calls.append(command); return Run(0,b'codex-cli 99.0.0\n')
        with patch('optimizer.runtime.sys.platform','linux'):
            self.assertFalse(runtime_check(True,sys.executable,run)['direct_sandbox_ready'])
        self.assertEqual(len(calls),1)
        with patch('optimizer.runtime.sys.platform','win32'):
            self.assertFalse(runtime_check(True,sys.executable,run)['direct_sandbox_ready'])
        self.assertEqual(len(calls),1)


if __name__=='__main__': unittest.main()
