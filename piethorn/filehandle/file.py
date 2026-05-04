import codecs
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Optional, Iterable, Any, Iterator, IO

from .content import ContentWrapper
from .path import BasePath, StrOrPath, BytesLike

class FileLockError(OSError):
    """Raised when the file cannot be locked."""


@dataclass
class FileChunk:
    """
    Represents a piece of file content returned by File.iter_content.

    - chunk: the actual content (str in text mode, bytes in binary mode).
    - size:  number of bytes from disk represented by this chunk.
    - line_end: True iff this chunk ends at a logical line boundary
                (newline or EOF). Always False in binary mode.
    """
    chunk: Union[str, bytes]
    size: int
    line_end: bool


@dataclass(frozen=True)
class FileOptions:
    encoding: str = "utf-8"
    indent: int | None = 2
    sort_keys: bool = True
    ensure_ascii: bool = False
    newline: str = "\n"

    # robustness knobs
    atomic_write: bool = True
    backup: bool = False          # if True, keep a .bak copy (best-effort)
    quick_flush: bool = False
    fsync: bool = True            # fsync file before replace (helps power-loss safety)
    force_write_last_only: bool = True
    create_parents: bool = True
    lock: bool = True             # best-effort lock via lockfile
    lock_timeout: float = 10.0
    lock_poll_interval: float = 0.05
    chunk_size: int = 4096 # The default max read/write chunk size in bytes

    # read behavior
    allow_trailing_bytes: bool = False  # if True, ignore junk after JSON value (rarely desired)

FileWriteType = Union[str, BytesLike, FileChunk, Iterable[Union[str, BytesLike, FileChunk]]]
FileReadType = Union[bytes, str]

