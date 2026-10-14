#!/usr/bin/env python3
"""Build an executable zipapp using only Python; no downloads or credentials."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipapp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default=str(Path.home()/'.local'))
    parser.add_argument('--replace', action='store_true', help='Replace an existing optimizer executable only')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = Path(args.prefix).expanduser()/'bin'/'codex-usage-optimizer'
    if output.exists() and not args.replace:
        parser.error('Command already exists; choose another prefix or explicitly use --replace')
    if output.is_symlink():
        parser.error('Refusing a symlinked executable destination')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='optimizer-build-') as temp:
        stage = Path(temp)
        shutil.copytree(root/'optimizer', stage/'optimizer', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (stage/'__main__.py').write_text('from optimizer.cli import main\nraise SystemExit(main())\n')
        zipapp.create_archive(stage, output, interpreter='/usr/bin/env python3')
    print(json.dumps({'installed': True, 'command': str(output), 'dependencies': 'stdlib only'}))


if __name__ == '__main__':
    main()
