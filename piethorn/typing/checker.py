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
    get_origin, Iterable, Sequence,
)

TypeHint: TypeAlias = Any
# TypeVar is not a normal class in every supported Python version, so capture
# the runtime implementation type from a real instance.
_TYPEVAR_TYPE = type(TypeVar("_TYPEVAR_TYPE"))


class UnsupportedTypeHint(TypeError):
    """Raised when a type hint cannot be checked at runtime."""

class UnsupportedTypeHintGroup(ExceptionGroup[TypeError], UnsupportedTypeHint):
    """Raised when a group of ``UnsupportedTypeHint``s are to be raised."""

    def __init__(self, message: str, exceptions: Sequence[TypeError]):
        ExceptionGroup.__init__(self, message, exceptions)

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
        return _is_class(self.origin, (Annotated, Final, ClassVar, Required, NotRequired))

    @property
    def is_literal(self) -> bool:
        """Whether the hint is ``Literal[...]``."""
        return _is_class(self.origin, Literal)

    @property
    def is_type_origin(self) -> bool:
        """Whether the hint is ``type`` or ``type[T]``."""
        return _is_class(self.origin, type)

    @property
    def is_callable_origin(self) -> bool:
        """Whether the hint is a Callable alias."""
        return _is_class(self.origin, collections_abc.Callable)

    @property
    def is_tuple_origin(self) -> bool:
        """Whether the hint is a tuple alias."""
        return _is_subclass(self.origin, tuple)

    @property
    def is_mapping_origin(self) -> bool:
        """Whether the hint's origin behaves like a mapping."""
        return _is_subclass(self.origin, collections_abc.Mapping)

    @property
    def is_sequence_origin(self) -> bool:
        """Whether the hint's origin behaves like a non-string sequence."""
        return (
            _is_subclass(self.origin, collections_abc.Sequence)
            and _valid_iter(self.origin)
        )

    @property
    def is_iterable_origin(self) -> bool:
        """Whether the hint's origin behaves like a non-string iterable."""
        return (
                _is_subclass(self.origin, collections_abc.Iterable)
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


def _unwrap_required(hint: TypeHint) -> TypeHint:
    """Remove Required/NotRequired wrappers from TypedDict value hints."""
    info = TypeInfo.build(hint)
    if info.origin in (Required, NotRequired):
        return info.first_arg
    return hint

def _callable_variadic_arg_hint(hint: TypeHint) -> TypeHint | None:
    """Return T for ``Unpack[tuple[T, ...]]`` callable parameters."""
    info = TypeInfo.build(hint)
    if not info.is_unpack:
        return None
    # Only tuple variadics represent an arbitrary number of positional args.
    if len(info.args) != 1:
        raise UnsupportedTypeHint(f"Unsupported callable parameter hint: {hint!r}")
    unpacked = TypeInfo.build(info.args[0])
    if unpacked.is_tuple_origin and len(unpacked.args) == 2 and unpacked.args[1] is Ellipsis:
        return unpacked.args[0]
    return None


class TypeChecker:
    def __init__(
            self,
            hint: TypeHint,
            *,
            origin_only: bool=False,
            accepts_unpack: bool=False,
            ignore_origin: bool=False,
            tuple_like: bool = False,
            sequence_like: bool = False,
            iterable_like: bool = False,
            map_like: bool = False,
            callable_like: bool = False,
            union_like: bool = False,
            literal_like: bool = False,
            allow_non_type_args: bool=False,
    ):
        self._info = TypeInfo.build(hint)
        self._hint = self._info
        self._origin_only = origin_only
        self._accepts_unpack = accepts_unpack
        self._ignore_origin = ignore_origin

        self._tuple_like = tuple_like
        self._sequence_like = sequence_like or self._tuple_like
        self._iterable_like = iterable_like or self._sequence_like
        self._map_like = map_like
        self._callable_like = callable_like
        self._union_like = union_like
        self._literal_like = literal_like
        self._allow_non_type_args = allow_non_type_args

    @property
    def info(self):
        return self._info

    @property
    def hint(self):
        return self._hint

    @hint.setter
    def hint(self, value):
        if isinstance(value, TypeInfo):
            self._hint = value
        elif value is None:
            self._hint = self.info
        else:
            self._hint = TypeInfo.build(value)

    def _expand_args(self, args=None):
        # Flatten fixed unpacked aliases such as Unpack[tuple[int, str]] into
        # regular positional item hints.
        if args is None:
            args = self.hint.args
        expanded = []
        for item in args:
            if not isinstance(item, type):
                if self._allow_non_type_args:
                    expanded.append(item)
                    continue
                raise UnsupportedTypeHint(f"TypeHint arg not TypeHint when required: {item!r}")
            item_info = TypeInfo.build(item)
            if not item_info.is_unpack:
                expanded.append(item)
                continue

            if not self._accepts_unpack:
                raise UnsupportedTypeHint(f"The type checker for '{self.hint.hint!r}' doesn't support 'typing.Unpack'")

            if len(item_info.args) != 1:
                raise UnsupportedTypeHint(f"Unsupported type hint: {self.hint.hint!r}")
            unpacked = TypeInfo.build(item_info.args[0])
            if unpacked.is_typed_dict:
                expanded.append(unpacked.hint)
                continue

            if unpacked.is_tuple_origin:
                if len(unpacked.args) == 2 and unpacked.args[1] is Ellipsis:
                    if len(args) == 1:
                        expanded = unpacked.args
                        break
                    raise UnsupportedTypeHint(f"Cannot expand variadic tuple in fixed sequence hint: {self.hint.hint!r}")
                expanded.extend(unpacked.args)
                continue

            if unpacked.is_typevar:
                expanded.append(unpacked.hint)
                continue

            raise UnsupportedTypeHint(f"Unsupported unpacked type hint: {item!r}")
        return tuple(expanded)

    def _match_args(
            self,
            value,
            hint_args: Iterable,
            on_type: bool,
            on_args: bool,
            zip_val_hint: bool,
            act_as_any: bool | None=None
    ):
        if act_as_any is None:
            act_as_any = self._union_like

        if on_args:
            if not isinstance(value, Iterable):
                raise TypeError(f"Expected an iterable, got {type(value)!r}")
            if zip_val_hint:
                for item, hint in zip(value, hint_args):
                    if not self._match_args(item, [hint], on_type, False, False, act_as_any):
                        return False
            else:
                for item in value:
                    if not self._match_args(item, hint_args, on_type, False, False, act_as_any):
                        return False
            return True

        check_call = type_check_type if on_type else type_check
        unsupported: list[TypeError] = []
        for option in hint_args:
            try:
                if check_call(value, option):
                    if act_as_any:
                        return True
                else:
                    if not act_as_any:
                        return False
            except (TypeError, UnsupportedTypeHint) as exc:
                if not act_as_any:
                    raise exc
                unsupported.append(exc)
        # Unsupported alternatives should surface loudly instead of silently
        # weakening a union/tuple-of-types check.
        if len(unsupported) != 0:
            if len(unsupported) == 1:
                raise unsupported[0]
            raise UnsupportedTypeHintGroup("TypeHint Unsupported", unsupported)
        return not act_as_any

    def _check_origin(self, value_hint: TypeInfo) -> bool:
        value = value_hint.origin if value_hint.origin is not None else value_hint.hint
        hint = self.hint.origin if self.hint.origin is not None else self.hint.hint
        if hint is Any or value is Any:
            return True
        return _is_class(value, hint)

    def _check_map(self, value):
        key_hint = None
        value_hint = None
        arg_count = len(self.hint.args)
        if arg_count >= 1:
            key_hint = self.hint.args[0]
        if arg_count >= 2:
            value_hint = self.hint.args[1]

        if key_hint is not None:
            key_info = TypeInfo.build(key_hint)
            if key_info.is_unpack:
                # Python uses Unpack[TypedDict] for **kwargs-like shapes. For mapping
                # values, that corresponds to validating the mapping as the TypedDict.
                if len(key_info.args) == 1 and TypeInfo.build(key_info.args[0]).is_typed_dict:
                    old_hint = self.hint
                    self.hint = key_info.args[0]
                    is_type = self.check_value(value)
                    self.hint = old_hint
                    return is_type
                raise UnsupportedTypeHint(f"Unsupported mapping key hint: {key_hint!r}")
            return all(
                type_check(item_key, key_hint) and (type_check(item_value, value_hint) if value_hint is not None else True)
                for item_key, item_value in value.items()
            )

        return False

    def _check_callable(self, value):
        params = self.hint.args[0]
        expected_return = self.hint.args[1] if len(self.hint.args) > 1 else Any
        params = self._expand_args(params)
        try:
            sig = inspect.signature(value, eval_str=True)
        except (NameError, TypeError, ValueError):
            # Some builtins/callable objects do not expose signatures. If Python
            # can call it, accept it rather than guessing.
            return True

        if not (
                expected_return is Any or
                sig.return_annotation is inspect.Signature.empty or
                type_check_type(sig.return_annotation, expected_return)
        ):
            return False
        if params is Ellipsis or not isinstance(params, list):
            return True

        expected_kwargs = None
        last_param_info = TypeInfo.build(params[-1])
        if (
                params and
                last_param_info.is_unpack and
                len(last_param_info.args) == 1 and
                TypeInfo.build(last_param_info.args[0]).is_typed_dict
        ):
            # Callable[[Unpack[TD]], R] models keyword arguments shaped like TD.
            expected_kwargs = get_args(params.pop())[0]
        annotations = getattr(expected_kwargs, "__annotations__", {})
        required_keys = set(getattr(expected_kwargs, "__required_keys__", set()))
        optional_keys = set(getattr(expected_kwargs, "__optional_keys__", set()))
        accepted_keys = set()
        var_keyword = None

        # Check arity and any available parameter annotations in one pass. Missing
        # annotations stay unknown and therefore pass.
        required = 0
        positional_capacity = 0
        param_index = 0
        has_varargs = False
        expected_variadic = False
        expected_min = 0
        for param in params:
            param_arg = _callable_variadic_arg_hint(param)
            if param_arg is not None:
                expected_variadic = True
            else:
                expected_min += 1
        for parameter in sig.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                # A *args parameter can absorb all remaining expected positional
                # hints, including variadic Unpack[tuple[T, ...]].
                has_varargs = True
                while param_index < len(params):
                    expected_hint = _callable_variadic_arg_hint(params[param_index]) or params[param_index]
                    if not type_check_type(expected_hint, parameter.annotation):
                        return False
                    param_index += 1
            if parameter.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                # Fixed positional parameters consume expected hints one-for-one.
                positional_capacity += 1
                if parameter.default is inspect.Parameter.empty:
                    required += 1
                if param_index < len(params):
                    expected_hint = _callable_variadic_arg_hint(params[param_index]) or params[param_index]
                    if not type_check_type(expected_hint, parameter.annotation):
                        return False
                    param_index += 1
            if expected_kwargs is not None:
                if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                    # **kwargs can accept any key, but its annotation still constrains
                    # all values from the TypedDict.
                    var_keyword = parameter
                if parameter.kind in (
                        inspect.Parameter.KEYWORD_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ):
                    # Named parameters can satisfy matching TypedDict keys directly.
                    accepted_keys.add(parameter.name)
                    if parameter.name in annotations:
                        expected = _unwrap_required(annotations[parameter.name])
                        if not type_check_type(expected, parameter.annotation):
                            return False

        if expected_variadic and not has_varargs:
            return False
        expected = expected_min if expected_variadic else len(params)
        if not (required <= expected and (has_varargs or expected <= positional_capacity)):
            return False

        if var_keyword is not None:
            if var_keyword.annotation is inspect.Signature.empty:
                return True
            return all(
                type_check_type(_unwrap_required(annotations[key]), var_keyword.annotation)
                for key in required_keys | optional_keys
            )

        if expected_kwargs is not None:
            return required_keys.issubset(accepted_keys)
        return True

    def check_value(self, value: Any) -> bool:
        if self._origin_only and not self._ignore_origin:
            # This exists because many type checks should be
            # carried out in a similar fashion to using `isinstance`.
            return self._check_origin(TypeInfo.build(type(value)))

        # The following if statements are to insure proper type checking
        # on some types.
        if self.hint.hint is Any:
            return True
        if self.hint.hint in (object, type):
            return isinstance(value, self.hint.hint)
        if self.hint.hint in (None, NoneType):
            return value is None
        if self.hint.hint in (NoReturn, Never):
            return False
        if self.hint.hint is LiteralString:
            return isinstance(value, str)
        if isinstance(self.hint.hint, str) or isinstance(self.hint.hint, ForwardRef):
            # There is not enough local context here to resolve names safely.
            raise UnsupportedTypeHint(f"Forward references are not supported at runtime: {self.hint.hint!r}")

        # These forms masquerade as callables/classes in different Python
        # versions, so handle them before generic origin-based dispatch.
        if self.hint.is_typevar:
            constraints = getattr(self.hint.hint, "__constraints__", ())
            if constraints:
                # Constrained TypeVars behave like a union of their constraints.
                return self._match_args(value, constraints, True, False, False, True)
            bound = getattr(self.hint.hint, "__bound__", None)
            if bound is not None:
                # Bounded TypeVars accept anything compatible with the bound.
                return type_check(value, bound)
            return True
        if self.hint.is_new_type:
            old_hint = self.hint
            self.hint = self.hint.hint.__supertype__
            is_type = self.check_value(value)
            self.hint = old_hint
            return is_type
        if self.hint.is_typed_dict:
            # TypedDict is structural at runtime: the value is still a normal mapping,
            # so validate the declared key set and each present value.
            required_keys = set(getattr(self.hint.hint, "__required_keys__", set()))
            optional_keys = set(getattr(self.hint.hint, "__optional_keys__", set()))
            annotations = getattr(self.hint.hint, "__annotations__", {})
            allowed_keys = required_keys | optional_keys

            if not required_keys.issubset(value.keys()):
                return False
            if any(key not in allowed_keys for key in value.keys()):
                return False

            for key, key_hint in annotations.items():
                if key in value and not type_check(value[key], _unwrap_required(key_hint)):
                    return False
            return True

        if self.hint.is_metadata_wrapper:
            # Metadata wrappers do not change the runtime value shape.
            old_hint = self.hint
            self.hint = self.hint.first_arg
            is_type = self.check_value(value)
            self.hint = old_hint
            return is_type

        # The rest of the check_value method is used to type check for almost
        # any possible type.
        if not self._ignore_origin:
            if not self._check_origin(TypeInfo.build(type(value))):
                return False
            if self._origin_only:
                return True

        if self._map_like:
            if self._check_map(value):
                return True

        if self._callable_like:
            if not callable(value):
                return False

        if self._iterable_like or self._callable_like:
            if len(self.hint.args) == 0:
                return True

        if self._callable_like:
            if self._check_callable(value):
                return True

        if self._tuple_like:
            # tuple[()] is the dedicated spelling for the empty tuple.
            if self.hint.args == ((),):
                return len(value) == 0

        expanded = self._expand_args()

        if self._iterable_like:
            if len(expanded) == 0:
                return True
            if (self._tuple_like and len(expanded) == 2 and expanded[1] is Ellipsis) or not self._tuple_like:
                # tuple[T, ...] validates every item against the same hint.
                if self._match_args(value, [expanded[0]], True, True, False):
                    return True
                if self._tuple_like:
                    return False

        if self._tuple_like:
            if len(value) == len(expanded):
                if self._match_args(value, expanded, True, True, True):
                    return True

        if self._literal_like:
            if value in expanded:
                return True

        if self._union_like:
            if self._match_args(value, expanded, True, False, False):
                return True

        return len(expanded) == 0

    def check_hint(self, value_hint: TypeHint | TypeInfo):
        if not isinstance(value_hint, TypeInfo):
            value_hint = TypeInfo.build(value_hint)
        if not self._check_origin(value_hint):
            return False
        if self._origin_only:
            return True
        return False

AnyType = TypeChecker(Any, origin_only=True) # This type is not in `TYPES` because `Any` will always come out as true
TYPES: list[TypeChecker] = []

Hint: TypeAlias = TypeHint | TypeInfo | TypeChecker
Hint = Hint | tuple[Hint, ...]

def get_type_checker(hint: TypeHint | TypeInfo | TypeChecker, default:TypeChecker | None=AnyType) -> TypeChecker:
    if isinstance(hint, TypeChecker):
        return hint
    if not isinstance(hint, TypeInfo):
        hint = TypeInfo.build(hint)
    for type_checker in TYPES:
        if type_checker.check_hint(hint):
            return type_checker
    if default is None:
        raise UnsupportedTypeHint(f"Unsupported TypeHint: {hint.hint!r}")
    return default

def type_check(value, hint: Hint) -> bool:
    if isinstance(hint, tuple):
        for h in hint:
            if type_check(value, h):
                return True
        return False
    this_hint = get_type_checker(hint, None)
    this_hint.hint = hint
    is_type = this_hint.check_value(value)
    this_hint.hint = None
    return is_type

def type_check_type(value, hint: Hint) -> bool:
    if isinstance(hint, tuple):
        for h in hint:
            if type_check_type(value, h):
                return True
        return False
    this_hint = get_type_checker(hint)
    this_hint.hint = hint
    is_type = this_hint.check_hint(value)
    this_hint.hint = None
    return is_type


def _valid_iter(origin: Any) -> bool:
    """
    Return whether an origin is not valid for sequence or iterable type checking
    even though of sound type.
    """
    return not _is_subclass(origin, (str, bytes, bytearray))


def _is_subclass(origin: Any, parent: Any) -> bool:
    """Safe ``issubclass`` wrapper for origin objects from typing aliases."""
    try:
        return isinstance(origin, type) and issubclass(origin, parent)
    except TypeError:
        return False

def _is_class(origin: Any, parent: Any) -> bool:
    if isinstance(parent, tuple):
        for item in parent:
            if _is_class(origin, item):
                return True
        return False
    try:
        return origin is parent
    except TypeError:
        return False
