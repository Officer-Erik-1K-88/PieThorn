import json
import os
from typing import MutableMapping, Sequence, overload, Iterable, final


class File:
    """Wrap a filesystem path with helpers for tree navigation and I/O."""

    def __init__(self, f_path, children=None, parent=None, sisters=None, find_children=True):
        self._file_path: str = os.path.abspath(f_path)
        self._file_path = self._file_path.replace("\\", "/")
        self._parent = parent
        if sisters is not None and not isinstance(sisters, _Children):
            raise TypeError("Cannot set sisters as anything other than a Children list.")
        self._sisters: _Children = sisters
        self._children = _Children(children)
        if find_children and self.exists():
            self.update_children()

    @property
    def file_path(self):
        """Return the normalized absolute path for this file wrapper."""
        return self._file_path

    @file_path.setter
    def file_path(self, f_path: str):
        """Disallow changing the wrapped path after construction."""
        raise NotImplementedError("This operation doesn't exist... Cannot change the file path of a file.")

    @property
    def parent(self):
        """Return the parent directory as a ``File`` wrapper when available."""
        if self._parent is None and self.exists():
            if "/" in self._file_path:
                splitted = self._file_path.split("/")
                parent_path = "/".join(splitted[0:len(splitted) - 1])
                self._parent = File(parent_path)
                self._sisters = self._parent._children
        return self._parent

    @property
    def children(self):
        """Return a read-only view of discovered child files."""
        return self._children.readonly()

    def update_children(self):
        """Refresh the cached child list when this file represents a directory."""
        if os.path.isdir(self._file_path):
            for f in os.listdir(self._file_path):
                try:
                    child_path = os.path.join(self._file_path, f)
                    self._children.add(File(child_path, parent=self, sisters=self._children))
                except ValueError:
                    pass

    def create_child(self, f, file_content=None):
        """Create, register, and optionally populate a child path beneath this one."""
        file = None
        if isinstance(f, File):
            file = f
        elif isinstance(f, str):
            f = f.replace("\\", "/")
            if not f.startswith(self.file_path):
                f = self.file_path + ("/" if not self.file_path.endswith("/") else "") + f
            file = File(f)
        else:
            raise TypeError(f"Cannot use type({type(f)}) for file path.")
        parent_path = os.path.dirname(file.file_path)
        if parent_path != self.file_path:
            for child in self._children:
                if child.file_path == parent_path:
                    return child.create_child(file, file_content)
        file._sisters = self._children
        file._parent = self
        if not file.file_path.startswith(self.file_path):
            raise ValueError("Cannot install a file as a child if the file path doesn't start with the path of parent.")
        self._children.add(file)
        file.build(file_content)
        return file

    @property
    def sisters(self):
        """Return sibling files from the parent directory when known."""
        return self._sisters.readonly()

    def exists(self):
        """Return whether the wrapped filesystem path exists."""
        return os.path.exists(self.file_path)

    def isfile(self):
        """Return whether the wrapped path should be treated as a file."""
        if not os.path.isfile(self.file_path):
            return "." in self.file_path.split("/")[-1]
        return True

    def isdir(self):
        """Return whether the wrapped path should be treated as a directory."""
        if not os.path.isdir(self.file_path):
            return "." not in self.file_path.split("/")[-1]
        return True

    def build(self, data=None):
        """Create the wrapped file or directory on disk."""
        if not self.exists():
            if self.isfile():
                splitted = self.file_path.split("/")
                dirpath = "/".join(splitted[0:len(splitted)-1])
                os.makedirs(dirpath, exist_ok=True)
                self.write(data, override=True)
            else:
                os.makedirs(self.file_path, exist_ok=True)
        else:
            raise IOError("Cannot build what already exists.")

    def write(self, data, line=-1, insert=True, override=False):
        """Write data to the file, optionally inserting or replacing one line."""
        if data is None:
            data = ""
        if self.isdir():
            raise IsADirectoryError("Cannot write data to a directory.")
        if override:
            with open(self.file_path, "w") as file:
                file.write(data)
            return

        with open(self.file_path, "r") as file:
            lines = file.readlines()

        if line == -1 or line >= len(lines):
            # Append data at the end of the file
            lines.append(data + "\n")
        else:
            if insert:
                # Insert data at specified line, shifting existing content down
                lines.insert(line, data + "\n")
            else:
                # Replace the existing line with new data
                lines[line] = data + "\n"

        with open(self.file_path, "w") as file:
            file.writelines(lines)

    def read(self, hint=-1):
        """Read and return lines from the wrapped file."""
        with open(self.file_path, "r") as file:
            lines = file.readlines(hint)
        return lines

    def rig(self, func, mode="r"):
        """Open the file and pass the file object to ``func``."""
        if callable(func):
            with open(self.file_path, mode) as file:
                ret = func(file)
            return ret
        raise TypeError("func must be callable")

    def __eq__(self, other):
        if isinstance(other, File):
            if self.exists() and other.exists():
                if os.path.samefile(self.file_path, other.file_path):
                    return True
            elif self.file_path == other.file_path:
                return True
        return super().__eq__(other)