class File(BasePath):
    def __init__(
            self,
            path: StrOrPath,
            *,
            file_descriptor: Optional[int] = None,
            is_temp: bool = False,
            options: FileOptions | None = None,
            create: bool = False,
            must_exist: bool = False
    ):
        super().__init__(path)
        self._options = options
        if self._options is None:
            if isinstance(path, File):
                self._options = path._options
            else:
                self._options = FileOptions()
        self._backing_up = False
        self._is_temp: bool = is_temp
        self._file_descriptor = file_descriptor

        if create and not self._path.exists():
            self._ensure_parent()
            self._path.open(mode="x", encoding=self._options.encoding).close()

        if must_exist:
            # Now enforce that it's a file.
            if not self._path.exists():
                raise FileNotFoundError(f"Path '{self._path}' does not exist.")
            if not self._path.is_file():
                raise IsADirectoryError(f"Path '{self._path}' is not a file.")

    @property
    def is_temp(self):
        """Determines whether this file is being used as a temp file."""
        return self._is_temp

    @property
    def options(self) -> FileOptions:
        """
        Gets the control options for this file.
        """
        return self._options

    @property
    def file_descriptor(self):
        return self._file_descriptor

    @property
    def size(self) -> int:
        """
        Size of the file in bytes.

        Raises FileNotFoundError if the file does not exist.
        """
        return self.path.stat().st_size

    # ------------------------------------------------------------
    # Reading Content
    # ------------------------------------------------------------

    def read(self, binary: bool = False, encoding: str | None = None):
        """
        Read the contents of this file.

        Ignores `options.chunk_size` bytes limit.
        :param binary: If True, return bytes instead of str
        :param encoding: Text encoding (ignored in binary mode)
        """
        enc = encoding or self.options.encoding
        if binary:
            return self.path.read_bytes()
        return self.path.read_text(encoding=enc)

    def iter_content(
            self,
            binary: bool = False,
            encoding: str | None = None,
            chunk_size: int = -1
    ) -> Iterator[FileChunk]:
        """
        Reads contents of this file.

        In binary mode, each chunk will be read up to `chunk_size` bytes.

        Binary Mode Yields: FileChunk(chunk: bytes, size: len(chunk), line_end=False)

        In text mode, the method attempts to read by line.
        However, it will be limited to `chunk_size` bytes,
        therefore the logical line will be returned in multiple chunks.
        As it attempts to keep line semantics, if a logical line contains
        fewer bytes than (or of same amount) `chunk_size`,
        the logical line will be returned as a single chunk with lineEnd=True.
        While if the logical line exceeds `chunk_size`,
        it is split into multiple chunks.
        In this case, only the final chunk for that line will have lineEnd=True;
        earlier chunks have lineEnd=False.

        Text Mode Yields: FileChunk(chunk: str, size: len(chunk), line_end: bool)

        :param binary: If True, return bytes instead of str
        :param encoding: Text encoding (ignored in binary mode).
        :param chunk_size: Max number of bytes to read and emit at a time.
        Set to -1 to define it should use the default chunk_size option.
        :return: An iterator over the contents of this file.
        """

        enc = encoding or self.options.encoding
        chunk_size = self.options.chunk_size if chunk_size == -1 else chunk_size

        # --- Binary mode: your version was basically fine ---
        if binary:
            with self.path.open("rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield FileChunk(
                        chunk=chunk,
                        size=len(chunk),
                        line_end=False,
                    )
            return

        # --- Text mode: truly chunked, line-aware, encoding-aware ---

        decoder = codecs.getincrementaldecoder(enc)()

        buffer: str = ""

        def split_text_to_byte_chunks(text: str, final_line_end: bool):
            """
            Split a decoded text string into chunks such that each chunk,
            when encoded with `enc`, is <= chunk_size bytes.

            `final_line_end` controls the lineEnd flag of the *last* chunk;
            all earlier chunks always have lineEnd=False.
            """
            if not text:
                return

            chars: list[str] = []
            c_bytes = 0

            # Chunks we build here correspond to the bytes underlying `text`,
            # but we reconstruct the byte length from encoding each char.
            for ch in text:
                b = ch.encode(enc)
                b_len = len(b)

                # If adding this char would exceed chunk_size, flush current chunk
                if chars and c_bytes + b_len > chunk_size:
                    s = "".join(chars)
                    yield FileChunk(
                        chunk = s,
                        size = c_bytes,
                        line_end= False,
                    )
                    chars = [ch]
                    c_bytes = b_len
                else:
                    chars.append(ch)
                    c_bytes += b_len

            if chars:
                s = "".join(chars)
                yield FileChunk(
                    chunk = s,
                    size = c_bytes,
                    line_end = final_line_end,
                )

        with self.path.open("rb") as f:  # always read bytes from disk
            while True:
                data_bytes = f.read(chunk_size)
                if not data_bytes:
                    # EOF: flush decoder and handle remaining buffer as final line
                    tail = decoder.decode(b"", final=True)
                    buffer += tail
                    break

                # Decode this block incrementally
                buffer += decoder.decode(data_bytes)

                # splitting buffer at line ends.
                segments = buffer.split("\n")
                buffer = segments.pop()
                for segment in segments:
                    line = segment+"\n" # Add the \n back to the logical line
                    for record in split_text_to_byte_chunks( # Split this logical line into byte-limited chunks.
                        line,
                        final_line_end=True, # Only the final chunk is marked lineEnd=True.
                    ):
                        yield record

                if buffer and len(buffer.encode(enc)) >= chunk_size:
                    current_chars: list[str] = []
                    c_bytes = 0
                    for ch in buffer:
                        b = ch.encode(enc)
                        b_len = len(b)

                        # If adding this char would exceed chunk_size, flush current chunk
                        if current_chars and c_bytes + b_len > chunk_size:
                            s = "".join(current_chars)
                            yield FileChunk(
                                chunk = s,
                                size = c_bytes,
                                line_end = False,
                            )
                            current_chars = [ch]
                            c_bytes = b_len
                        else:
                            current_chars.append(ch)
                            c_bytes += b_len
                    if current_chars:
                        buffer = "".join(current_chars)
                    else:
                        buffer = ""

            # After EOF and decoder flush, buffer holds the final unterminated line (if any)
            if buffer:
                # Final logical line: its last fragment gets lineEnd=True
                for record in split_text_to_byte_chunks(buffer, final_line_end=True):
                    yield record

    # ------------------------------------------------------------
    # Writing Content
    # ------------------------------------------------------------

    def touch(self, mode: int = 0o666, exist_ok: bool = True) -> None:
        """
        Create the file if it does not exist, or update its modification time.

        This also ensures that the parent directory exists.
        """
        with self.locked():
            self._ensure_parent()
            self.path.touch(mode=mode, exist_ok=exist_ok)

    def move_to(self, dest: StrOrPath, *, overwrite: bool = False) -> "File":
        """
        Move this file to `dest`.

        If `overwrite` is False and the destination exists, raises FileExistsError.

        The File instance is updated in-place to point to the new location and
        is also returned for chaining.
        """
        from shutil import move

        if isinstance(dest, BasePath):
            dest_path = dest.path
        else:
            dest_path = Path(dest)

        if dest_path.exists() and not overwrite:
            raise FileExistsError(f"Destination '{dest_path}' already exists.")

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        move(str(self.path), str(dest_path))
        self._path = dest_path
        return self

    def copy_to(
            self,
            dest: StrOrPath,
            *,
            overwrite: bool = False,
            follow_symlinks: bool = False,
            true_copy: bool = True,
            as_temp: bool = False,
    ) -> "File":
        """
        Copy this file to `dest` and return a new File instance for the copy.

        The current File instance is not modified and continues to point to
        the original path.
        """

        if isinstance(dest, BasePath):
            dest_path = dest.path
        else:
            dest_path = Path(dest)

        if dest_path.exists():
            if dest_path.is_dir():
                dest_path = dest_path / self.path.name
            if dest_path.exists() and not overwrite:
                raise FileExistsError(f"Destination '{dest_path}' already exists.")

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if true_copy:
            from shutil import copy2
            copy2(str(self.path), str(dest_path), follow_symlinks=follow_symlinks)
        else:
            if not follow_symlinks and self.is_symlink():
                os.symlink(os.readlink(self.path), dest_path)
            else:
                if self.size <= self.options.chunk_size:
                    dest_path.write_bytes(self.path.read_bytes())
                else:
                    dest_file = File(dest_path, options=self.options, is_temp=as_temp)
                    dest_file.write_content("wb", self.iter_content(True))
                    return dest_file
        return File(dest_path, options=self.options, is_temp=as_temp)

    def make_backup(
            self,
            *,
            follow_symlinks: bool = False,
            force: bool = False,
            pass_errors: bool = False,
            dest: Optional[StrOrPath] = None
    ):
        if force or (self.options.backup and not self._backing_up and not self.is_temp):
            if not self.exists():
                if pass_errors:
                    return None
                raise FileNotFoundError(f"The file '{self.path}' does not exist.")
            bak = self.path.with_suffix(self.path.suffix + ".bak")
            if dest is not None:
                bak = Path(dest) / bak.name
            self._backing_up = True
            bak_file = self.copy_to(bak, follow_symlinks=follow_symlinks, true_copy=False)
            self._backing_up = False
            return bak_file
        return None

    def make_temp(self) -> "File":
        """Makes a temp file for this file."""
        dirpath = self.path.parent
        suffix = self.path.suffix + ".tmp"
        fd, tmp_name = tempfile.mkstemp(prefix=self.path.name + ".", suffix=suffix, dir=dirpath)
        os.close(fd)  # <- critical: do not keep FD around
        tmp_path = Path(tmp_name)
        tmp_file = File(tmp_path, options=self.options, is_temp=True)
        return tmp_file

    def write(self, data, binary: bool = False, encoding: str | None = None):
        """
        Write content to this file.

        Ignores `options.chunk_size` bytes limit.
        :param data: Data to write (str or bytes)
        :param binary: If True, write data as bytes; otherwise as text.
        :param encoding: Encoding for text mode
        """
        with self.locked():
            self._write_data_check(data, binary)

            tmp_path: File | None = None
            if self.options.atomic_write and not self.is_temp:
                tmp_path = self.make_temp()

            try:
                target = tmp_path if tmp_path is not None else self

                if target is self:
                    self._ensure_parent()

                self.make_backup(pass_errors=True)

                target._write_helper(
                    data,
                    f=target.open(
                        mode="wb" if binary else "w",
                        encoding=encoding
                    ),
                    handle_self=True,
                )
                if tmp_path is not None:
                    os.replace(tmp_path.path, self.path)  # atomic replace on most platforms/filesystems
            finally:
                if tmp_path is not None:
                    # If something failed before replace, remove temp
                    try:
                        tmp_path.remove(missing_ok=True)
                    except OSError:
                        pass

    def write_content(
        self,
        mode: str,
        data: FileWriteType = (),
        *,
        encoding: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> int:
        """
        Unified writer for both text and binary modes.

        Ignores `options.chunk_size` bytes limit.

        Parameters
        ----------
        mode : str
            Any valid Python file mode that *includes* at least one of:
            'w', 'a', 'x', '+'.
            Examples: 'w', 'a', 'x', 'wb', 'ab', 'w+', 'xb', 'a+b', 'wt', etc.
        data : str | bytes-like | iterable of str/bytes-like
            - In text mode (no 'b'): must be str or iterable of str.
            - In binary mode ('b' present): must be bytes-like or iterable of bytes-like.
        encoding : str, optional
            Used for text modes; defaults to `self.encoding`.
        newline : str | None, optional
            Passed to `open()` in text modes (same semantics as built-in open).

        Returns
        -------
        int
            Total number of *bytes* written to disk.

        Raises
        ------
        ValueError
            If mode is not a write/append/create mode.
        TypeError
            If data type does not match text/binary mode.
        """
        with self.locked():
            # Validate mode: must have at least one write-ish flag.
            if not any(flag in mode for flag in ("w", "a", "x", "+")):
                raise ValueError(
                    f"write_content() requires a write/append/create mode, got {mode!r}"
                )

            is_binary = "b" in mode
            enc = encoding or self.options.encoding

            # Normalize data into an iterable of "chunks"
            # (each chunk is either FileChunk or raw payload)
            if isinstance(data, (str, bytes, bytearray, memoryview)) or self._is_filechunk(data):
                chunks = (data,)
            else:
                chunks = data  # assume iterable

            tmp_path: File | None = None
            if self.options.atomic_write and not self.is_temp:
                tmp_path = self.make_temp()

            total_bytes = 0

            try:
                target = tmp_path if tmp_path is not None else self

                if target is self:
                    self._ensure_parent()

                # Best-effort backup of the original before we mutate/replace it.
                # (Only once.)
                self.make_backup(pass_errors=True)

                with target.open(
                    mode=mode,
                    encoding=enc,
                    newline=newline,
                ) as f:
                    def _iter_with_last(it):
                        it = iter(it)
                        try:
                            prev = next(it)
                        except StopIteration:
                            return
                        for cur in it:
                            yield prev, False
                            prev = cur
                        yield prev, True

                    for item, on_last in _iter_with_last(chunks):
                        f_chunk = self._is_filechunk(item)
                        # Extract payload if it's a FileChunk
                        if f_chunk:
                            payload = item.chunk
                        else:
                            payload = item

                        # enforces proper data type
                        target._write_data_check(payload, is_binary)

                        b = bytes(payload) if is_binary else payload
                        target._write_helper(b, f=f, handle_self=False, on_last=on_last)
                        total_bytes += item.size if f_chunk else len(b if is_binary else b.encode(enc))

                if tmp_path is not None:
                    os.replace(tmp_path.path, self.path)  # atomic replace on most platforms/filesystems
            finally:
                if tmp_path is not None:
                    # If something failed before replace, remove temp
                    try:
                        tmp_path.remove(missing_ok=True)
                    except OSError:
                        pass

            return total_bytes

    def write_text(self, text: str, *, encoding: Optional[str] = None,
                   newline: Optional[str] = None) -> int:
        return self.write_content("w", text, encoding=encoding, newline=newline)

    def write_bytes(self, data: BytesLike) -> int:
        return self.write_content("wb", data)

    def append(self, data, *, binary: bool = False, encoding: str | None = None, newline: str | None = None) -> int:
        """
        Append data to this file and return the number of bytes written.

        This is a convenience wrapper around write_content() using 'a' or 'ab'
        modes.
        """
        mode = "ab" if binary else "a"
        return self.write_content(mode=mode, data=data, encoding=encoding, newline=newline)

    def append_text(self, text: str, *, encoding: Optional[str] = None,
                    newline: Optional[str] = None) -> int:
        return self.append(text, binary=False, encoding=encoding, newline=newline)

    def append_bytes(self, data: BytesLike) -> int:
        return self.append(data, binary=True)

    # ------------------------------------------------------------
    # Low-level open (if you need full control)
    # ------------------------------------------------------------
    def open(
        self,
        mode: str,
        *,
        buffering: int = -1,
        encoding: Optional[str] = None,
        errors: str | None = None,
        newline: Optional[str] = None,
    ):
        """
        Opens this file.

        If this file has a `file_descriptor`, then it will be
        opened with `os.fdopen`.
        Otherwise, it will be opened with `Path.open`.

        If the `file_descriptor` is closed or being used by a different
        file, then a new `file_descriptor` will be created.

        Supports all standard modes: "r", "w", "a", "rb", "wb", "ab", etc.
        """
        enc = encoding or self.options.encoding
        is_write_mode = any(flag in mode for flag in ("w", "a", "x", "+"))
        if is_write_mode:
            self._ensure_parent()
        if "b" in mode:
            # Binary mode: encoding/newline must be None (per open() rules)
            opened_io = self.path.open(mode, buffering)
        else:
            opened_io = self.path.open(
                mode,
                buffering,
                encoding=enc,
                errors=errors,
                newline=newline
            )
        return ContentWrapper(
            opened_io,
            self.path,
            mode=mode,
            encoding=enc,
            errors=errors,
            newline=newline,
        )

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------
    def _ensure_parent(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # Small duck-type helper
    @staticmethod
    def _is_filechunk(obj: Any) -> bool:
        # Don't import your actual FileChunk here; duck-typing is clean enough.
        return hasattr(obj, "chunk") and hasattr(obj, "size") and hasattr(obj, "line_end")

    def _write_helper(
            self,
            data: FileWriteType,
            f:IO[Any],
            handle_self: bool,
            on_last: bool=True
    ):
        try:
            if self._is_filechunk(data):
                data = data.chunk
            f.write(data)
            is_ready = on_last or not self.options.force_write_last_only
            if self.options.quick_flush or (is_ready and (self.is_temp or self.options.fsync)):
                f.flush()
            if self.options.fsync and is_ready:
                os.fsync(f.fileno())
        finally:
            if handle_self:
                f.close()

    def _write_data_check(
            self,
            data: FileWriteType,
            binary: bool,
    ):
        data_z = data.chunk if self._is_filechunk(data) else data
        if binary:
            if not isinstance(data_z, (bytes, bytearray, memoryview)):
                raise TypeError(
                    "Binary mode requires bytes-like data, "
                    f"got {type(data).__name__}"
                )
        else:
            if not isinstance(data_z, str):
                raise TypeError(
                    "Text mode requires string data, "
                    f"got {type(data).__name__}"
                )

    # -----------------------------
    # Locking (best-effort, lockfile)
    # -----------------------------
    @contextmanager
    def locked(self):
        """Context manager that applies this File's best-effort lock."""
        fd = self._acquire_lock()
        try:
            yield
        finally:
            self._release_lock(fd)

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
                    raise FileLockError(f"Timed out acquiring lock: {lock_path}")
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
    # magic methods
    # -----------------------------

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self._path!r}, options={self.options!r})"

