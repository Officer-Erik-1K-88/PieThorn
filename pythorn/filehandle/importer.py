import importlib.util
import inspect
import os
import sys
import functools
from pathlib import Path
from types import ModuleType
from typing import Optional, Iterable, Collection, Callable, Mapping, Any, TypeAlias, TypeVar

HERE = Path(__file__).resolve().parent
LOCAL_SOURCE_DIR = HERE.parent

EMPTY_PATH = Path()
StrPath: TypeAlias = str | os.PathLike[str]

class CallerRoot:
    """Track a discovered project root and its caller-specific children."""

    def __init__(self, path: Path = EMPTY_PATH, source_dir: Optional[StrPath] = None, allow_path_changes=True, allow_source_changes=True):
        self._path = path
        self._source_dir = source_dir
        self._parent: CallerRoot | None = None
        self._children: dict[str, CallerRoot] = dict()
        self._path_can_change = allow_path_changes
        self._source_can_change = allow_source_changes

    @property
    def path(self):
        """Return the tracked project or caller path."""
        return self._path

    @property
    def has_path(self):
        """Return whether a non-empty path has been discovered."""
        return self._path is not None and self._path != EMPTY_PATH

    @path.setter
    def path(self, path):
        """Set the tracked path when path changes are allowed."""
        if self._path_can_change:
            if not isinstance(path, Path):
                if path is None:
                    path = EMPTY_PATH
                else:
                    path = Path(path)
            self._path = path
        else:
            raise RuntimeError(f"Path can't change: {self._path}")

    @property
    def source_dir(self):
        """Return the effective source directory beneath the tracked path."""
        path = self.path
        source_dir = self._source_dir
        if source_dir is not None:
            if path is None:
                return Path(source_dir)
            return path / source_dir
        return path

    @source_dir.setter
    def source_dir(self, source: StrPath | None):
        """Set the relative or absolute source directory when allowed."""
        if self._source_can_change:
            if source is not None and not isinstance(source, StrPath):
                source = str(source)
            self._source_dir = source
        else:
            raise RuntimeError(f"Source can't change: {self._source_dir}")

    @property
    def parent(self):
        """Return the parent ``CallerRoot`` in the discovery tree."""
        return self._parent

    @property
    def children(self) -> Collection[CallerRoot]:
        """Return child caller roots discovered beneath this root."""
        return self._children.values()

    def child(self, path: Path, source_dir: Optional[StrPath] = None):
        """Return or create a cached child root for ``path`` and ``source_dir``."""
        combine_paths = f"{path}-:-{source_dir}"
        child = self._children.setdefault(combine_paths, CallerRoot(path, source_dir))
        child._parent = self
        return child

_PROJECT_ROOT = CallerRoot()

_LIKELY_IN_PROJECT_DIR = (".git", "pyproject.toml", ".venv")


