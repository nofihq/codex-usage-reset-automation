#!/usr/bin/env python3
"""Offline clean-clone and installation smoke test; no accounts or network."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import os

ROOT=Path(__file__).resolve().parents[1]


def run(argv,cwd,env):
    result=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=60)
    if result.returncode:
        raise RuntimeError('Verification failed: '+argv[0])
    return result


def main():
    env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'
    with tempfile.TemporaryDirectory(prefix='optimizer-clean-clone-') as temp:
        base=Path(temp); clone=base/'source'; prefix=base/'installed'
        run(['git','clone','--no-hardlinks','--quiet',str(ROOT),str(clone)],base,env)
        shutil.copyfile(clone/'examples/config.example.json',clone/'config.json')
        steps=[]
        for command in ('doctor','check'):
            result=run(['python3','-m','optimizer',command,'--config','config.json'],clone,env)
            if not json.loads(result.stdout)['ok']: raise RuntimeError('Offline check failed')
            steps.append(command)
        result=run(['python3','-m','unittest','discover','-s','tests','-v'],clone,env)
        count=re.search(r'Ran (\d+) tests',result.stderr)
        steps.append('unit tests')
        run(['python3','scripts/privacy_check.py'],clone,env); steps.append('tracked privacy scan')
        for fixture,now in (('status-before.json','2026-10-14T10:00:00Z'),('status-after.json','2026-10-14T12:02:00Z')):
            result=run(['python3','-m','optimizer','dry-run','--config','examples/config.fixture.json',
                        '--status','fixtures/'+fixture,'--feed-fixture','fixtures/timeline.json',
                        '--now',now,'--state-dir',str(base/'replay-state')],clone,env)
            if json.loads(result.stdout)['live_requests_enabled']: raise RuntimeError('Live requests must stay disabled')
        steps.append('synthetic replay')
        run(['python3','scripts/install.py','--prefix',str(prefix)],clone,env)
        result=run([str(prefix/'bin/codex-usage-optimizer'),'doctor','--config',str(clone/'config.json')],base,env)
        if not json.loads(result.stdout)['ok']: raise RuntimeError('Installed command failed')
        steps.append('installed command outside clone')
        status=run(['git','status','--porcelain'],clone,env)
        if status.stdout.strip(): raise RuntimeError('Clean clone acquired unignored changes')
        print(json.dumps({'ok':True,'tests_passed':int(count.group(1)) if count else None,
                          'checks':steps,'network_calls':0,'account_reads':0,'live_requests':0},indent=2))


if __name__=='__main__': main()