@final
class _Children(Sequence[File]):
    def __init__(self, iterable: Iterable[File] = None):
        self._list: list[File] = []
        self._dirs: list[File] = []
        self._files: list[File] = []
        if iterable is not None:
            for f in iterable:
                self.add(f)
        self._readonly = _ReadOnlyChildren(self)

    def readonly(self):
        """Return the cached read-only wrapper around this child collection."""
        return self._readonly

    def view(self):
        """Return all children as a tuple."""
        return tuple(self._list)

    def files(self):
        """Return only child entries that are files."""
        return tuple(self._files)

    def dirs(self):
        """Return only child entries that are directories."""
        return tuple(self._dirs)

    def add(self, f: File):
        """Add a child file wrapper and index it by file-vs-directory type."""
        if f not in self._list:
            self._list.append(f)
            if f.isfile():
                self._files.append(f)
            elif f.isdir():
                self._dirs.append(f)
            else:
                raise OSError("Cannot handle something that isn't a file nor directory.")
        else:
            raise ValueError("The provided file already exist in this children list.")

    @overload
    def __getitem__(self, index: int) -> File:
        return self._list[index]

    @overload
    def __getitem__(self, index: slice) -> Sequence[File]:
        return self._list[index]

    def __getitem__(self, index) -> File:
        if isinstance(index, str):
            path = os.path.abspath(index)
            for f in self._list:
                if os.path.samefile(f.file_path, path):
                    return f
            raise KeyError("The provided path isn't in this list of children.")
        return self._list[index]

    def __len__(self):
        return len(self._list)


class _ReadOnlyChildren(Sequence[File]):
    def __init__(self, children: _Children):
        self._children = children

    def view(self):
        """Return all wrapped children as an immutable tuple."""
        return self._children.view()

    def files(self):
        """Return only wrapped child files."""
        return self._children.files()

    def dirs(self):
        """Return only wrapped child directories."""
        return self._children.dirs()

    def __getitem__(self, index):
        return self._children[index]

    def __len__(self):
        return len(self._children)

# JSON File handling

class JSONEncoder(json.JSONEncoder): # The custom json encoder class
    """Encode JSON with compact primitives and expanded nested structures."""

    def __init__(self, *, skipkeys=False, ensure_ascii=True,
            check_circular=True, allow_nan=True, sort_keys=False,
            indent=None, separators=None, default=None):
        super().__init__(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
            check_circular=check_circular, allow_nan=allow_nan, sort_keys=sort_keys,
            indent=indent, separators=separators, default=default)

    def dumps(self, obj):
        """Creates a default compact JSON string"""
        return json.dumps(
            obj, skipkeys=self.skipkeys, ensure_ascii=self.ensure_ascii,
            check_circular=self.check_circular, allow_nan=self.allow_nan,
            sort_keys=self.sort_keys, indent=None,
            separators=(self.item_separator, self.key_separator),
            default=self.default)

    def _complex(self, o, indent_level=0, markers=None, _one_shot=False):
        """Recursive method to encode objects with proper indentation."""
        # primitive type handling
        if isinstance(o, (str, int, float, bool, type(None))):
            return super().iterencode(o, _one_shot)

        # handle indent
        indent = self.indent
        if indent is not None and not isinstance(indent, str):
            indent = ' ' * indent
        chunks = []
        # list, tuple, dict, and unknown are handled below
        if markers is not None: # implementation of json encoder's check_circular attribute
            markerid = id(o)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = o
        if isinstance(o, (list, tuple)):  # encoding for lists
            if all(isinstance(i, (str, int, float, bool, type(None))) for i in o):
                chunks.append(self.dumps(o))  # Compact formatting for primitive lists
            else: # large form formatting for complex lists
                chunks.append("[\n")
                indent_level += 1
                for i in o:
                    chunks.append(f"{indent * indent_level}")
                    chunks.extend(self._complex(i, indent_level, markers, _one_shot))
                    chunks.append(f"{self.item_separator}\n")
                if chunks[-1].endswith(f"{self.item_separator}\n"):
                    chunks[-1] = chunks[-1].removesuffix(f"{self.item_separator}\n")+"\n"
                indent_level -= 1
                chunks.append(f"{indent * indent_level}]")
        elif isinstance(o, dict): # encode dictionaries
            chunks.append("{\n")
            indent_level += 1
            placeholder = []
            for k, v in o.items():
                if not isinstance(k, (str, int, float, bool, type(None))):
                    if self.skipkeys:
                        continue
                    raise TypeError(f'keys must be str, int, float, bool or None, '
                                    f'not {k.__class__.__name__}')
                group = [f"{indent * indent_level}{self.dumps(k)}{self.key_separator}"]
                group.extend(self._complex(v, indent_level, markers, _one_shot))
                group.append(f"{self.item_separator}\n")
                if self.sort_keys:
                    placeholder.append(group)
                else:
                    chunks.extend(group)
            if self.sort_keys:
                placeholder.sort()
                for group in placeholder:
                    chunks.extend(group)
            if chunks[-1].endswith(f"{self.item_separator}\n"):
                chunks[-1] = chunks[-1].removesuffix(f"{self.item_separator}\n")+"\n"
            indent_level -= 1
            chunks.append((indent * indent_level)+"}")
        else: # handle unknowns the way the json encoder's do it, but with this encoding format.
            o = self.default(o)
            chunks.extend(self._complex(o, indent_level, markers, _one_shot))
        if markers is not None:
            del markers[markerid]
        return chunks

    def iterencode(self, o, _one_shot = False):
        """Yield encoded JSON chunks, honoring the custom indentation strategy."""
        if self.indent is None:
            # Default encoder handling when indent is none.
            return super().iterencode(o, _one_shot)
        markers = {} if self.check_circular else None
        return self._complex(o, 0, markers, _one_shot)



