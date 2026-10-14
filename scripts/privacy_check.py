#!/usr/bin/env python3
"""Conservative tracked-source privacy check; never read untracked credential files."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = subprocess.run(['git','ls-files','-z'],cwd=ROOT,capture_output=True,check=True)
    names = [item.decode() for item in result.stdout.split(b'\0') if item]
    problems = []
    for name in names:
        path = ROOT/name
        parts = Path(name).parts
        if (name == 'config.json' or any(part in {'.codex','runtime','accounts','.accounts','sessions','captures','screenshots','snapshots','private'} for part in parts)
                or path.suffix in {'.png','.jpg','.mp4','.har','.pem','.key'} or path.name.startswith('.env')
                or path.name in {'auth.json','history.jsonl'}):
            problems.append({'file':name,'reason':'private/generated path tracked'})
            continue
        if path.is_symlink():
            problems.append({'file':name,'reason':'symlink tracked'})
            continue
        if not path.is_file():
            problems.append({'file':name,'reason':'tracked file missing'})
            continue
        text = path.read_text()
        if re.search(r'/home/[A-Za-z0-9_-]+/|/Users/[A-Za-z0-9_-]+/',text):
            problems.append({'file':name,'reason':'owner-specific absolute home path'})
        if re.search(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}',text) or re.search(r'\bgh[pousr]_[A-Za-z0-9]{24,}',text):
            problems.append({'file':name,'reason':'possible access credential'})
        emails = re.findall(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',text)
        if any(not email.endswith('.invalid') for email in emails):
            problems.append({'file':name,'reason':'non-synthetic email address'})
    print(json.dumps({'ok':bool(names) and not problems,'tracked_files':len(names),'problems':problems,
                      'scope':'tracked source only; manual review still required'},indent=2))
    return 0 if names and not problems else 2


if __name__=='__main__': raise SystemExit(main())
