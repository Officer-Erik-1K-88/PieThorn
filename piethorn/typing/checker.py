import builtins
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
    get_origin, Iterable, Sequence, Callable, Union, Unpack, Mapping,
)

TypeHint: TypeAlias = Any
# TypeVar is not a normal class in every supported Python version, so capture
# the runtime implementation type from a real instance.
_TYPEVAR_TYPE = type(TypeVar("_TYPEVAR_TYPE"))


class UnsupportedTypeHint(TypeError):
    """
    Raised when a type hint cannot be checked at runtime.

    The checker raises this when a hint cannot be resolved into a supported
    runtime strategy. This is different from a normal ``False`` result: a
    ``False`` result means the hint was understood and did not match, while
    this exception means the hint was not supported by this checker.

    Args:
        *args: Standard ``TypeError`` message arguments.
    """

class UnsupportedTypeHintGroup(ExceptionGroup[TypeError], UnsupportedTypeHint):
    """
    Raised when multiple type-hint checks fail for unsupported-hint reasons.

    This is used for union-like paths where several alternatives may be tried
    before the checker can decide that none of the alternatives were supported.
    Grouping preserves every underlying failure instead of hiding useful detail
    behind the last exception.

    Args:
        message: Human-readable message for the grouped failure.
        exceptions: The unsupported-hint errors collected while checking.
    """

    def __init__(self, message: str, exceptions: Sequence[TypeError]):
        """
        Build an unsupported-hint exception group.

        Args:
            message: Message passed to ``ExceptionGroup``.
            exceptions: Individual ``TypeError`` instances to group.

        Returns:
            None.

        Raises:
            TypeError: If ``ExceptionGroup`` rejects the supplied exception
                sequence.
        """
        ExceptionGroup.__init__(self, message, exceptions)

@dataclass(frozen=True)
class TypeInfo:
    """
    Cached runtime information for a type hint.

    ``typing.get_origin`` and ``typing.get_args`` are cheap, but scattering them
    everywhere makes new hint support hard to add. This class is the one place
    where a raw hint is classified into the facts the checker needs.

    Attributes:
        hint: Original hint object.
        origin: Result of ``typing.get_origin(hint)``.
        args: Result of ``typing.get_args(hint)``.
    """
    hint: TypeHint
    origin: Any
    args: tuple[Any, ...]

    @classmethod
    def build(cls, hint: TypeHint) -> TypeInfo:
        """
        Build ``TypeInfo`` for a raw hint.

        Args:
            hint: Raw type hint to inspect.

        Returns:
            A cached ``TypeInfo`` snapshot for ``hint``.
        """
        return cls(hint=hint, origin=get_origin(hint), args=get_args(hint))

    def replace(self, hint: TypeHint) -> TypeInfo:
        """
        Return a fresh ``TypeInfo`` for a related hint.

        Args:
            hint: Replacement raw hint.

        Returns:
            A new ``TypeInfo`` built from ``hint``.
        """
        return type(self).build(hint)

    @property
    def is_union(self) -> bool:
        """
        Whether the hint is PEP 604 union syntax or ``typing.Union``.

        Returns:
            ``True`` for hints such as ``int | str`` and ``typing.Union[int,
            str]``. Returns ``False`` for non-union hints.
        """
        return self.origin is UnionType or isinstance(self.hint, UnionType) or self.origin is Union

    @property
    def is_unpack(self) -> bool:
        """
        Whether the hint is ``typing.Unpack[...]``.

        Returns:
            ``True`` when ``typing.get_origin`` identifies the hint as
            ``Unpack``. Returns ``False`` otherwise.
        """
        return self.origin is Unpack

    @property
    def is_typevar(self) -> bool:
        """
        Whether the hint is a TypeVar instance.

        Returns:
            ``True`` when the raw hint has the runtime TypeVar implementation
            type. Returns ``False`` otherwise.
        """
        return isinstance(self.hint, _TYPEVAR_TYPE)

    @property
    def is_new_type(self) -> bool:
        """
        Whether the hint was created with ``typing.NewType``.

        Returns:
            ``True`` when the hint is callable and exposes ``__supertype__``.
            Returns ``False`` for ordinary callables/classes.
        """
        return callable(self.hint) and hasattr(self.hint, "__supertype__")

    @property
    def is_typed_dict(self) -> bool:
        """
        Whether the hint is a TypedDict declaration.

        Returns:
            ``True`` when the hint is a dict subclass with TypedDict key
            metadata and annotations. Returns ``False`` for normal dict classes
            and mapping aliases.
        """
        return (
            isinstance(self.hint, type)
            and issubclass(self.hint, dict)
            and hasattr(self.hint, "__required_keys__")
            and hasattr(self.hint, "__optional_keys__")
            and hasattr(self.hint, "__annotations__")
        )

    @property
    def is_metadata_wrapper(self) -> bool:
        """
        Whether the hint wraps another hint without changing runtime shape.

        Returns:
            ``True`` for wrappers such as ``Annotated``, ``Final``, ``ClassVar``,
            ``Required``, and ``NotRequired``. Returns ``False`` otherwise.
        """
        return _is_class(self.origin, (Annotated, Final, ClassVar, Required, NotRequired))

    @property
    def is_literal(self) -> bool:
        """
        Whether the hint is ``Literal[...]``.

        Returns:
            ``True`` when the hint's origin is ``Literal``. Returns ``False``
            otherwise.
        """
        return _is_class(self.origin, Literal)

    @property
    def is_type_origin(self) -> bool:
        """
        Whether the hint is ``type`` or ``type[T]``.

        Returns:
            ``True`` when the hint's origin is ``type``. Returns ``False`` for
            non-class-object hints.
        """
        return _is_class(self.origin, type)

    @property
    def is_callable_origin(self) -> bool:
        """
        Whether the hint is a Callable alias.

        Returns:
            ``True`` when the hint origin is compatible with
            ``collections.abc.Callable``. Returns ``False`` otherwise.
        """
        return _is_class(self.origin, collections_abc.Callable)

    @property
    def is_tuple_origin(self) -> bool:
        """
        Whether the hint is a tuple alias.

        Returns:
            ``True`` when the hint origin is a tuple subclass. Returns ``False``
            otherwise.
        """
        return _is_subclass(self.origin, tuple)

    @property
    def is_mapping_origin(self) -> bool:
        """
        Whether the hint's origin behaves like a mapping.

        Returns:
            ``True`` when the origin is a ``collections.abc.Mapping`` subclass.
            Returns ``False`` otherwise.
        """
        return _is_subclass(self.origin, collections_abc.Mapping)

    @property
    def is_sequence_origin(self) -> bool:
        """
        Whether the hint's origin behaves like a non-string sequence.

        Returns:
            ``True`` when the origin is a sequence and is not treated as a
            scalar string-like type by this checker.
        """
        return (
            _is_subclass(self.origin, collections_abc.Sequence)
            and _valid_iter(self.origin)
        )

    @property
    def is_iterable_origin(self) -> bool:
        """
        Whether the hint's origin behaves like a non-string iterable.

        Returns:
            ``True`` when the origin is iterable and is not treated as a scalar
            string-like type by this checker.
        """
        return (
                _is_subclass(self.origin, collections_abc.Iterable)
                and _valid_iter(self.origin)
        )

    @property
    def first_arg(self) -> TypeHint:
        """
        Return the first argument or ``Any`` when no argument was provided.

        Returns:
            ``self.args[0]`` when at least one argument exists. Otherwise
            returns ``Any`` as a permissive default.
        """
        return self.args[0] if self.args else Any

    def unwrap_metadata(self) -> TypeInfo:
        """
        Strip runtime-neutral metadata wrappers.

        Returns:
            A ``TypeInfo`` for the first non-wrapper hint inside chains such as
            ``Annotated[Final[int], ...]`` or ``Required[Annotated[str, ...]]``.
        """
        info = self
        while info.is_metadata_wrapper:
            # Every supported wrapper stores its wrapped type as the first arg.
            info = info.replace(info.first_arg)
        return info