class JSONFile[_VT](MutableMapping[str, _VT]):
    """Persist a mutable mapping to a JSON file or nested JSON object."""

    def __init__(self, f_path: str | File = None, data: dict[str, _VT]=None, mother=None):
        self.encoder = None
        self._file = None
        if data is None:
            data = {}
        self._data: dict[str, _VT] = data
        if mother is not None and not isinstance(mother, JSONFile):
            raise TypeError("The mother argument must be of type JSONFile or is None.")
        self._mother: JSONFile = mother
        self.file = f_path
        if not self.exists():
            self.save()

    @property
    def file(self) -> File | str | None:
        """Return the backing file path or nested key for this JSON view."""
        return self._file

    @file.setter
    def file(self, f_path: str | File):
        """Set the backing file path or nested key for this JSON view."""
        if self.has_mother() and f_path is None:
            raise TypeError("file must not be None as it's this JSON file's key in it's mother JSON file.")
        if isinstance(f_path, str) and not self.has_mother():
            f_path = File(f_path, find_children=False)
        self._file = f_path

    def exists(self):
        """Return whether the backing file or nested JSON key exists."""
        if self.has_path():
            if self.has_mother():
                return self.file in self._mother._data
            return self.file.exists()
        return False

    def has_path(self):
        """Return whether this JSON wrapper is associated with a file or key."""
        return self.file is not None

    def has_mother(self):
        """Return whether this JSON wrapper is nested inside another ``JSONFile``."""
        return self._mother is not None

    def load(self):
        """
        Loads the JSON data from the file.
        """
        if self.has_mother():
            self._data = self._mother[self.file]
        else:
            self._data = self.file.rig(json.load)

    def save(self):
        """
        Saves the stored data of this JSONFile to the file.
        """
        if self.has_mother():
            self._mother[self.file] = self._data
        else:
            self.file.rig(lambda f: json.dump(self._data, f, indent=4, cls=self.encoder), "w")

    def get(self, key: str, default = None):
        """
        Loads the data from the file then
        retrieves the value for a given key.
        Returns a default value if the key is not found.
        """
        self.load()
        return self.fast_get(key, default)

    def fast_get(self, key: str, default = None):
        """
        Retrieves the value for a given key without loading the file.
        Returns a default value if the key is not found.
        """
        value = self._data.get(key, default)
        if isinstance(value, dict) and value != default:
            return JSONFile(key, value, self)
        return value

    def setdefault(self, key: str, default: _VT = None) -> _VT | None:
        """Set and persist ``default`` for ``key`` when it is missing."""
        value = self._data.setdefault(key, default)
        self.save()
        if isinstance(value, dict):
            value = JSONFile(key, value, self)
        return value

    def pop(self, key: str) -> _VT:
        """Remove and persist the value stored at ``key``."""
        value = self._data.pop(key)
        self.save()
        return value

    def popitem(self):
        """Remove and persist the most recent key-value pair."""
        item = self._data.popitem()
        self.save()
        return item

    def clear(self):
        """
        Clears all data from the JSON file.
        """
        self._data.clear()
        self.save()

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, item: str):
        self.load()
        value = self._data[item]
        if isinstance(value, dict):
            value = JSONFile(item, value, self)
        return value

    def __setitem__(self, key: str, value: _VT):
        self._data[key] = value
        self.save()

    def __delitem__(self, key: str):
        del self._data[key]
        self.save()

    def pathed_as(self, other):
        """Return whether another ``JSONFile`` points at the same backing path."""
        if isinstance(other, JSONFile):
            if self.file == other.file:
                if self._mother == other._mother:
                    return True
        return False

    def __eq__(self, other):
        if isinstance(other, JSONFile) and self.pathed_as(other):
            return self._data == other._data
        return False
