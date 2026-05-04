import os
from dataclasses import dataclass
from io import IOBase, RawIOBase, BufferedIOBase, TextIOBase, FileIO, BytesIO, TextIOWrapper, UnsupportedOperation
from os import PathLike
from typing import Optional, Iterable, Any, IO, TypeVar, Generic, Sequence, \
    Protocol, runtime_checkable

TIO = TypeVar("TIO", bound=IOBase | IO[Any])

# --- Protocols for optional capabilities (no more hasattr soup) ---

@runtime_checkable
class SupportsGetValue(Protocol):
    def getvalue(self) -> Any: ...

@runtime_checkable
class SupportsGetBuffer(Protocol):
    def getbuffer(self) -> Any: ...

@runtime_checkable
class SupportsPeek(Protocol):
    def peek(self, size: int = 0, /) -> Any: ...

@runtime_checkable
class SupportsRead1(Protocol):
    def read1(self, size: int = -1, /) -> Any: ...

@runtime_checkable
class SupportsReadAll(Protocol):
    def readall(self) -> Any: ...

@runtime_checkable
class SupportsReadInto(Protocol):
    def readinto(self, buffer: Any) -> int: ...

@runtime_checkable
class SupportsReadInto1(Protocol):
    def readinto1(self, buffer: Any) -> int: ...

@runtime_checkable
class SupportsReconfigure(Protocol):
    def reconfigure(
        self,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        line_buffering: bool | None = None,
        write_through: bool | None = None,
    ) -> None: ...

@dataclass(frozen=True)
class FDState:
    path: PathLike[str]
    is_open: bool

_fd_state: dict[int, FDState] = {}

def used_file_descriptor(fd: int | None) -> bool:
    """

    :param fd: The file descriptor
    :return: Whether the file descriptor is on record.
    """
    if fd is None:
        return False
    return fd in _fd_state.keys()

def get_file_descriptor(fd: int | None, default=None):
    """

    :param fd: The file descriptor
    :param default: The value to return if the file descriptor isn't on record.
    :return: A `tuple` where the first element is the last known path tied to `fd` and the second element is if it is open.
    """
    if fd is None:
        return default
    return _fd_state.get(fd, default)

def fd_closed(fd: int | None, *, path: Optional[PathLike[str]] = None) -> bool:
    """
    Gets whether a file descriptor is closed or not.

    The `path` argument is for when wanting to validate that
    the file descriptor is for a certain path. If the given
    `path` isn't the last known path to the file descriptor,
    then `False` is returned.

    :param fd: The file descriptor.
    :param path: The optional path of the file descriptor.
    :return: True if the file descriptor is closed, False otherwise.
    """
    descriptor = get_file_descriptor(fd)
    if descriptor is None:
        return False
    if path is not None and descriptor.path != path:
        return False
    return not descriptor.is_open

def fd_open(fd: int) -> bool:
    """
    Gets whether a file descriptor is open or not.

    :param fd: The file descriptor.
    :return: False if the file descriptor is closed, True otherwise.
    """
    descriptor = get_file_descriptor(fd)
    if descriptor is None:
        return False
    return descriptor.is_open