def _unwrap_required(hint: TypeHint) -> TypeHint:
    """
    Remove ``Required`` and ``NotRequired`` wrappers from a TypedDict value hint.

    Args:
        hint: A raw type hint that may be wrapped by ``Required`` or
            ``NotRequired``.

    Returns:
        The wrapped inner hint when a required-key wrapper is present.
        Otherwise, returns ``hint`` unchanged.
    """
    info = TypeInfo.build(hint)
    if info.origin in (Required, NotRequired):
        return info.first_arg
    return hint

def _callable_variadic_arg_hint(hint: TypeHint) -> TypeHint | None:
    """
    Return the variadic item hint from a callable parameter hint.

    Args:
        hint: A parameter hint from a ``Callable`` arg list.

    Returns:
        ``T`` when ``hint`` is ``Unpack[tuple[T, ...]]``. Returns ``None`` when
        ``hint`` is not an unpacked variadic tuple.

    Raises:
        UnsupportedTypeHint: If ``hint`` is an ``Unpack`` form that this
            callable checker cannot interpret.
    """
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


def _is_type_hint_arg(info: TypeInfo) -> bool:
    """
    Return whether ``info`` describes a type-hint argument.

    Args:
        info: Cached information for one item returned by ``typing.get_args``.

    Returns:
        ``True`` when the argument is itself a type hint, such as ``int``,
        ``dict[str, int]``, ``T``, ``Any``, or a forward reference. Returns
        ``False`` for runtime metadata values such as the ``1`` in
        ``Literal[1]``.
    """
    special_hints = (Any, None, NoneType, NoReturn, Never, LiteralString, inspect.Signature.empty)
    return (
            isinstance(info.hint, type)
            or info.origin is not None
            or info.is_typevar
            or info.is_new_type
            or isinstance(info.hint, (str, ForwardRef, UnionType))
            or any(info.hint is special_hint for special_hint in special_hints)
    )


