from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar
import json
import os
import tempfile
import time


T = TypeVar("T")


class JsonFileError(Exception):
    """Base exception for JsonFile."""


class JsonDecodeError(JsonFileError):
    """Raised when JSON decoding fails."""


class JsonLockError(JsonFileError):
    """Raised when the file cannot be locked."""


@dataclass(frozen=True)
class JsonFileOptions:
    encoding: str = "utf-8"
    indent: int | None = 2
    sort_keys: bool = True
    ensure_ascii: bool = False
    newline: str = "\n"

    # robustness knobs
    atomic_write: bool = True
    backup: bool = False          # if True, keep a .bak copy (best-effort)
    fsync: bool = True            # fsync file before replace (helps power-loss safety)
    create_parents: bool = True
    lock: bool = True             # best-effort lock via lockfile
    lock_timeout: float = 10.0
    lock_poll_interval: float = 0.05

    # read behavior
    allow_trailing_bytes: bool = False  # if True, ignore junk after JSON value (rarely desired)


class JsonFile:
    """
    Robust JSON-on-disk helper.

    Key features:
      - Atomic writes (write to temp file then os.replace)
      - Optional .bak backup
      - Best-effort cross-platform lock using a lockfile (O_EXCL)
      - Convenience: load/save/update/edit/get/set
    """

    def __init__(self, path: str | Path, *, options: JsonFileOptions | None = None) -> None:
        self.path = Path(path)
        self.options = options or JsonFileOptions()

    # -----------------------------
    # Locking (best-effort, lockfile)
    # -----------------------------
    def _lock_path(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".lock")

    def _acquire_lock(self) -> int | None:
        if not self.options.lock:
            return None

        lock_path = self._lock_path()
        deadline = time.monotonic() + self.options.lock_timeout

        # Create the directory for the lock if needed
        if self.options.create_parents:
            lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                # O_EXCL + O_CREAT => atomic creation (fails if exists)
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                # Write PID + timestamp for debugging
                msg = f"pid={os.getpid()} time={time.time()}\n"
                os.write(fd, msg.encode(self.options.encoding, errors="replace"))
                return fd
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise JsonLockError(f"Timed out acquiring lock: {lock_path}")
                time.sleep(self.options.lock_poll_interval)

    def _release_lock(self, fd: int | None) -> None:
        if fd is None:
            return
        lock_path = self._lock_path()
        try:
            os.close(fd)
        finally:
            # Best-effort remove
            try:
                lock_path.unlink(missing_ok=True)
            except OSError:
                pass

    # -----------------------------
    # Core IO
    # -----------------------------
    def exists(self) -> bool:
        return self.path.exists()

    def load(self, default: T | None = None) -> Any | T:
        """
        Load JSON. If file doesn't exist and default is provided, returns default.
        Raises:
          - FileNotFoundError (if missing and default is None)
          - JsonDecodeError (if invalid JSON)
        """
        if not self.path.exists():
            if default is not None:
                return default
            raise FileNotFoundError(self.path)

        raw = self.path.read_text(encoding=self.options.encoding)

        try:
            if not self.options.allow_trailing_bytes:
                return json.loads(raw)
            # allow trailing: parse first JSON value only
            decoder = json.JSONDecoder()
            obj, idx = decoder.raw_decode(raw)
            return obj
        except json.JSONDecodeError as e:
            raise JsonDecodeError(f"Invalid JSON in {self.path}: {e}") from e

    def save(self, data: Any) -> None:
        """
        Save JSON with atomic replace + optional backup + optional lock.
        """
        lock_fd = self._acquire_lock()
        try:
            if self.options.create_parents:
                self.path.parent.mkdir(parents=True, exist_ok=True)

            text = json.dumps(
                data,
                indent=self.options.indent,
                sort_keys=self.options.sort_keys,
                ensure_ascii=self.options.ensure_ascii,
            ) + self.options.newline

            if self.options.atomic_write:
                self._atomic_write_text(text)
            else:
                self.path.write_text(text, encoding=self.options.encoding)

            if self.options.backup and not self.options.atomic_write:
                self._write_backup_best_effort()
        finally:
            self._release_lock(lock_fd)

    def _atomic_write_text(self, text: str) -> None:
        # Write temp file in same directory so os.replace is atomic on same filesystem
        dirpath = self.path.parent
        suffix = self.path.suffix + ".tmp"
        fd, tmp_name = tempfile.mkstemp(prefix=self.path.name + ".", suffix=suffix, dir=dirpath)
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding=self.options.encoding, newline="") as f:
                f.write(text)
                f.flush()
                if self.options.fsync:
                    os.fsync(f.fileno())

            # Best-effort: if target exists, keep a quick backup before replace
            if self.options.backup and self.path.exists():
                bak = self.path.with_suffix(self.path.suffix + ".bak")
                try:
                    # Copy bytes (small files) or rename? Copy keeps original intact.
                    bak.write_bytes(self.path.read_bytes())
                except OSError:
                    pass

            os.replace(tmp_path, self.path)  # atomic replace on most platforms/filesystems
        finally:
            # If something failed before replace, remove temp
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _write_backup_best_effort(self) -> None:
        # If atomic_write already did a pre-replace backup when file existed,
        # this becomes a post-write backup snapshot too (best-effort).
        bak = self.path.with_suffix(self.path.suffix + ".bak")
        try:
            bak.write_bytes(self.path.read_bytes())
        except OSError:
            pass

    # -----------------------------
    # Convenience helpers
    # -----------------------------
    def update(self, fn: Callable[[Any], Any], *, default: Any = None) -> Any:
        """
        Load -> apply fn(data) -> save -> return new data.
        If missing, starts from default.
        Whole operation is locked (if enabled).
        """
        lock_fd = self._acquire_lock()
        try:
            current = self.load(default=default)
            new_data = fn(current)
            self._save_under_lock(new_data)
            return new_data
        finally:
            self._release_lock(lock_fd)

    def edit(self, *, default: Any = None):
        """
        Context manager: gives you a mutable object, saves on exit.

        Example:
            with JsonFile("x.json").edit(default={}) as obj:
                obj["a"] = 123
        """
        return _JsonEditContext(self, default=default)

    def get(self, key: str, default: Any = None) -> Any:
        data = self.load(default={})
        if isinstance(data, Mapping):
            return data.get(key, default)
        raise TypeError(f"JSON root is not an object/dict in {self.path}")

    def set(self, key: str, value: Any, *, default_root: Any = None) -> None:
        if default_root is None:
            default_root = {}
        def mut(d: Any) -> Any:
            if not isinstance(d, dict):
                raise TypeError(f"JSON root is not an object/dict in {self.path}")
            d[key] = value
            return d
        self.update(mut, default=default_root)

    def _save_under_lock(self, data: Any) -> None:
        # Internal save path that assumes the lock (if any) is already held
        if self.options.create_parents:
            self.path.parent.mkdir(parents=True, exist_ok=True)

        text = json.dumps(
            data,
            indent=self.options.indent,
            sort_keys=self.options.sort_keys,
            ensure_ascii=self.options.ensure_ascii,
        ) + self.options.newline

        if self.options.atomic_write:
            self._atomic_write_text(text)
        else:
            self.path.write_text(text, encoding=self.options.encoding)

        if self.options.backup and not self.options.atomic_write:
            self._write_backup_best_effort()


class _JsonEditContext:
    def __init__(self, jf: JsonFile, *, default: Any):
        self.jf = jf
        self.default = default
        self._lock_fd: int | None = None
        self.data: Any = None

    def __enter__(self) -> Any:
        self._lock_fd = self.jf._acquire_lock()
        self.data = self.jf.load(default=self.default)
        return self.data

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is None:
                self.jf._save_under_lock(self.data)
        finally:
            self.jf._release_lock(self._lock_fd)
        return False  # don't suppress exceptions
