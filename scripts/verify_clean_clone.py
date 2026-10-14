#!/usr/bin/env python3
"""Offline clean-clone and installation smoke test; no accounts or network."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import os
import sys

ROOT=Path(__file__).resolve().parents[1]


def run(argv,cwd,env):
    result=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=60)
    if result.returncode:
        raise RuntimeError('Verification failed: '+argv[0])
    return result


def main():
    env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'
    with tempfile.TemporaryDirectory(prefix='optimizer-clean-clone-') as temp:
        base=Path(temp).resolve(); clone=base/'source'; prefix=base/'installed'
        run(['git','clone','--no-hardlinks','--quiet',str(ROOT),str(clone)],base,env)
        shutil.copyfile(clone/'examples/config.single-account.json',clone/'config.json')
        steps=[]
        for command in ('doctor','check'):
            result=run([sys.executable,'-m','optimizer',command,'--config','config.json'],clone,env)
            if not json.loads(result.stdout)['ok']: raise RuntimeError('Offline check failed')
            steps.append(command)
        result=run([sys.executable,'-m','optimizer','dry-run','--config','config.json',
                    '--state-dir',str(base/'quickstart-state')],clone,env)
        quickstart=json.loads(result.stdout)
        if (quickstart['live_requests_enabled'] or len(quickstart['decisions']) != 1
                or quickstart['decisions'][0]['account_id'] != 'plus'
                or quickstart['decisions'][0]['action'] != 'hold'):
            raise RuntimeError('Single-account quickstart must hold without live requests')
        steps.append('single-account quickstart')
        result=run([sys.executable,'-m','unittest','discover','-s','tests','-v'],clone,env)
        count=re.search(r'Ran (\d+) tests',result.stderr)
        skipped=re.search(r'skipped=(\d+)',result.stderr)
        tests_run=int(count.group(1)) if count else None
        tests_skipped=int(skipped.group(1)) if skipped else 0
        steps.append('unit tests')
        run([sys.executable,'scripts/privacy_check.py'],clone,env); steps.append('tracked privacy scan')
        for fixture,now in (('status-before.json','2026-10-14T10:00:00Z'),('status-after.json','2026-10-14T12:02:00Z')):
            result=run([sys.executable,'-m','optimizer','dry-run','--config','examples/config.fixture.json',
                        '--status','fixtures/'+fixture,'--feed-fixture','fixtures/timeline.json',
                        '--now',now,'--state-dir',str(base/'replay-state')],clone,env)
            if json.loads(result.stdout)['live_requests_enabled']: raise RuntimeError('Live requests must stay disabled')
        steps.append('synthetic replay')
        run([sys.executable,'scripts/install.py','--prefix',str(prefix)],clone,env)
        command=([sys.executable, str(prefix/'bin/codex-usage-optimizer.pyz')] if os.name == 'nt'
                 else [str(prefix/'bin/codex-usage-optimizer')])
        result=run(command+['doctor','--config',str(clone/'config.json')],base,env)
        if not json.loads(result.stdout)['ok']: raise RuntimeError('Installed command failed')
        steps.append('installed command outside clone')
        status=run(['git','status','--porcelain'],clone,env)
        if status.stdout.strip(): raise RuntimeError('Clean clone acquired unignored changes')
        print(json.dumps({'ok':True,'tests_run':tests_run,'tests_skipped':tests_skipped,
                          'tests_passed':tests_run-tests_skipped if tests_run is not None else None,
                          'checks':steps,'network_calls':0,'account_reads':0,'live_requests':0},indent=2))


if __name__=='__main__': main()