class TypeChecker:
    """
    Runtime checker for one family of type hints.

    Args:
        hint: The template hint this checker is built around. Registry checkers
            use this as their family hint, while fallback checkers use the
            caller's unsupported hint directly.
        auto_detect_flags: When true, infer structural flags from ``hint``.
        origin_only: When true, checking stops after compatible origin.
        accepts_unpack: Whether ``_expand_args`` may consume ``Unpack``.
        ignore_origin: Whether structural arg checks may succeed without origin
            compatibility.
        tuple_like: Whether tuple fixed/variadic arg rules apply.
        sequence_like: Whether homogeneous sequence rules apply.
        iterable_like: Whether homogeneous iterable rules apply.
        map_like: Whether key/value mapping rules apply.
        callable_like: Whether callable parameter/return rules apply.
        union_like: Whether union alternative rules apply.
        literal_like: Whether literal value rules apply.
        allow_non_type_args: Whether runtime metadata args are allowed.

    Attributes:
        info: The immutable template ``TypeInfo`` for this checker.
        hint: The active ``TypeInfo`` currently being checked.
    """

    def __init__(
            self,
            hint: TypeHint | TypeInfo,
            auto_detect_flags: bool = False,
            *,
            origin_only: bool = False,
            accepts_unpack: bool = False,
            ignore_origin: bool = False,
            tuple_like: bool = False,
            sequence_like: bool = False,
            iterable_like: bool = False,
            map_like: bool = False,
            callable_like: bool = False,
            union_like: bool = False,
            literal_like: bool = False,
            allow_non_type_args: bool = False,
    ):
        """
        Build a checker for ``hint``.

        Args:
            hint: The family hint or active fallback hint.
            auto_detect_flags: Infer flags from ``hint`` for fallback checkers.
            origin_only: Stop checks after origin compatibility.
            accepts_unpack: Permit supported ``typing.Unpack`` expansion.
            ignore_origin: Let structural checks decide compatibility without
                origin compatibility.
            tuple_like: Enable tuple-specific checks.
            sequence_like: Enable sequence-style item checks.
            iterable_like: Enable iterable-style item checks.
            map_like: Enable mapping key/value checks.
            callable_like: Enable callable parameter/return checks.
            union_like: Enable union alternative checks.
            literal_like: Enable literal payload checks.
            allow_non_type_args: Permit non-type metadata args such as literal
                values.

        Returns:
            None.
        """
        if isinstance(hint, TypeChecker):
            hint = hint.hint
        if not isinstance(hint, TypeInfo):
            hint = TypeInfo.build(hint)
        self._info = hint
        self._hint = self._info

        if auto_detect_flags:
            # Plain, non-parameterized hints can be checked with origin alone.
            origin_only = len(self._info.args) == 0
            # Tuple gets its own flag because tuple hints may be fixed length.
            tuple_like = self._info.is_tuple_origin
            # Sequence implies iterable behavior through the stored flags below.
            sequence_like = self._info.is_sequence_origin
            # Iterable is the fallback for set/range/generator-like shapes.
            iterable_like = self._info.is_iterable_origin
            # Mapping has key/value semantics instead of item-only semantics.
            map_like = self._info.is_mapping_origin
            # Callable checks parameter lists and return hints.
            callable_like = self._info.is_callable_origin
            # Union checks each alternative as a possible match.
            union_like = self._info.is_union
            # Literal checks runtime payload values instead of type origins.
            literal_like = self._info.is_literal
            # Literal args are values, not type hints.
            allow_non_type_args = literal_like
            # These forms are defined by args more than by origin.
            ignore_origin = literal_like or union_like or callable_like
            # Only structural shapes know where Unpack should be applied.
            accepts_unpack = (
                    tuple_like or
                    sequence_like or
                    iterable_like or
                    map_like or
                    callable_like or
                    union_like
            )

        self._origin_only = origin_only
        self._accepts_unpack = accepts_unpack
        self._ignore_origin = ignore_origin

        # Tuple is also a sequence.
        self._tuple_like = tuple_like
        self._sequence_like = sequence_like or self._tuple_like
        # Sequence is also iterable.
        self._iterable_like = iterable_like or self._sequence_like
        self._map_like = map_like
        self._callable_like = callable_like
        self._union_like = union_like
        self._literal_like = literal_like
        self._allow_non_type_args = allow_non_type_args

        # Shape flags are the only flags that interpret generic args.
        self._has_flags = (
                self._tuple_like or
                self._sequence_like or
                self._iterable_like or
                self._map_like or
                self._callable_like or
                self._union_like or
                self._literal_like
        )

    @property
    def info(self):
        """The template ``TypeInfo`` this checker was constructed with."""
        return self._info

    @property
    def hint(self):
        """The active ``TypeInfo`` currently being checked."""
        return self._hint

    @hint.setter
    def hint(self, value):
        """
        Set the active hint for a reusable checker.

        Args:
            value: A ``TypeChecker``, ``TypeInfo``, raw type hint, or ``None``.
                ``None`` resets the active hint back to ``self.info``.

        Returns:
            None.
        """
        # ``None`` resets a reusable registry checker to its template hint.
        if isinstance(value, TypeChecker):
            # Keep the active hint from another checker, not its template.
            self._hint = value.hint
        elif isinstance(value, TypeInfo):
            # TypeInfo is already normalized and can be stored directly.
            self._hint = value
        elif value is None:
            self._hint = self.info
        else:
            # Raw hints are normalized once at assignment time.
            self._hint = TypeInfo.build(value)

    def _expand_args(self, args=None):
        """
        Return normalized hint args, expanding supported ``Unpack`` forms.

        Args:
            args: Optional argument sequence to expand. When omitted,
                ``self.hint.args`` is used.

        Returns:
            A tuple of normalized arguments. Fixed tuple ``Unpack`` aliases are
            flattened. ``Unpack[tuple[T, ...]]`` is preserved as ``(T,
            Ellipsis)`` when it is the entire arg list.

        Raises:
            UnsupportedTypeHint: If an arg is runtime metadata and
                ``allow_non_type_args`` is false, if ``Unpack`` appears in a
                checker that does not accept it, or if the unpacked shape cannot
                be represented by this checker.
        """
        if args is None:
            # Default to the active hint's arguments.
            args = self.hint.args
        expanded = []
        for item in args:
            item_info = TypeInfo.build(item)
            # Literal values and other metadata require an explicit opt-in.
            if not _is_type_hint_arg(item_info):
                if not self._allow_non_type_args:
                    raise UnsupportedTypeHint(f"TypeHint arg not TypeHint when required: {item!r}")
                expanded.append(item)
                continue
            if not item_info.is_unpack:
                # Normal type-hint args are already usable.
                expanded.append(item)
                continue

            # Only structural checkers can give Unpack a concrete meaning.
            if not self._accepts_unpack:
                raise UnsupportedTypeHint(f"The type checker for '{self.hint.hint!r}' doesn't support 'typing.Unpack'")

            if len(item_info.args) != 1:
                raise UnsupportedTypeHint(f"Unsupported type hint: {self.hint.hint!r}")
            unpacked = TypeInfo.build(item_info.args[0])
            if unpacked.is_typed_dict:
                # Mapping/callable code applies TypedDict keyword-shape rules.
                expanded.append(unpacked.hint)
                continue

            if unpacked.is_tuple_origin:
                # Tuple unpacking is the only fixed positional expansion here.
                if len(unpacked.args) == 2 and unpacked.args[1] is Ellipsis:
                    # Variadic tuple unpacking cannot mix with fixed args.
                    if len(args) == 1:
                        expanded = unpacked.args
                        break
                    raise UnsupportedTypeHint(f"Cannot expand variadic tuple in fixed sequence hint: {self.hint.hint!r}")
                expanded.extend(unpacked.args)
                continue

            if unpacked.is_typevar:
                # Preserve the TypeVar for its own constraint/bound handling.
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
        """
        Match one value or hint against one or more hint arguments.

        Args:
            value: Runtime value or type hint to check.
            hint_args: Candidate hints to compare against.
            on_type: Use ``type_check`` when true. Use ``type_check_type`` when
                false.
            on_args: When true, ``value`` is treated as an iterable of
                values/hints and every item is checked.
            zip_val_hint: When true, pair each item in ``value`` with the hint
                at the same position. When false, every item is checked against
                all ``hint_args``.
            act_as_any: Whether any candidate hint may match. Defaults to this
                checker's ``union_like`` flag.

        Returns:
            ``True`` when the value or hint matches the requested arg policy.
            ``False`` when it is supported but incompatible.

        Raises:
            TypeError: If ``on_args`` is true and ``value`` is not iterable.
            UnsupportedTypeHint: If a required nested hint check is unsupported.
            UnsupportedTypeHintGroup: If multiple alternatives are unsupported.
        """
        if act_as_any is None:
            act_as_any = self._union_like

        if on_args:
            if not isinstance(value, Iterable):
                raise TypeError(f"Expected an iterable, got {type(value)!r}")
            if zip_val_hint:
                # Positional matching: value[i] must satisfy hint_args[i].
                for item, hint in zip(value, hint_args):
                    if not self._match_args(item, [hint], on_type, False, False, act_as_any):
                        return False
            else:
                # Homogeneous/union matching: each item may use any hint arg.
                for item in value:
                    if not self._match_args(item, hint_args, on_type, False, False, act_as_any):
                        return False
            return True

        check_call = type_check if on_type else type_check_type
        unsupported: list[TypeError] = []
        for option in hint_args:
            try:
                # ``act_as_any`` means one successful option is enough.
                if check_call(value, option):
                    if act_as_any:
                        return True
                else:
                    # Without union-like behavior, the first mismatch fails.
                    if not act_as_any:
                        return False
            except (TypeError, UnsupportedTypeHint) as exc:
                if not act_as_any:
                    raise exc
                # In union-like mode, collect unsupported options and continue.
                unsupported.append(exc)
        # Unsupported alternatives should surface loudly instead of silently
        # weakening a union/tuple-of-types check.
        if len(unsupported) != 0:
            if len(unsupported) == 1:
                raise unsupported[0]
            raise UnsupportedTypeHintGroup("TypeHint Unsupported", unsupported)
        return not act_as_any

    def _check_origin(self, value_hint: TypeInfo) -> bool:
        """
        Return whether ``value_hint`` has an origin compatible with ``hint``.

        Args:
            value_hint: Cached information for the candidate runtime type or
                candidate type hint.

        Returns:
            ``True`` when origins are identical, when the candidate origin is a
            subclass of the active hint origin, or when either side is ``Any``.
            Otherwise returns ``False``.
        """
        value = value_hint.origin if value_hint.origin is not None else value_hint.hint
        hint = self.hint.origin if self.hint.origin is not None else self.hint.hint
        if hint is Any or value is Any:
            return True
        if _is_class(value, hint):
            # Exact origin match.
            return True
        # Subclass origin match, e.g. list against Sequence.
        return _is_subclass(value, hint)

    def _check_hint_map(self, value_hint: TypeInfo) -> bool:
        """
        Compare mapping key/value hints against this checker's map hint.

        Args:
            value_hint: Cached information for the candidate mapping hint.

        Returns:
            ``True`` when the candidate key/value hints are compatible with the
            active mapping key/value hints. Returns ``False`` when the candidate
            is missing required args or when either nested hint is incompatible.

        Raises:
            UnsupportedTypeHint: If a nested key or value hint check is
                unsupported by the registry/fallback checker.
        """
        if len(self.hint.args) == 0:
            # Unparameterized mappings accept any key/value hints.
            return True
        if len(value_hint.args) == 0:
            # A parameterized mapping does not match an unparameterized candidate.
            return False

        # Missing value hint defaults to Any.
        key_hint = self.hint.args[0]
        value_item_hint = self.hint.args[1] if len(self.hint.args) >= 2 else Any
        value_key_hint = value_hint.args[0]
        value_value_hint = value_hint.args[1] if len(value_hint.args) >= 2 else Any
        return (
                type_check_type(value_key_hint, key_hint)
                and type_check_type(value_value_hint, value_item_hint)
        )

    def _check_hint_callable(self, value_hint: TypeInfo) -> bool:
        """
        Compare callable parameter and return hints.

        Args:
            value_hint: Cached information for the candidate callable hint.

        Returns:
            ``True`` when return hints match and parameter lists are compatible.
            Returns ``False`` when args are missing, return hints differ,
            ellipsis usage differs, or fixed parameter hints differ.

        Raises:
            UnsupportedTypeHint: If a nested parameter or return hint cannot be
                checked.
        """
        if len(self.hint.args) == 0:
            # Unparameterized Callable accepts any callable hint.
            return True
        if len(value_hint.args) == 0:
            # Parameterized Callable does not match unparameterized candidate.
            return False

        # Callable args are stored as (params, return).
        params = self.hint.args[0]
        value_params = value_hint.args[0]
        expected_return = self.hint.args[1] if len(self.hint.args) > 1 else Any
        value_return = value_hint.args[1] if len(value_hint.args) > 1 else Any

        if not type_check_type(value_return, expected_return):
            return False
        if params is Ellipsis or value_params is Ellipsis:
            # Callable[..., R] only matches another ellipsis parameter list.
            return params is value_params
        return (
                len(value_params) == len(params)
                and self._match_args(value_params, params, False, True, True)
        )

    def _check_map(self, value):
        """
        Validate a runtime mapping's observed keys and values.

        Args:
            value: Runtime mapping object to inspect.

        Returns:
            ``True`` when every observed key and value satisfies the active
            mapping hints. Returns ``False`` when no key hint exists or any
            observed item is incompatible.

        Raises:
            UnsupportedTypeHint: If a mapping key hint uses an unsupported
                ``Unpack`` form or a nested key/value hint is unsupported.
        """
        key_hint = None
        value_hint = None
        arg_count = len(self.hint.args)
        if arg_count >= 1:
            # First mapping arg is the key hint.
            key_hint = self.hint.args[0]
        if arg_count >= 2:
            # Second mapping arg is the value hint.
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
                # Keys are always checked; values are only checked when a value hint exists.
                type_check(item_key, key_hint) and (type_check(item_value, value_hint) if value_hint is not None else True)
                for item_key, item_value in value.items()
            )

        # No key hint means this checker has no mapping contract to apply.
        return False

    def _check_callable(self, value):
        """
        Validate a runtime callable with whatever signature data is available.

        Args:
            value: Runtime callable object.

        Returns:
            ``True`` when the callable can accept the expected parameter shape
            and has a compatible return annotation. Missing signatures or
            annotations are treated as unknown and accepted. Returns ``False``
            when visible signature information is incompatible.

        Raises:
            UnsupportedTypeHint: If callable parameter hints, return hints, or
                TypedDict-unpacked keyword hints cannot be checked.
        """
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
            # Ellipsis means arbitrary parameters; non-list params are already broad.
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
                # Expected callable can accept an arbitrary number of this arg.
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
            # **kwargs annotation applies to all TypedDict key value hints.
            return all(
                type_check_type(_unwrap_required(annotations[key]), var_keyword.annotation)
                for key in required_keys | optional_keys
            )

        if expected_kwargs is not None:
            # Without **kwargs, named parameters must cover all required keys.
            return required_keys.issubset(accepted_keys)
        return True

    def check_value(self, value: Any) -> bool:
        """
        Return whether runtime ``value`` satisfies this checker's active hint.

        Args:
            value: Runtime object to check.

        Returns:
            ``True`` when ``value`` satisfies ``self.hint``. Returns ``False``
            when the value is supported but incompatible.

        Raises:
            UnsupportedTypeHint: If the active hint or one of its nested hints
                cannot be checked at runtime.
            UnsupportedTypeHintGroup: If multiple alternatives are unsupported.
            TypeError: If an internal iterable-arg check receives a non-iterable
                value where an iterable shape is required.
        """
        if self._origin_only and not self._ignore_origin:
            # This exists because many type checks should be
            # carried out in a similar fashion to using `isinstance`.
            return self._check_origin(TypeInfo.build(type(value)))

        # Sentinel hints need explicit runtime behavior.
        if self.hint.hint is Any:
            # Any accepts every runtime value.
            return True
        if self.hint.hint in (object, type):
            # object and type use normal isinstance semantics.
            return isinstance(value, self.hint.hint)
        if self.hint.hint in (None, NoneType):
            # None and NoneType only accept the None singleton.
            return value is None
        if self.hint.hint in (NoReturn, Never):
            # Impossible hints accept no runtime values.
            return False
        if self.hint.hint is LiteralString:
            # LiteralString has no runtime distinction from str.
            return isinstance(value, str)
        if isinstance(self.hint.hint, str) or isinstance(self.hint.hint, ForwardRef):
            # There is not enough local context here to resolve names safely.
            raise UnsupportedTypeHint(f"Forward references are not supported at runtime: {self.hint.hint!r}")

        # These forms masquerade as callables/classes in different Python
        # versions, so handle them before generic origin-based dispatch.
        if self.hint.is_typevar:
            # Constrained TypeVars are unions of their constraints.
            constraints = getattr(self.hint.hint, "__constraints__", ())
            if constraints:
                return self._match_args(value, constraints, True, False, False, True)
            bound = getattr(self.hint.hint, "__bound__", None)
            if bound is not None:
                # Bounded TypeVars defer to the bound hint.
                return type_check(value, bound)
            return True
        if self.hint.is_new_type:
            # NewType is runtime-compatible with its supertype.
            old_hint = self.hint
            self.hint = self.hint.hint.__supertype__
            is_type = self.check_value(value)
            self.hint = old_hint
            return is_type
        if self.hint.is_typed_dict:
            # TypedDict values are regular mappings at runtime.
            required_keys = set(getattr(self.hint.hint, "__required_keys__", set()))
            optional_keys = set(getattr(self.hint.hint, "__optional_keys__", set()))
            annotations = getattr(self.hint.hint, "__annotations__", {})
            allowed_keys = required_keys | optional_keys

            # Missing required keys fail before value types are inspected.
            if not required_keys.issubset(value.keys()):
                return False
            # Unknown keys fail because this checker models a closed shape.
            if any(key not in allowed_keys for key in value.keys()):
                return False

            for key, key_hint in annotations.items():
                # Optional keys are only checked when present.
                if key in value and not type_check(value[key], _unwrap_required(key_hint)):
                    return False
            return True

        if self.hint.is_metadata_wrapper:
            # Metadata wrappers do not change runtime shape.
            old_hint = self.hint
            self.hint = self.hint.first_arg
            is_type = self.check_value(value)
            self.hint = old_hint
            return is_type

        # Normal runtime checks must pass origin before args are considered.
        if not self._ignore_origin:
            if not self._check_origin(TypeInfo.build(type(value))):
                return False
            if self._origin_only:
                return True

        if not self._has_flags:
            # Runtime instances do not retain args for unsupported generic classes.
            if self._ignore_origin:
                raise UnsupportedTypeHint("Cannot have a TypeChecker that ignores origin when it has no flags")
            return True

        if self._map_like:
            # Mapping checks can succeed before iterable checks inspect keys.
            if self._check_map(value):
                return True

        if self._callable_like:
            # Callable-like hints require callable runtime values.
            if not callable(value):
                return False

        if self._iterable_like or self._callable_like:
            # No args means origin/callability was enough.
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
                # Homogeneous iterable and tuple[T, ...] checks.
                if self._match_args(value, [expanded[0]], True, True, False):
                    return True
                if self._tuple_like:
                    return False

        if self._tuple_like:
            # Fixed-length tuple hints are positional.
            if len(value) == len(expanded):
                if self._match_args(value, expanded, True, True, True):
                    return True

        if self._literal_like:
            # Literal checks compare the runtime value directly to payloads.
            if value in expanded:
                return True

        if self._union_like:
            # Union checks the runtime value against every alternative.
            if self._match_args(value, expanded, True, False, False):
                return True

        # Args existed but no structural branch could prove compatibility.
        return len(expanded) == 0

    def check_hint(self, value_hint: TypeHint | TypeInfo):
        """
        Return whether ``value_hint`` is compatible with this checker's hint.

        Args:
            value_hint: Candidate type hint or prebuilt ``TypeInfo``.

        Returns:
            ``True`` when ``value_hint`` is compatible with ``self.hint``.
            Returns ``False`` when both hints are supported but incompatible.

        Raises:
            UnsupportedTypeHint: If either hint contains unsupported forward
                references, unsupported ``Unpack`` forms, or unsupported nested
                hints.
            UnsupportedTypeHintGroup: If multiple union alternatives are
                unsupported.
            TypeError: If an internal iterable-arg check receives a non-iterable
                value where an iterable shape is required.
        """
        if not isinstance(value_hint, TypeInfo):
            value_hint = TypeInfo.build(value_hint)

        # inspect.Signature.empty is used for missing callable annotations.
        # Missing annotations are unknown, not incompatible.
        if value_hint.hint is inspect.Signature.empty or self.hint.hint is inspect.Signature.empty:
            return True
        if value_hint.hint is Any or self.hint.hint is Any:
            # Any on either side means the hint relationship is unconstrained.
            return True
        if value_hint.hint == self.hint.hint:
            # Exact hint equality is always compatible.
            return True
        if isinstance(value_hint.hint, str) or isinstance(value_hint.hint, ForwardRef):
            raise UnsupportedTypeHint(f"Forward references are not supported at runtime: {value_hint.hint!r}")
        if isinstance(self.hint.hint, str) or isinstance(self.hint.hint, ForwardRef):
            raise UnsupportedTypeHint(f"Forward references are not supported at runtime: {self.hint.hint!r}")

        # NoReturn/Never describe an impossible value set. An impossible value
        # set is a subtype of everything.
        if self.hint.hint in (NoReturn, Never):
            # The expected impossible set is compatible with all candidates here.
            return True
        if value_hint.hint in (NoReturn, Never):
            # The candidate impossible set only equals another impossible set.
            return self.hint.hint in (NoReturn, Never)
        if value_hint.hint is object:
            # object as candidate is broader than every concrete expected hint.
            return True
        if self.hint.hint is object:
            # object as expected only exactly matches object in this direction.
            return value_hint.hint is object
        if value_hint.hint is LiteralString:
            # LiteralString candidate can be treated like str unless expected is stricter.
            return self.hint.hint is LiteralString or self.check_hint(str)
        if self.hint.hint is LiteralString:
            # Expected LiteralString accepts hints compatible with str.
            return type_check_type(str, value_hint.hint)
        if value_hint.hint in (None, NoneType):
            # None-compatible candidate only matches None-compatible expected hint.
            return self.hint.hint in (None, NoneType)

        if self.hint.is_typevar:
            # Constrained TypeVars behave like a union of their constraints.
            constraints = getattr(self.hint.hint, "__constraints__", ())
            if constraints:
                return any(type_check_type(value_hint, constraint) for constraint in constraints)
            bound = getattr(self.hint.hint, "__bound__", None)
            if bound is not None:
                # Bounded TypeVars defer to hint compatibility with the bound.
                return type_check_type(value_hint, bound)
            return True
        if self.hint.is_new_type:
            # NewType compatibility is inherited from its supertype.
            old_hint = self.hint
            self.hint = self.hint.hint.__supertype__
            is_type = self.check_hint(value_hint)
            self.hint = old_hint
            return is_type
        if value_hint.is_new_type:
            # Compare the candidate NewType by its supertype.
            value_hint = value_hint.replace(value_hint.hint.__supertype__)
        if self.hint.is_metadata_wrapper:
            # Metadata wrappers do not change compatibility.
            old_hint = self.hint
            self.hint = self.hint.first_arg
            is_type = self.check_hint(value_hint)
            self.hint = old_hint
            return is_type
        if value_hint.is_metadata_wrapper:
            value_hint = value_hint.unwrap_metadata()
        if self.hint.is_typed_dict:
            # TypedDict hint compatibility is key-shape compatibility.
            if not value_hint.is_typed_dict:
                return False

            required_keys = set(getattr(self.hint.hint, "__required_keys__", set()))
            optional_keys = set(getattr(self.hint.hint, "__optional_keys__", set()))
            value_required_keys = set(getattr(value_hint.hint, "__required_keys__", set()))
            value_optional_keys = set(getattr(value_hint.hint, "__optional_keys__", set()))
            # Required and optional key sets must match exactly.
            if required_keys != value_required_keys or optional_keys != value_optional_keys:
                return False

            annotations = getattr(self.hint.hint, "__annotations__", {})
            value_annotations = getattr(value_hint.hint, "__annotations__", {})
            # Annotation keys must match even before comparing value hints.
            if annotations.keys() != value_annotations.keys():
                return False
            return all(
                type_check_type(
                    _unwrap_required(value_annotations[key]),
                    _unwrap_required(key_hint),
                )
                for key, key_hint in annotations.items()
            )

        # Hint args are compared before origin is used as a final fallback.
        origin_matches = self._check_origin(value_hint)
        if self._origin_only:
            # Origin-only hint checks still need origin compatibility.
            return origin_matches

        if self._map_like:
            # Mapping args can match across aliases when origin is ignored.
            if self._check_hint_map(value_hint) and (self._ignore_origin or origin_matches):
                return True

        if self._iterable_like or self._callable_like:
            if len(self.hint.args) == 0:
                # No args means there is no structural detail to compare.
                return origin_matches

        if self._callable_like:
            # Callable compatibility is params plus return hint.
            if self._check_hint_callable(value_hint) and (self._ignore_origin or origin_matches):
                return True

        if self._tuple_like:
            if self.hint.args == ((),):
                # tuple[()] is the empty tuple hint.
                return value_hint.args == ((),) and (self._ignore_origin or origin_matches)

        expanded = self._expand_args()
        value_expanded = self._expand_args(value_hint.args)

        if self._iterable_like:
            if len(expanded) == 0:
                return True
            if len(value_expanded) == 0:
                return False
            if (self._tuple_like and len(expanded) == 2 and expanded[1] is Ellipsis) or not self._tuple_like:
                if self._tuple_like:
                    # Variadic tuple hints only match variadic tuple candidates.
                    return (
                            len(value_expanded) == 2
                            and value_expanded[1] is Ellipsis
                            and type_check_type(value_expanded[0], expanded[0])
                            and (self._ignore_origin or origin_matches)
                    )
                return (
                        # Homogeneous iterable hints have exactly one item arg.
                        len(value_expanded) == 1
                        and type_check_type(value_expanded[0], expanded[0])
                        and (self._ignore_origin or origin_matches)
                )

        if self._tuple_like:
            if len(value_expanded) == len(expanded):
                # Fixed tuple candidates compare position by position.
                if (
                        self._match_args(value_expanded, expanded, False, True, True)
                        and (self._ignore_origin or origin_matches)
                ):
                    return True

        if self._literal_like:
            # Literal order does not matter, but multiplicity is preserved by length.
            return len(value_expanded) == len(expanded) and all(
                value_item in expanded
                for value_item in value_expanded
            )

        if self._union_like:
            # Union alternatives are compared as an unordered set.
            return len(value_expanded) == len(expanded) and all(
                any(type_check_type(value_item, hint_item) for hint_item in expanded)
                for value_item in value_expanded
            )

        # Fallback keeps unsupported generic aliases distinct by args.
        if len(value_expanded) != len(expanded):
            return False
        if len(expanded) != 0 and not self._match_args(value_expanded, expanded, False, True, True):
            return False
        return origin_matches


