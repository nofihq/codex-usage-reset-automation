"""Private synthetic temporary directories on each OS."""
from contextlib import contextmanager
import os
from pathlib import Path
import tempfile


@contextmanager
def private_temp():
    with tempfile.TemporaryDirectory() as directory:
        if os.name == 'nt':
            from optimizer.windows_security import create_private_directory
            path = Path(directory)/'private'
            create_private_directory(path)
            yield str(path)
        else:
            yield str(Path(directory).resolve())
