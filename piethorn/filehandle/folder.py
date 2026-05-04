from typing import List, Iterable

from .path import BasePath, StrOrPath
from .file import File


class Folder(BasePath):
    def __init__(self, path: StrOrPath, *, create: bool = False, must_exist: bool = False):
        """
        Initialize the Folder with a path.

        :param create:
            If True, create the folder (and parents) if it does not exist.
        :param must_exist:
            If True, raise NotADirectoryError if the path does not exist
            or is not a directory.
        """
        super().__init__(path)

        if create and not self._path.exists():
            self._path.mkdir(parents=True, exist_ok=True)

        if must_exist:
            # Now enforce that it's a directory.
            if not self._path.exists():
                raise FileNotFoundError(f"Path '{self._path}' does not exist.")
            if not self._path.is_dir():
                raise NotADirectoryError(f"Path '{self._path}' is not a directory.")

    @property
    def size(self) -> int:
        """
        Total size, in bytes, of all files in this folder and its subfolders.

        Files that disappear during traversal are silently skipped.
        """
        total = 0
        for _, _, files in self.walk():
            for f in files:
                try:
                    total += f.size
                except FileNotFoundError:
                    # File was removed between listing and stat; ignore.
                    continue
        return total

    def ensure(self) -> "Folder":
        """
        Ensure that this folder exists on disk.

        Creates the directory (and parents) if necessary, and returns self
        for convenient chaining.
        """
        self.path.mkdir(parents=True, exist_ok=True)
        return self

    def walk(self) -> Iterable[tuple["Folder", list["Folder"], list[File]]]:
        """
        Recursively walk this folder, yielding (folder, subfolders, files)
        tuples similar to os.walk().

        The first yielded element is always (self, [...], [...]).
        """
        stack: list[Folder] = [self]
        while stack:
            current = stack.pop()
            subfolders: list[Folder] = []
            files: list[File] = []

            for entry in current.list(files=True, folders=True):
                if isinstance(entry, File):
                    files.append(entry)
                elif isinstance(entry, Folder):
                    subfolders.append(entry)

            # Depth-first traversal: you can reverse if you care about order
            stack.extend(reversed(subfolders))
            yield current, subfolders, files

    def list(self, *, files: bool = True, folders: bool = True) -> List[BasePath]:
        """
        List the folder contents.
        :param files: Include files in the output
        :param folders: Include subfolders in the output
        :return: A list of BasePath objects
        """
        if not self._path.is_dir():
            # Optional: be explicit when the folder doesn't exist or isn't a dir.
            raise NotADirectoryError(f"Path '{self._path}' is not a directory.")
        output = []
        for item in self.path.iterdir():
            if item.is_file() and files:
                output.append(File(item))
            elif item.is_dir() and folders:
                output.append(Folder(item))
        return output

    def delete(self, name: str):
        """
        Delete a file or folder inside this folder.

        Currently, a best-effort delete: if the target doesn't exist, nothing happens.
        """
        target = BasePath(self.path / name)
        if target.exists():
            target.remove()
        # If you want this to be strict, raise if not exists instead.

    def file(self, name: str, *, create: bool = False, must_exist: bool = False) -> File:
        """
        Return a File object representing a file inside this folder.

        :param name: The name of the file.
        :param create: If True, create the file if missing.
        :param must_exist: If True, require the file to exist already.
        """
        return File(self.path / name, create=create, must_exist=must_exist)

    def subfolder(self, name: str, *, create: bool = False, must_exist: bool = False) -> "Folder":
        """
        Return a Folder object representing a subfolder.

        :param name: The name of the subfolder.
        :param create: If True, create the subfolder if missing.
        :param must_exist: If True, require the subfolder to exist already.
        """
        return Folder(self.path / name, create=create, must_exist=must_exist)