def _valid_iter(origin: Any) -> bool:
    """
    Return whether an origin is valid for sequence or iterable type checking.

    Args:
        origin: Runtime origin object to inspect.

    Returns:
        ``True`` when ``origin`` can be treated as an iterable container by this
        checker. Returns ``False`` for string-like origins, because those are
        treated as scalar values here even though they are iterable in Python.
    """
    return not _is_subclass(origin, (str, bytes, bytearray))


def _is_subclass(origin: Any, parent: Any) -> bool:
    """
    Safely test whether ``origin`` is a subclass of ``parent``.

    Args:
        origin: Candidate origin object.
        parent: Expected parent class or tuple of parent classes.

    Returns:
        ``True`` when ``origin`` is a class and is a subclass of ``parent``.
        Returns ``False`` when ``origin`` is not a class or ``issubclass`` would
        raise ``TypeError``.
    """
    try:
        return isinstance(origin, type) and issubclass(origin, parent)
    except TypeError:
        return False

def _is_class(origin: Any, parent: Any) -> bool:
    """
    Safely test whether ``origin`` is exactly ``parent``.

    Args:
        origin: Candidate origin object.
        parent: Expected object or tuple of expected objects.

    Returns:
        ``True`` when ``origin`` is identical to ``parent`` or to one item in
        ``parent``. Returns ``False`` for non-matching or invalid comparisons.
    """
    if isinstance(parent, tuple):
        for item in parent:
            if _is_class(origin, item):
                return True
        return False
    try:
        return origin is parent
    except TypeError:
        return False