class ContentWrapper(Generic[TIO], IOBase, IO[Any]):
    def __init__(
            self,
            content: Optional[TIO] = None,
            path: Optional[PathLike[str]] = None,
            *,
            mode: str | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            line_buffering: bool = False,
            write_through: bool = False,
            closefd: bool = True,
            own_content: bool = False,
    ):
        self._content = content
        self._path = path
        self._mode = mode
        self._encoding = encoding
        self._errors = errors
        self._newline = newline
        self._line_buffering = line_buffering
        self._write_through = write_through
        self._closefd = closefd
        self._own_content = own_content
        if (content is None and path is not None) or (path is None and content is not None):
            raise ValueError("If content or path is specified, then the other is required.")
        if self._content is not None and self._content.closed:
            raise RuntimeError("Content is already closed.")
        self._update_fd_state(is_open=True)

    @property
    def content(self) -> Optional[TIO]:
        return self._content

    @property
    def path(self) -> Optional[PathLike[str]]:
        return self._path

    @property
    def own_content(self):
        return self._own_content

    @property
    def mode(self) -> str | None:
        return getattr(self.content, "mode", self._mode)

    @property
    def name(self) -> str | None:
        return getattr(self.content, "name", None)

    @property
    def encoding(self) -> str | None:
        return getattr(self.content, "encoding", self._encoding)

    @property
    def errors(self) -> str | None:
        return getattr(self.content, "errors", self._errors)

    @property
    def newline(self) -> str | None:
        return getattr(self.content, "newline", self._newline)

    @property
    def line_buffering(self) -> bool:
        return bool(getattr(self.content, "line_buffering", self._line_buffering))

    @property
    def write_through(self) -> bool:
        return bool(getattr(self.content, "write_through", self._write_through))

    @property
    def closed(self):
        c = self.content
        return True if c is None else c.closed

    @property
    def closefd(self) -> bool:
        return bool(getattr(self.content, "closefd", self._closefd))

    # -----------------------------
    # Checkers
    # -----------------------------

    def has_content(self):
        return self.content is not None

    def isatty(self):
        return self._require().isatty()

    def readable(self):
        return self._require().readable()

    def writable(self):
        return self._require().writable()

    def seekable(self):
        return self._require().seekable()

    def is_raw(self):
        return isinstance(self.content, RawIOBase)

    def is_buffered(self):
        return isinstance(self.content, BufferedIOBase)

    def is_text(self):
        return isinstance(self.content, TextIOBase)

    def is_file_io(self):
        return isinstance(self.content, FileIO)

    def is_bytes_io(self):
        return isinstance(self.content, BytesIO)

    # -----------------------------
    # Attach / detach typing
    # -----------------------------

    def detach(self, *, require: bool = False) -> tuple[TIO | None, PathLike[str] | None]:
        ret = self._get(require=require)
        self._update_fd_state(remove=True)
        self._path = None
        self._content = None
        return ret

    def attach(
            self,
            content: TIO,
            path: PathLike[str],
            *,
            mode: str | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            line_buffering: bool = False,
            write_through: bool = False,
            own_content: bool = False,
    ) -> tuple[TIO | None, PathLike[str] | None]:
        ret = self._get(False)
        self._content = content
        self._path = path
        if mode is not None:
            self._mode = mode
        self._recon(
            has_recon=True,
            encoding=encoding,
            errors=errors,
            newline=newline,
            line_buffering=line_buffering,
            write_through=write_through,
            own_content=own_content,
        )
        if (content is None and path is not None) or (path is None and content is not None):
            raise ValueError("If content or path is specified, then the other is required.")
        if self._content is not None and self._content.closed:
            raise RuntimeError("Content is already closed.")
        self._update_fd_state(is_open=True)
        return ret

    def reconfigure(
            self,
            *,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            line_buffering: bool | None = None,
            write_through: bool | None = None,
            own_content: bool | None = None,
    ):
        c = self._require()
        has_recon = False
        # If it's a TextIOWrapper, call its real reconfigure
        if isinstance(c, TextIOWrapper):
            has_recon = True
            c.reconfigure(
                encoding=encoding,
                errors=errors,
                newline=newline,
                line_buffering=line_buffering,
                write_through=write_through,
            )
        # Or if some other stream provides a compatible method
        elif isinstance(c, SupportsReconfigure):
            has_recon = True
            c.reconfigure(
                encoding=encoding,
                errors=errors,
                newline=newline,
                line_buffering=line_buffering,
                write_through=write_through,
            )
        self._recon(
            has_recon=has_recon,
            encoding=encoding,
            errors=errors,
            newline=newline,
            line_buffering=line_buffering,
            write_through=write_through,
            own_content=own_content,
        )

    # -----------------------------
    # Basic ops
    # -----------------------------

    def close(self, detach: bool = True):
        c = self.content
        if c is not None:
            c.close()
            self._close_handle(valid_close=True)
        return self.detach() if detach else None

    def flush(self):
        self._require().flush()

    def fileno(self) -> int:
        return self._require().fileno()

    def tell(self) -> int:
        return self._require().tell()

    def getvalue(self) -> Any:
        c = self._require()
        if isinstance(c, SupportsGetValue):
            return c.getvalue()
        raise NotImplementedError()

    def getbuffer(self) -> Any:
        c = self._require()
        if isinstance(c, SupportsGetBuffer):
            return c.getbuffer()
        raise NotImplementedError()

    # -----------------------------
    # Reading Content
    # -----------------------------

    def seek(self, offset, whence=os.SEEK_SET) -> int:
        return self._require().seek(offset, whence)

    def read(self, size: int=-1) -> Any:
        return self._require().read(size)

    def read1(self, size: int | None=-1) -> Any:
        c = self._require()
        if isinstance(c, SupportsRead1):
            if size is None and isinstance(c, BufferedIOBase):
                size = -1
            return self.content.read1(size)
        raise NotImplementedError()

    def readline(self, size = -1, /) -> Any:
        return self._require().readline(size)

    def readlines(self, sizehint = -1, /) -> list[Any]:
        return self._require().readlines(sizehint)

    def readall(self) -> Any:
        c = self._require()
        if isinstance(c, SupportsReadAll):
            return c.readall()
        raise NotImplementedError()

    def readinto(self, buffer) -> int:
        c = self._require()
        ret = None
        if isinstance(c, SupportsReadInto):
            ret = c.readinto(buffer)
        else:
            raise NotImplementedError()
        return ret or 0

    def readinto1(self, buffer) -> int:
        c = self._require()
        if isinstance(c, SupportsReadInto1):
            return c.readinto1(buffer)
        raise NotImplementedError()

    def peek(self, size: int=0, /) -> Any:
        c = self._require()
        if isinstance(c, SupportsPeek):
            return c.peek(size)
        raise NotImplementedError()

    # -----------------------------
    # Writing Content
    # -----------------------------

    def truncate(self, size:int | None=None) -> int:
        return self._require().truncate(size)

    def write(self, data: Any) -> int:
        return self._require().write(data)

    def writelines(self, lines: Iterable[Any]) -> None:
        self._require().writelines(lines)

    # -----------------------------
    # Helpers
    # -----------------------------

    def _require(self) -> TIO:
        """
        Return the underlying stream or raise BlockingIOError.

        assert content exists (improves typing a lot)
        """
        if self._content is None:
            raise BlockingIOError()
        return self._content

    def _recon(
            self,
            has_recon: bool,
            *,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            line_buffering: bool | None = None,
            write_through: bool | None = None,
            own_content: bool | None = None,
    ):
        if encoding is not None:
            self._encoding = encoding
        if errors is not None:
            self._errors = errors
        if newline is not None:
            self._newline = newline
        if line_buffering is not None:
            self._line_buffering = line_buffering
        if write_through is not None:
            self._write_through = write_through
        if own_content is not None:
            self._own_content = own_content

    def _get(self, require: bool):
        return (self._require() if require else self.content), self.path

    def _close_handle(self, *, valid_close: bool=False, force_close: bool=False) -> None:
        if self._content is None:
            return
        closed = valid_close or self._content.closed
        if closed:
            self._update_fd_state(is_open=False)
        elif force_close:
            self.close(detach=False)

    def _update_fd_state(self, *, is_open: bool | None=None, remove: bool=False) -> None:
        c = self._content
        if c is None:
            return
        try:
            fd = c.fileno()
            if remove:
                _fd_state.pop(fd, None)
                return
            if is_open is not None:
                    _fd_state[fd] = FDState(self._path, is_open)
        except (UnsupportedOperation, OSError, ValueError):
            pass

    # -----------------------------
    # Iteration + context manager
    # -----------------------------

    def __iter__(self):
        return iter(self._require())

    def __next__(self):
        return next(self._require())  # type: ignore[misc]

    def __enter__(self):
        c = self._content
        if c is not None:
            # delegate if it supports it
            enter = getattr(c, "__enter__", None)
            if callable(enter):
                enter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        c = self._content
        if c is not None:
            exit_ = getattr(c, "__exit__", None)
            if callable(exit_):
                ret = exit_(exc_type, exc_val, exc_tb)
                self._close_handle(force_close=self.own_content)
                return ret
        if self.own_content:
            self.close(False)
        return None

    def __del__(self):
        # best-effort; don't raise during GC
        try:
            self.close(False)
        except Exception:
            pass


class TextContentWrapper(ContentWrapper[TextIOBase]):
    def read(self, size: int | None = None) -> str:
        return super().read(size)

    def readline(self, size: int = -1) -> str:
        return super().readline(size)

    def readlines(self, sizehint: int = -1) -> list[str]:
        return super().readlines(sizehint)

    def write(self, data: str) -> int:
        return super().write(data)

    def writelines(self, lines: Iterable[str]) -> None:
        super().writelines(lines)


class BufferedContentWrapper(ContentWrapper[BufferedIOBase]):
    def read(self, size: int | None = None) -> bytes:
        return super().read(size)

    def read1(self, size: int | None = -1) -> bytes:
        return super().read1(size)

    def readline(self, size: int = -1) -> bytes:
        return super().readline(size)

    def readlines(self, sizehint: int = -1) -> list[bytes]:
        return super().readlines(sizehint)

    def write(self, data: bytes | bytearray | memoryview) -> int:
        return super().write(data)

    def writelines(self, lines: Iterable[Sequence[int]]) -> None:
        super().writelines(lines)

