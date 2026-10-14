"""Small standard-library platform helpers; no credential or network access."""
import os
from pathlib import Path
import shutil
import stat
import sys


def supported():
    return sys.version_info >= (3, 10) and (os.name == 'nt' or sys.platform.startswith('linux') or sys.platform == 'darwin')


def state_default():
    if os.name == 'nt':
        return str(Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData'/'Local'))/'codex-usage-reset-automation')
    if sys.platform == 'darwin':
        return str(Path.home()/'Library'/'Application Support'/'codex-usage-reset-automation')
    return str(Path.home()/'.local'/'state'/'codex-usage-reset-automation')


def is_link(path):
    """Reject Windows junctions/reparse points as well as POSIX symlinks."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def codex_command():
    executable = shutil.which('codex')
    if not executable:
        raise OSError('Codex is not on PATH')
    if os.name == 'nt' and Path(executable).suffix.lower() in {'.cmd', '.bat', '.ps1'}:
        # npm's Windows shim is a batch file. Invoke the official JS entry point
        # with Node directly, never a shell with interpolated paths/arguments.
        launcher = Path(executable).parent/'node_modules'/'@openai'/'codex'/'bin'/'codex.js'
        node = shutil.which('node')
        if not node or not launcher.is_file():
            raise OSError('Unsupported Windows CLI shim')
        return [node, str(launcher)]
    return [executable]


def private_directory(directory):
    """Create a private directory or validate an existing one without repairing it."""
    path = Path(directory).expanduser().absolute()
    if any(is_link(component) for component in (path, *path.parents)):
        raise ValueError('Linked directory prohibited')
    if os.name == 'nt':
        from .windows_security import create_private_directory, validate_private
        path.parent.mkdir(parents=True, exist_ok=True)
        create_private_directory(path)
        validate_private(path)
    else:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError('Directory must be user-owned and private')
    return path


def installed_command(prefix):
    path = Path(prefix)/'bin'/'codex-usage-optimizer'
    return [sys.executable, str(path.with_suffix('.pyz'))] if os.name == 'nt' else [str(path)]