# Broad catch-all hints are resolved before registry scanning.
AnyType = TypeChecker(Any, origin_only=True)
ObjectType = TypeChecker(object, origin_only=True)
TYPES: list[TypeChecker] = [
    # Basic numeric scalar checkers.
    TypeChecker(int, origin_only=True),
    TypeChecker(bool, origin_only=True),
    TypeChecker(float, origin_only=True),
    TypeChecker(complex, origin_only=True),
    # String/byte-like values are scalar for this checker, not iterable shapes.
    TypeChecker(str, origin_only=True),
    TypeChecker(bytes, origin_only=True),
    TypeChecker(bytearray, origin_only=True),
    # Tuple has fixed-length and variadic forms, unlike generic Sequence.
    TypeChecker(tuple, tuple_like=True),
    TypeChecker(slice, origin_only=True),
    TypeChecker(NoneType),
    # Abstract containers cover their builtin subclasses when possible.
    TypeChecker(Mapping, map_like=True),
    TypeChecker(Sequence, sequence_like=True),
    TypeChecker(Iterable, iterable_like=True),
    # Typing forms below are mostly argument-driven.
    TypeChecker(UnionType | Union, union_like=True, ignore_origin=True),
    TypeChecker(Literal, literal_like=True, allow_non_type_args=True),
    TypeChecker(Callable, callable_like=True, allow_non_type_args=True),
    TypeChecker(type, origin_only=True),
]

