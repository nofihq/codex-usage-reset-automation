"""Credential-free Linux sandbox smoke test; never an auth or model readiness test."""
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading

DIAGNOSTIC_VERSIONS = {'0.158.0', '0.159.2', '0.162.1'}
OUTPUT_LIMIT = 65536
TIMEOUT = 20


@dataclass(frozen=True)
class Run:
    code: int | None
    output: bytes = b''
    timeout: bool = False
    overflow: bool = False


def diagnostic_environment(home):
    # Allow system runtime variables only, not credentials, proxies or config overrides.
    keys=('PATH','HOME','LANG','LC_ALL','TZ','SystemRoot','WINDIR','USERPROFILE','TEMP','TMP')
    env={key:os.environ[key] for key in keys if key in os.environ}
    env['CODEX_HOME']=str(home)
    return env


def run_bounded(command, cwd, env, timeout=TIMEOUT):
    process=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,
                             start_new_session=(os.name == 'posix'))
    output=bytearray(); overflow=threading.Event()
    def kill_tree():
        try:
            if os.name == 'posix': os.killpg(process.pid, signal.SIGKILL)
            else: process.kill()
        except OSError: pass
    def read():
        while True:
            block=process.stdout.read(8192)
            if not block: return
            available=OUTPUT_LIMIT-len(output)
            output.extend(block[:available])
            if len(block)>available:
                overflow.set()
                kill_tree()
                return
    reader=threading.Thread(target=read,daemon=True); reader.start()
    timed_out=False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True
        kill_tree(); process.wait(timeout=3)
    finally:
        reader.join(timeout=1)
        if reader.is_alive():
            timed_out=True
            kill_tree(); reader.join(timeout=1)
        if not reader.is_alive(): process.stdout.close()
    return Run(process.returncode,bytes(output),timed_out,overflow.is_set())


def category(result):
    if result.timeout: return 'timeout'
    if result.overflow: return 'output_limit'
    if result.code == 0: return 'passed'
    if b'app-server socket directory must be' in result.output:
        return 'daemon_directory_blocked'
    if b'unexpected argument' in result.output or b'unrecognized' in result.output:
        return 'unsupported_cli_interface'
    return 'host_runtime_unavailable'


def runtime_check(compare_nested=False, executable=None, runner=run_bounded):
    report={'mode':'runtime_preflight','account_reads':0,'model_requests_sent':0,
            'platform':sys.platform,'codex_version':None,'checks':{},
            'direct_sandbox_ready':False,'live_dispatch_enabled':False}
    if not sys.platform.startswith('linux'):
        report['blocker']='Linux cloud-host diagnostic only; native OS validation is separate'
        return report
    binary=executable or shutil.which('codex')
    if not binary:
        report['blocker']='Codex executable unavailable'
        return report
    try:
        binary=str(Path(binary).resolve(strict=True))
        with tempfile.TemporaryDirectory(prefix='optimizer-runtime-') as temp:
            base=Path(temp).resolve(); home=base/'empty-home'; home.mkdir(mode=0o700)
            env=diagnostic_environment(home)
            version=runner([binary,'--version'],base,env)
            matches=re.findall(rb'(?m)^codex-cli (\d+\.\d+\.\d+)[\r\t ]*$',version.output)
            if version.code != 0 or version.timeout or version.overflow or len(matches) != 1:
                report['blocker']='Codex version unavailable'
                return report
            report['codex_version']=matches[0].decode()
            if report['codex_version'] not in DIAGNOSTIC_VERSIONS:
                report['blocker']='CLI interface not reviewed for this diagnostic'
                return report
            # Python's isolated, no-site interpreter does no work or account/network I/O.
            smoke=[sys.executable,'-I','-S','-c','pass']
            direct=runner([binary,'sandbox','--permission-profile',':read-only','--',*smoke],base,env)
            report['checks']['direct']={'exit_code':direct.code,'category':category(direct)}
            report['direct_sandbox_ready']=category(direct)=='passed'
            if compare_nested:
                nested=runner([binary,'sandbox','--permission-profile',':workspace','--',
                               binary,'sandbox','--permission-profile',':read-only','--',*smoke],base,env)
                report['checks']['nested']={'exit_code':nested.code,'category':category(nested)}
            if not report['direct_sandbox_ready']:
                report['blocker']='Current host cannot initialize the read-only sandbox'
            else:
                report['next_step']='Test the direct cloud scheduler route separately; this does not verify auth, model requests or spending controls'
    except (OSError, ValueError, subprocess.SubprocessError):
        report['blocker']='Runtime diagnostic could not complete'
    return report


if __name__ == '__main__':
    import argparse
    import json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare-nested',action='store_true')
    args=parser.parse_args()
    result=runtime_check(args.compare_nested)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['direct_sandbox_ready'] else 2)
