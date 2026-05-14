import inspect
from collections import abc as collections_abc
from dataclasses import dataclass
from types import NoneType, UnionType
from typing import (
    Annotated,
    Any,
    ClassVar,
    Final,
    ForwardRef,
    Literal,
    LiteralString,
    Never,
    NoReturn,
    NotRequired,
    Required,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
)

TypeHint: TypeAlias = Any
# TypeVar is not a normal class in every supported Python version, so capture
# the runtime implementation type from a real instance.
_TYPEVAR_TYPE = type(TypeVar("_TYPEVAR_TYPE"))


class UnsupportedTypeHint(TypeError):
    """Raised when a type hint cannot be checked at runtime."""

@dataclass(frozen=True)
class TypeInfo:
    """
    Cached runtime information for a type hint.

    ``typing.get_origin`` and ``typing.get_args`` are cheap, but scattering them
    everywhere makes new hint support hard to add. This class is the one place
    where a raw hint is classified into the facts the checker needs.
    """
    hint: TypeHint
    origin: Any
    args: tuple[Any, ...]

    @classmethod
    def build(cls, hint: TypeHint) -> TypeInfo:
        """Build ``TypeInfo`` for a raw hint."""
        return cls(hint=hint, origin=get_origin(hint), args=get_args(hint))

    def replace(self, hint: TypeHint) -> TypeInfo:
        """Return a fresh ``TypeInfo`` for a related hint."""
        return type(self).build(hint)

    @property
    def is_union(self) -> bool:
        """Whether the hint is PEP 604 union syntax or ``typing.Union``."""
        return self.origin is UnionType or isinstance(self.hint, UnionType) or self.origin is getattr(__import__("typing"), "Union")

    @property
    def is_unpack(self) -> bool:
        """Whether the hint is ``typing.Unpack[...]``."""
        return self.origin is getattr(__import__("typing"), "Unpack")

    @property
    def is_typevar(self) -> bool:
        """Whether the hint is a TypeVar instance."""
        return isinstance(self.hint, _TYPEVAR_TYPE)

    @property
    def is_new_type(self) -> bool:
        """Whether the hint was created with ``typing.NewType``."""
        return callable(self.hint) and hasattr(self.hint, "__supertype__")

    @property
    def is_typed_dict(self) -> bool:
        """Whether the hint is a TypedDict declaration."""
        return (
            isinstance(self.hint, type)
            and issubclass(self.hint, dict)
            and hasattr(self.hint, "__required_keys__")
            and hasattr(self.hint, "__optional_keys__")
            and hasattr(self.hint, "__annotations__")
        )

    @property
    def is_metadata_wrapper(self) -> bool:
        """Whether the hint wraps another hint without changing runtime shape."""
        return self.origin in (Annotated, Final, ClassVar, Required, NotRequired)

    @property
    def is_literal(self) -> bool:
        """Whether the hint is ``Literal[...]``."""
        return self.origin is Literal

    @property
    def is_type_origin(self) -> bool:
        """Whether the hint is ``type`` or ``type[T]``."""
        return self.origin is type

    @property
    def is_callable_origin(self) -> bool:
        """Whether the hint is a Callable alias."""
        return self.origin is collections_abc.Callable

    @property
    def is_tuple_origin(self) -> bool:
        """Whether the hint is a tuple alias."""
        return self.origin is tuple

    @property
    def is_mapping_origin(self) -> bool:
        """Whether the hint's origin behaves like a mapping."""
        return _is_origin_subclass(self.origin, collections_abc.Mapping)

    @property
    def is_sequence_origin(self) -> bool:
        """Whether the hint's origin behaves like a non-string sequence."""
        return (
            _is_origin_subclass(self.origin, collections_abc.Sequence)
            and _valid_iter(self.origin)
        )

    @property
    def is_iterable_origin(self) -> bool:
        """Whether the hint's origin behaves like a non-string iterable."""
        return (
                _is_origin_subclass(self.origin, collections_abc.Iterable)
                and _valid_iter(self.origin)
        )

    @property
    def first_arg(self) -> TypeHint:
        """Return the first argument or Any when no argument was provided."""
        return self.args[0] if self.args else Any

    def unwrap_metadata(self) -> TypeInfo:
        """Strip runtime-neutral wrappers such as Annotated and Required."""
        info = self
        while info.is_metadata_wrapper:
            info = info.replace(info.first_arg)
        return info

def _valid_iter(origin: Any) -> bool:
    """
    Return whether an origin is not valid for sequence or iterable type checking
    even though of sound type.
    """
    return not _is_origin_subclass(origin, (str, bytes, bytearray))


def _is_origin_subclass(origin: Any, parent: Any) -> bool:
    """Safe ``issubclass`` wrapper for origin objects from typing aliases."""
    try:
        return isinstance(origin, type) and issubclass(origin, parent)
    except TypeError:
        return False
