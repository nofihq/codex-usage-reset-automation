"""Single-host native locks, private bounded state, rotating scrubbed logs."""
from contextlib import contextmanager
try:
    import fcntl
except ImportError:
    fcntl = None
import json
import os
import stat
from pathlib import Path
import tempfile

from .adapters import read_json
from .platforms import is_link, private_directory

if os.name == 'nt':
    import msvcrt
    from .windows_security import validate_private

STATE_BYTES = 131072
LOG_BYTES = 65536
LOG_FILES = 4
LOG_RETENTION_SECONDS = 7 * 86400
METRICS = ("ticks", "hold", "check_status", "would_request", "feed_ok", "feed_failed", "errors")


class Store:
    def __init__(self, directory):
        if fcntl is None and os.name != 'nt':
            raise ValueError("No supported file-locking backend")
        self.directory = private_directory(directory)
        self.path = self.directory / "state.json"
        self.validate_paths()

    def validate_paths(self):
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or is_link(self.directory):
            raise ValueError("Unsafe state directory")
        if os.name == 'nt':
            validate_private(self.directory)
        elif (info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077):
            raise ValueError("State directory must be owned by this user and private (0700)")
        paths = [self.path, self.directory/"lock"]
        paths += list(self.directory.glob("events.log*")) + list(self.directory.glob("state-*.tmp"))
        for path in paths:
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(info.st_mode) or is_link(path) or info.st_nlink != 1:
                raise ValueError("Unsafe state file")
            if os.name == 'nt':
                validate_private(path)
            elif (info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o022):
                raise ValueError("Unsafe state file; inspect locally without changing shared permissions")

    @contextmanager
    def locked(self):
        self.validate_paths()
        fd = os.open(self.directory/"lock", os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(fd, "a") as lock:
            try:
                if os.name == 'nt':
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise ValueError("Another tick owns the state lock") from exc
            try:
                # Remove only our own abandoned atomic-write temp files, under lock.
                for orphan in self.directory.glob("state-*.tmp"):
                    orphan.unlink()
                yield
            finally:
                if os.name == 'nt':
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock, fcntl.LOCK_UN)

    def load(self):
        self.validate_paths()
        if not self.path.exists():
            return {"version": 1, "accounts": {}, "metrics": {}}
        state = read_json(self.path, STATE_BYTES)
        if not isinstance(state, dict) or state.get("version") != 1:
            raise ValueError("Unknown state version; do not overwrite")
        if not isinstance(state.get("accounts"), dict) or len(state["accounts"]) > 16:
            raise ValueError("Invalid account state")
        if not isinstance(state.get("metrics"), dict):
            raise ValueError("Invalid metrics state")
        if any(k not in METRICS or type(v) is not int or not 0 <= v <= 10**9
               for k, v in state["metrics"].items()):
            raise ValueError("Invalid metrics")
        return state

    def save(self, state):
        self.validate_paths()
        data = json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if len(data) > STATE_BYTES:
            raise ValueError("State limit exceeded; hold without discarding idempotency")
        fd, name = tempfile.mkstemp(prefix="state-", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
            if os.name != 'nt':
                directory_fd = os.open(self.directory, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            Path(name).unlink(missing_ok=True)

    def log(self, now, code):
        self.validate_paths()
        # Caller supplies only an allowlisted code; no feed text/status/exception strings.
        if code not in METRICS:
            raise ValueError("Unknown log code")
        paths = [self.directory / ("events.log" if i == 0 else f"events.log.{i}")
                 for i in range(LOG_FILES)]
        for path in paths:
            if path.exists() and path.stat().st_mtime < now - LOG_RETENTION_SECONDS:
                path.unlink()
            elif path.exists():
                # Retention applies to individual entries even in a quiet active file.
                if path.stat().st_size > LOG_BYTES:
                    raise ValueError("Unexpected oversized log")
                rows = path.read_text().splitlines(keepends=True)
                keep = [row for row in rows if json.loads(row)["at"] >= now - LOG_RETENTION_SECONDS]
                if keep != rows:
                    with path.open("w", encoding="utf-8", newline="") as handle:
                        handle.write("".join(keep))
        entry = json.dumps({"at": now, "code": code}, separators=(",", ":")) + "\n"
        if paths[0].exists() and paths[0].stat().st_size + len(entry.encode()) > LOG_BYTES:
            paths[-1].unlink(missing_ok=True)
            for i in range(LOG_FILES-2, -1, -1):
                if paths[i].exists():
                    paths[i].replace(paths[i+1])
        with paths[0].open("a", encoding="utf-8", newline="") as handle:
            handle.write(entry)
        if os.name != 'nt':
            os.chmod(paths[0], 0o600)
        os.utime(paths[0], (now, now))


def increment(state, key):
    if key not in METRICS:
        raise ValueError("Unknown metric")
    metrics = state.setdefault("metrics", {})
    metrics[key] = min(10**9, metrics.get(key, 0) + 1)
