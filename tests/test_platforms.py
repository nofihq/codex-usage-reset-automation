"""Portability regressions; synthetic data, no account or hosted runner calls."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from helpers import private_temp
from optimizer.cli import doctor
from optimizer.platforms import codex_command, is_link, state_default, supported
from optimizer.storage import Store
from optimizer.windows_security import private_sddl

ROOT = Path(__file__).resolve().parents[1]
SID = 'S-1-5-21-111-222-333-1001'


class PlatformPolicy(unittest.TestCase):
    def test_three_desktop_platforms_and_unknown(self):
        for name in ('linux', 'darwin', 'win32'):
            with patch('optimizer.platforms.sys.platform', name), patch('optimizer.platforms.os.name', 'nt' if name == 'win32' else 'posix'):
                self.assertTrue(supported())
                self.assertTrue(doctor()['ok'])
        with patch('optimizer.platforms.sys.platform', 'unsupported'), patch('optimizer.platforms.os.name', 'posix'):
            self.assertFalse(supported())

    def test_windows_acl_accepts_only_owner_system_and_admins(self):
        value=f'O:{SID}D:P(A;OICI;FA;;;{SID})(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)'
        self.assertTrue(private_sddl(value,SID))
        self.assertTrue(private_sddl(value.replace('SY','S-1-5-18'),SID))
        for bad in (value.replace(SID,'S-1-5-21-999',1), value+'(A;;FR;;;WD)',
                    value+'(A;;FR;;;BU)', f'O:{SID}D:NO_ACCESS_CONTROL', f'O:{SID}D:',
                    value+'(XA;;FR;;;SY;(condition))'):
            self.assertFalse(private_sddl(bad,SID),bad)

    def test_cli_resolution_never_uses_a_batch_shell(self):
        with private_temp() as temp:
            shim=Path(temp)/'codex.cmd'
            launcher=Path(temp)/'node_modules'/'@openai'/'codex'/'bin'/'codex.js'
            launcher.parent.mkdir(parents=True); launcher.write_text('synthetic')
            # Patch after constructing Paths: a foreign os.name changes pathlib's class.
            with patch('optimizer.platforms.shutil.which',side_effect=[str(shim),'node-fixture']), patch('optimizer.platforms.os.name','nt'), patch('optimizer.platforms.Path',type(shim)):
                self.assertEqual(codex_command(),['node-fixture',str(launcher)])
            launcher.unlink()
            with patch('optimizer.platforms.shutil.which',side_effect=[str(shim),'node-fixture']), patch('optimizer.platforms.os.name','nt'), patch('optimizer.platforms.Path',type(shim)):
                with self.assertRaises(OSError): codex_command()

    def test_lock_blocks_another_process_and_releases(self):
        with private_temp() as temp:
            script='''from optimizer.storage import Store
import sys
try:
    with Store(sys.argv[1]).locked(): pass
except ValueError:
    sys.exit(2)
'''
            store=Store(temp)
            with store.locked():
                result=subprocess.run([sys.executable,'-c',script,temp],cwd=ROOT,capture_output=True,timeout=10)
                self.assertEqual(result.returncode,2,result.stderr)
            result=subprocess.run([sys.executable,'-c',script,temp],cwd=ROOT,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_interactive_login_is_explicit_isolated_and_has_no_model_turn(self):
        from scripts.account_login import main
        with private_temp() as temp:
            config=Path(temp)/'config.json'
            home=Path(temp)/'account'
            config.write_text(json.dumps({'profiles':[{'account_id':'plus','plan_label':'Plus',
                'assumed_windows_minutes':[300,10080],'codex_home':str(home)}]}))
            with patch('scripts.account_login.installed_version',return_value='0.159.2'), patch('scripts.account_login.codex_command',return_value=['synthetic-codex']), patch('scripts.account_login.subprocess.call',return_value=0) as call:
                self.assertEqual(main(['--config',str(config),'--alias','plus']),0)
                self.assertEqual(call.call_args.args[0],['synthetic-codex','-c','forced_login_method="chatgpt"','login'])
                self.assertEqual(call.call_args.kwargs['env']['CODEX_HOME'],str(home))
                self.assertNotIn('OPENAI_API_KEY',call.call_args.kwargs['env'])
                self.assertEqual(list(home.iterdir()),[])
            with patch('scripts.account_login.installed_version',return_value='99.0.0'), patch('scripts.account_login.subprocess.call',side_effect=AssertionError('No login')), patch('sys.stderr',io.StringIO()):
                self.assertEqual(main(['--config',str(config),'--alias','plus']),2)

    @unittest.skipUnless(os.name == 'nt','Native Windows ACL test')
    def test_windows_new_state_and_files_have_private_acl(self):
        from optimizer.windows_security import validate_private
        with private_temp() as temp:
            store=Store(Path(temp)/'state')
            with store.locked():
                store.save(store.load()); store.log(2000000000,'hold')
            for name in ('state.json','lock','events.log'):
                validate_private(store.directory/name)

    @unittest.skipUnless(os.name == 'nt','Native Windows broad ACL test')
    def test_windows_broad_directory_rejected_without_repair(self):
        import ctypes
        from ctypes import wintypes
        from optimizer.windows_security import api, current_sid
        with private_temp() as temp:
            path=Path(temp)/'shared'; path.mkdir()
            kernel, advapi=api(); descriptor=ctypes.c_void_p()
            value=f'O:{current_sid()}D:P(A;OICI;FA;;;{current_sid()})(A;OICI;FR;;;WD)'
            self.assertTrue(advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(value,1,ctypes.byref(descriptor),None))
            function=advapi.SetFileSecurityW
            function.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.c_void_p]; function.restype=wintypes.BOOL
            try:
                self.assertTrue(function(str(path),4|0x80000000,descriptor))
            finally: kernel.LocalFree(descriptor)
            with self.assertRaises(ValueError): Store(path)
            self.assertEqual(list(path.iterdir()),[])


if __name__=='__main__': unittest.main()