# Add builtin classes not already covered by explicit or abstract checkers.
for builtin_type in dict.fromkeys(
    type_obj
    for name, type_obj in vars(builtins).items()
    if isinstance(type_obj, type) and name != "__loader__"
):
    if builtin_type not in {
        object,
        Any,
        type,
    }:
        can_build = True
        for type_checker in TYPES:
            # Skip builtin classes already covered by a broader registered checker.
            if _is_subclass(builtin_type, type_checker.info.hint) or _is_class(builtin_type, type_checker.info.hint):
                can_build = False
                break
        if can_build:
            # Remaining builtin classes get simple origin-only behavior.
            TYPES.append(TypeChecker(builtin_type, origin_only=True))

Hint: TypeAlias = TypeHint | TypeInfo | TypeChecker
Hint = Hint | tuple[Hint, ...]

def get_type_checker(hint: TypeHint | TypeInfo | TypeChecker, default:TypeChecker | None=AnyType) -> TypeChecker:
    """
    Return the registered checker for ``hint``.

    Args:
        hint: Raw type hint, ``TypeInfo``, or ``TypeChecker`` to resolve.
        default: Checker to return when no registered checker supports
            ``hint``. Pass ``None`` to raise instead.

    Returns:
        A checker from ``TYPES``, one of the special catch-all checkers, the
        checker passed in through ``hint``, or ``default``.

    Raises:
        UnsupportedTypeHint: If no checker supports ``hint`` and ``default`` is
            ``None``.
    """
    if isinstance(hint, TypeChecker):
        return hint
    if not isinstance(hint, TypeInfo):
        # Normalize once before scanning the registry.
        hint = TypeInfo.build(hint)
    if hint.hint is Any:
        return AnyType
    if hint.hint is object:
        return ObjectType
    for tc in TYPES:
        # A checker decides whether it owns a hint through check_hint.
        if tc.check_hint(hint):
            return tc
    if default is None:
        raise UnsupportedTypeHint(f"Unsupported TypeHint: {hint.hint!r}")
    # Callers may request permissive fallback behavior through default.
    return default

