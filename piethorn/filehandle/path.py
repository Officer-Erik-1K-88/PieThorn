from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Optional, Literal, Union

StrOrPath = Union[str, PathLike[str], "BasePath"]
BytesLike = Union[bytes, bytearray, memoryview]


class BasePath(PathLike[str]):
    def __init__(self, path: StrOrPath):
        if isinstance(path, BasePath):
            self._path = path._path
        else:
            self._path = Path(path)

    @property
    def path(self) -> Path:
        """Gets the underlying pathlib.Path."""
        return self._path

    @property
    def parent(self) -> "BasePath":
        """
        Gets the logical parent of the path.

        For a filesystem root, returns self.
        """
        parent = self._path.parent
        if parent == self._path:
            return self
        return BasePath(parent)

    @property
    def name(self) -> str:
        """Final path component (same as Path.name)."""
        return self._path.name

    @property
    def stem(self) -> str:
        """Final path component without suffix (same as Path.stem)."""
        return self._path.stem

    @property
    def suffix(self) -> str:
        """File extension including the leading dot, or empty string."""
        return self._path.suffix

    @property
    def suffixes(self) -> list[str]:
        """List of all suffixes (for e.g. '.tar.gz')."""
        return list(self._path.suffixes)

    def is_file(self) -> bool:
        """Return True if this path points to a regular file."""
        return self._path.is_file()

    def is_dir(self) -> bool:
        """Return True if this path points to a directory."""
        return self._path.is_dir()

    def is_symlink(self) -> bool:
        """Return True if this path points to a symbolic link."""
        return self._path.is_symlink()

    def stat(self, *, follow_symlinks: bool = False):
        """
        Return an os.stat_result for this path.

        This is just a thin wrapper around Path.stat().
        """
        return self._path.stat(follow_symlinks=follow_symlinks)

    def exists(self, *, follow_symlinks: bool = False) -> bool:
        """
        Checks if the path exists.

        This method normally follows symlinks;
        to check whether a symlink exists, add the argument follow_symlinks=False.
        """
        return self._path.exists(follow_symlinks=follow_symlinks)

    def create(self, mode: int = 0o777, parents: bool = False, exist_ok: bool = False, *, force_folder: bool = False):
        """
        Creates the path if it doesn't exist.

        For Folder subclasses: creates a directory.
        For other subclasses: creates an empty file.

        :param mode: Only used for `mkdir` use.
        :param parents: If True, creates the parent folders.
        :param exist_ok: If True, then will not raise an exception if already exists.
        """
        from .folder import Folder  # avoid top-level circular import
        if isinstance(self, Folder) or force_folder:
            # Directory semantics
            self._path.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
            return

        # File semantics
        if parents:
            self._path.parent.mkdir(mode=mode, parents=True, exist_ok=True)
        try:
            self._path.open("x").close()
        except FileExistsError:
            if not exist_ok:
                raise
    
    def remove(self, *, follow_symlinks: bool = False, missing_ok: bool = False):
        """
        Delete this path.

        Default behavior is **safe** for symlinks:
        - If this path is a symlink, only the link itself is deleted.
        - If this path is a regular file, it is unlinked.
        - If this path is a directory, it is removed recursively.

        If `follow_symlinks` is True and this path is a symlink, then the
        *target* is deleted (recursively for directories), and the symlink
        is unlinked afterward.
        """
        p = self._path

        # --- Symlink handling first ---
        if p.is_symlink():
            if not follow_symlinks:
                # Safe behavior: remove the link only
                p.unlink(missing_ok=missing_ok)
                return

            # Dangerous behavior: remove the real target
            try:
                target = p.resolve(strict=True)
            except FileNotFoundError:
                # Broken symlink: nothing real to delete, just unlink the link
                p.unlink(missing_ok=missing_ok)
                return

            # Recursively remove the target as a BasePath
            BasePath(target).remove(follow_symlinks=True, missing_ok=missing_ok)

            # Finally remove the symlink itself (may already be dangling)
            p.unlink(missing_ok=missing_ok)
            return

        # --- Non-symlink behavior below ---

        if not p.exists():
            if not missing_ok:
                raise FileNotFoundError("Can't find path '{}'".format(p.name))
            return

        if p.is_file():
            p.unlink(missing_ok=missing_ok)
            return

        # Treat as folder: recursive delete
        folder = self.get_proper(forced="folder")
        try:
            paths = folder.list()
            if paths:
                for path in paths:
                    path.remove(missing_ok=missing_ok)
            p.rmdir()
        except NotADirectoryError:
            # Fallback: if it's actually a file by the time we get here
            if p.is_file():
                p.unlink(missing_ok=missing_ok)

    def get_proper(self, *, forced: Optional[Literal["file", "folder"]] = None):
        """
        Converts this path into a proper path of its respective format.

        If `forced` is "file", the path will be converted to a `File`.
        If `forced` is "folder", the path will be converted to a `Folder`.
        If `forced` is None, the path will be converted based on actual filesystem type.

        If this instance is already the type it'll be converted to,
        then this method returns this instance.
        """
        from .file import File
        from .folder import Folder
        as_file = self._path.is_file() or forced == "file"
        if as_file and forced != "folder":
            return self if isinstance(self, File) else File(self)
        return self if isinstance(self, Folder) else Folder(self)

    # -----------------------------
    # magic methods
    # -----------------------------

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self._path!r})"

    def __str__(self):
        return str(self._path)

    def __fspath__(self):
        return str(self._path)