def with_caller_context(*, needs_caller_root: bool = False, check_output: bool = False, out: type=Any):
    """
    Decorator that injects the caller's directory and project root
    into the decorated function's arguments.

    :param needs_caller_root: Defines if the location of the file path of the caller should be passed to the wrapped function as `caller_root`.
    :param check_output: Whether the output of the wrapped function is a ``Mapping`` that should be parsed as controls.
    :param out: The true output type of the wrapped function. Useful for type management.
    """
    out_t = TypeVar("out_t", bound=out)

    def with_caller_context_decor(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> out_t:
            global _PROJECT_ROOT
            caller_dir = EMPTY_PATH

            rescan = kwargs.get("rescan_for_project_root", False)

            if needs_caller_root or rescan:
                # Frame 0: This wrapper
                # Frame 1: The user code calling your package function
                caller_frame = inspect.stack()[1]
                caller_file = caller_frame.filename

                # Absolute path to the caller's directory
                caller_dir = Path(os.path.abspath(os.path.dirname(caller_file)))

            if (not _PROJECT_ROOT.has_path) or rescan:

                # Walk up to find a project root indicator (e.g., .git or pyproject.toml)
                project_root = caller_dir
                found_project_root = False
                for parent in caller_dir.parents:
                    for item in _LIKELY_IN_PROJECT_DIR:
                        if (parent / item).exists():
                            project_root = parent
                            found_project_root = True
                            break
                    if found_project_root:
                        break
                if found_project_root:
                    _PROJECT_ROOT._path = project_root

            # Pass these detected paths into your function
            if needs_caller_root:
                kwargs["caller_root"] = _PROJECT_ROOT.child(caller_dir)
            output = func(*args, project_root=_PROJECT_ROOT, **kwargs)
            if check_output:
                if isinstance(output, Mapping):
                    strict = output.get("strict", False)
                    new_path = output.get("path")
                    new_source = output.get("source")
                    if new_path is not None:
                        try:
                            _PROJECT_ROOT.path = new_path
                        except RuntimeError as e:
                            if strict:
                                raise e
                    if new_source is not None:
                        try:
                            _PROJECT_ROOT.source = new_source
                        except RuntimeError as e:
                            if strict:
                                raise e
                    return output.get("output")
            return output

        return wrapper
    return with_caller_context_decor

@with_caller_context()
def to_path(*args: StrPath, sub_to_source: bool = False, resolve: bool=False, strict:bool=False, project_root: CallerRoot=_PROJECT_ROOT) -> Path:
    """Resolve path fragments relative to the tracked project or source root."""

    source_dir = project_root.source_dir
    path = Path(*args)
    if path.is_absolute():
        if sub_to_source and not path.is_relative_to(source_dir):
            if strict:
                raise RuntimeError("Path not relative to source directory when defined as so")
    else:
        if sub_to_source:
            path = source_dir / path
    if resolve:
        path = path.resolve(strict)
    return path

@with_caller_context(check_output=True, out=bool)
def change_source_dir(source_dir: StrPath, *, path: Optional[Path]=None, strict: bool=False, project_root: CallerRoot=_PROJECT_ROOT):
    """

    :param strict:
    :param source_dir: The path, that is relative to project root, to change the known source directory tp.
    :param path: The path to change the known project directory to.
    :return:
    """
    path = path.resolve() if path is not None else None
    changed = False
    if path is not None and path.is_dir() and path.exists():
        changed = True
    if source_dir is not None:
        if path is None:
            path = project_root.path
        complete_source_dir = path / source_dir
        if complete_source_dir.is_dir() and complete_source_dir.exists():
            source_dir = complete_source_dir
            changed = True
    return {
        "strict": strict,
        "path": path if path is not project_root.path else None,
        "source_dir": source_dir if source_dir is not project_root.source_dir else None,
        "output": changed,
    }

@with_caller_context()
def convert_dot_notation(s: str, *, project_root: CallerRoot=_PROJECT_ROOT) -> str:
    """Convert dotted module notation into an existing project-relative path."""

    s = s.replace(".", "/")
    if (project_root.source_dir/s).exists():
        return s
    s += ".py"
    if (project_root.source_dir/s).exists():
        return s
    raise FileNotFoundError(f"Could not find {project_root.source_dir/s}")


def load_target_module(name: str, path: Path | StrPath, at_local=False) -> ModuleType:
    """Load and register a Python module directly from a filesystem path."""

    if at_local:
        path = LOCAL_SOURCE_DIR / path
    if not isinstance(path, Path):
        path = Path(path)
    # noinspection PyUnresolvedReferences
    if not path.exists():
        raise FileNotFoundError(f"Could not find target file: {path}")

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


class ModuleInfo:
    """Store filesystem-backed metadata for a module and its submodules."""

    def __init__(self, path: Path, *, name: Optional[str]=None, submodules: Optional[Iterable[ModuleInfo]] = None):
        """
        Initialize module metadata for a file system path.

        Args:
            path: Path to the module or package represented by this instance.
            name: Optional module name override. When provided, leading and
                trailing whitespace is removed and spaces are replaced with
                underscores. When omitted, `path.stem` is used.
            submodules: Optional iterable of child `ModuleInfo` objects to
                attach to this module. Each child is linked back to this
                instance as its parent.

        Raises:
            FileNotFoundError: If the resolved `path` does not exist.
        """
        self._name = name.strip().replace(" ", "_") if name is not None else path.stem
        self._path = path.resolve()
        if not self._path.exists():
            raise FileNotFoundError(f"Path not found: {self._path}")

        self._sub_modules: dict[str, ModuleInfo] = {}
        self._parent: Optional[ModuleInfo] = None
        if submodules is not None:
            for submodule in submodules:
                submodule._parent = self
                self._sub_modules[submodule.name] = submodule
        self._module: Module | None = None

    @property
    def import_name(self):
        """Return the dotted import path built from this module's ancestry."""
        name = self._name
        if self._parent is not None:
            parent = self._parent
            while parent is not None:
                name = f"{parent.name}.{name}"
                parent = parent._parent
        return name

    @property
    def name(self):
        """Return the local module name."""
        return self._name

    @property
    def path(self):
        """Return the resolved filesystem path for this module."""
        return self._path

    @property
    def parent(self):
        """Return the parent module info if one exists."""
        return self._parent

    @property
    def sub_modules(self):
        """Return known submodule metadata keyed by module name."""
        return self._sub_modules

    @property
    def module(self):
        """Returns the actual Module instance, building it if necessary."""
        if not self.is_built:
            self._module = Module(module_info=self)
        return self._module

    @property
    def is_built(self):
        """Return whether a runtime ``Module`` wrapper has been created."""
        return self._module is not None

    def build_module(self):
        """
        Builds the module that this class holds information about.

        This method only builds the direct `module` once.
        Refer to `build_submodules` for information in how
        submodules are built.
        :return:
        """
        if not self.is_built:
            self._module = Module(module_info=self)
        self.build_submodules()

    def build_submodules(self):
        """
        Builds the submodules that this class holds information about.

        If `submodule.is_built` is `False`, this method builds the submodule's direct `module` once.
        Otherwise, this method only builds the submodules of the submodule.
        :return:
        """
        for submodule in self._sub_modules.values():
            if submodule.is_built:
                submodule.build_submodules()
            else:
                submodule.build_module()

NO_DELI_ATTRIBUTES = (
    "__class__", "__dict__", "__dir__", "__getattribute__",
    "__module_info__", "__passed_module__",
    "__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__",
)
class Module:
    """Expose a package tree as lazily loaded attributes and submodules."""

    def __init__(self, *args, module_info: Optional[ModuleInfo]=None, **kwargs):
        module_info = module_info if module_info is not None else ModuleInfo(*args, **kwargs)
        if not module_info.is_built:
            module_info._module = self
        path = module_info.path
        self.__module_info__ = module_info
        self.__passed_module__: ModuleType | None = None
        this_module = path / "__init__.py" if path.is_dir() else path
        # Step 1: Load the actual Python code
        if this_module.is_file() and this_module.suffix == ".py":
            import_name = module_info.import_name
            try:
                self.__passed_module__ = load_target_module(import_name, this_module)
            except Exception as e:
                print(f"Failed to load module {this_module}: {e}")
        # Step 2: Map the filesystem hierarchy
        if path.is_dir():
            for item in module_info.path.iterdir():
                if (
                        (item.is_file() and item.suffix == ".py" and item.name != "__init__.py")
                        or
                        (item.is_dir() and (item / "__init__.py").exists())
                ):
                    module_name = item.stem
                    # Register the submodule in the Info tree
                    module_info.sub_modules.setdefault(module_name, ModuleInfo(item))

    def __dir__(self):
        original_dir = super().__dir__()
        new_dir = set(original_dir)
        module: ModuleType | None = super().__getattribute__("__passed_module__")
        if module is not None:
            new_dir.update(module.__dir__())
        module_info: ModuleInfo = super().__getattribute__("__module_info__")
        new_dir.update(module_info.sub_modules.keys())
        return new_dir

    def __getattribute__(self, item):
        if item not in NO_DELI_ATTRIBUTES:
            try:
                module: ModuleType | None = super().__getattribute__("__passed_module__")
                if module is None:
                    raise AttributeError
                return getattr(module, item)
            except AttributeError:
                try:
                    module_info: ModuleInfo = super().__getattribute__("__module_info__")
                    return module_info.sub_modules[item].module
                except (KeyError, AttributeError):
                    pass
        return super().__getattribute__(item)