def type_check(value, hint: Hint) -> bool:
    """
    Return whether runtime ``value`` satisfies ``hint``.

    Args:
        value: Runtime object to check.
        hint: Type hint, ``TypeInfo``, ``TypeChecker``, or tuple of hints.

    Returns:
        ``True`` when ``value`` satisfies at least one supplied hint. Returns
        ``False`` when all supplied hints are supported but incompatible.

    Raises:
        UnsupportedTypeHint: If checking requires an unsupported hint form.
        UnsupportedTypeHintGroup: If multiple alternatives are unsupported.
        TypeError: If a structural check receives a runtime shape it cannot
            iterate or inspect as required.
    """
    if isinstance(hint, tuple):
        # Tuple input is treated as a union of possible hints.
        for h in hint:
            if type_check(value, h):
                return True
        return False
    try:
        this_hint = get_type_checker(hint, None)
    except UnsupportedTypeHint:
        # Fallback checkers are temporary and inferred from the hint itself.
        this_hint = TypeChecker(hint, True)
    this_hint.hint = hint
    is_type = this_hint.check_value(value)
    # Reset reusable registry checkers to their template hint.
    this_hint.hint = None
    return is_type

def type_check_type(value, hint: Hint) -> bool:
    """
    Return whether type hint ``value`` is compatible with ``hint``.

    Args:
        value: Candidate type hint.
        hint: Expected type hint, ``TypeInfo``, ``TypeChecker``, or tuple of
            hints.

    Returns:
        ``True`` when ``value`` is compatible with at least one supplied hint.
        Returns ``False`` when all supplied hints are supported but
        incompatible.

    Raises:
        UnsupportedTypeHint: If either side contains an unsupported hint form.
        UnsupportedTypeHintGroup: If multiple alternatives are unsupported.
        TypeError: If a structural hint-arg check receives a non-iterable shape.
    """
    if isinstance(hint, tuple):
        # Tuple input is treated as a union of possible hint expectations.
        for h in hint:
            if type_check_type(value, h):
                return True
        return False
    try:
        this_hint = get_type_checker(hint, None)
    except UnsupportedTypeHint:
        # Fallback checkers are temporary and inferred from the expected hint.
        this_hint = TypeChecker(hint, True)
    this_hint.hint = hint
    is_type = this_hint.check_hint(value)
    # Reset reusable registry checkers to their template hint.
    this_hint.hint = None
    return is_type
