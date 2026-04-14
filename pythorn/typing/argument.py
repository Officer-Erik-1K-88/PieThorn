import inspect
from enum import Enum
from types import UnionType
from typing import Any, MutableMapping, Collection, TypeAlias

_TypeInfo: TypeAlias = type | UnionType
_ClassInfo: TypeAlias = _TypeInfo | tuple[_TypeInfo, ...]

class ArgumentKind(Enum):
    """
    Defines the kind of the argument
    """
    POSITIONAL_OR_KEYWORD = (True, True, False, inspect.Parameter.POSITIONAL_OR_KEYWORD, "positional or keyword")
    POSITIONAL_ONLY = (True, False, False, inspect.Parameter.POSITIONAL_ONLY, "positional-only")
    KEYWORD_ONLY = (False, True, False, inspect.Parameter.KEYWORD_ONLY, "keyword-only")
    VAR_POSITIONAL = (True, False, True, inspect.Parameter.VAR_POSITIONAL, "variadic positional")
    VAR_KEYWORD = (False, True, True, inspect.Parameter.VAR_KEYWORD, "variadic keyword")

    @staticmethod
    def from_param_kind(param_kind):
        if param_kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            return ArgumentKind.POSITIONAL_OR_KEYWORD
        elif param_kind is inspect.Parameter.POSITIONAL_ONLY:
            return ArgumentKind.POSITIONAL_ONLY
        elif param_kind is inspect.Parameter.KEYWORD_ONLY:
            return ArgumentKind.KEYWORD_ONLY
        elif param_kind is inspect.Parameter.VAR_POSITIONAL:
            return ArgumentKind.VAR_POSITIONAL
        elif param_kind is inspect.Parameter.VAR_KEYWORD:
            return ArgumentKind.VAR_KEYWORD
        raise RuntimeError("Cannot determine the kind of the parameter")

    def __init__(
            self,
            positional: bool,
            keyword: bool,
            variadic: bool,
            param_kind: inspect._ParameterKind,
            description: str,
    ) -> None:
        """

        :param positional: Whether the argument is positional
        :param keyword: Whether the argument is keyword
        :param variadic: Whether the argument is variadic, i.e., ``*args`` or ``**kwargs``.
        """
        self._positional = positional
        self._keyword = keyword
        self._variadic = variadic
        self._kind = param_kind
        self._description = description

    @property
    def positional(self) -> bool:
        return self._positional

    @property
    def keyword(self) -> bool:
        return self._keyword

    @property
    def variadic(self) -> bool:
        return self._variadic

    @property
    def kind(self):
        return self._kind

    @property
    def description(self):
        return self._description

    def __str__(self) -> str:
        return self.name

_empty = inspect.Parameter.empty

class Argument:
    """
    Used to define information on an argument to a
    class, method, or function.

    The Argument class is used for typing that
    python's built in type check system doesn't allow for.
    """
    empty = _empty
    @staticmethod
    def from_param(param: inspect.Parameter) -> Argument:
        kwargs = {
            "key": param.name,
            "type_var": param.annotation if param.annotation is not _empty else Any,
            "kind": ArgumentKind.from_param_kind(param.kind),
            "default": param.default,
        }
        return Argument(**kwargs)

    def __init__(
            self,
            key: str,
            type_var: _ClassInfo,
            *,
            allowed_values: Collection[Any] | type[_empty] = _empty,
            kind=ArgumentKind.POSITIONAL_OR_KEYWORD,
            default=_empty,
            value=_empty,
    ) -> None:
        """
        Creates an argument for the given key.

        :param key: The name of the argument
        :param type_var: The valid type that this argument is allowed to store.
        :param allowed_values: A collection of allowed values for this argument.
        :param kind: The kind of the argument. Refer to ``ArgumentKind`` class for details.
        :param default: The default value of the argument.
        :param value: The value of the argument.
        """
        self._key = key
        self._type_var = type_var
        self._allowed_values = allowed_values
        self._kind = kind
        self._default = _empty
        self._value = Arguments(parent=self,strict_keys=False) if kind.variadic else _empty
        if default is not _empty:
            self.set_default(default)
        if value is not _empty:
            self.set(value)

    @property
    def key(self) -> str:
        """
        The name of the argument.
        :return:
        """
        return self._key

    @property
    def type_var(self) -> _ClassInfo:
        """
        The type of the argument.
        :return:
        """
        return self._type_var

    @property
    def kind(self) -> ArgumentKind:
        return self._kind

    @property
    def has_default(self) -> bool:
        """
        Whether the argument has a default value.
        :return:
        """
        return self._default is not _empty

    @property
    def default(self):
        """
        The default value of the argument.
        :return:
        """
        return self._default

    def set_default(self, default: Any):
        """
        Sets the default value of the argument.
        :param default: The default value of the argument
        :return:
        """
        if self.kind.variadic:
            raise ValueError(f"{self.kind.description} parameters cannot have default values")
        valid = self.validate(default, False)
        if not valid:
            raise TypeError(f"Default value '{default}' is invalid for argument '{self._key}'")
        self._default = default

    @property
    def allowed_values(self) -> Collection[Any] | type[_empty]:
        """
        The allowed values of the argument.
        :return:
        """
        return self._allowed_values

    @property
    def has_value(self) -> bool:
        """
        Whether the argument has a value.
        :return:
        """
        return self._value is not _empty

    @property
    def value(self):
        """
        The value of the argument.

        If ``has_value`` is ``False``, then ``default`` is returned.
        :return: The value of the argument. If the argument is variadic, then an `Arguments` class is returned.
        """
        if self.has_value:
            return self._value
        return self.default

    def set(self, value: Any, *, key: str | None = None):
        """
        Sets the value of the argument.

        ``validate`` is called on the value.

        :param value: The value to set.
        :param key: The key of the value (For when this argument is variadic keyword)
        :return: The old value or ``Arguement.empty``
        """
        if self.kind.variadic:
            if self.kind.positional:
                raise ValueError(f"Cannot set the value when argument is {self.kind.description} parameter")
            elif self.kind.keyword:
                if key is None:
                    raise ValueError(f"Cannot set the value when argument is {self.kind.description} parameter, missing key")
                assert isinstance(self._value, Arguments)
                return self._value.set(key, value)
        self.validate(value)
        old = self.value
        self._value = value
        return old

    def add(self, value: Any):
        """
        Adds the value to the argument.

        This method can only be used when the argument is variadic.
        The key that is set to the value is ``{key}-{len(value)}``.

        :param value: The value to add.
        :return:
        """
        if not self.kind.variadic:
            raise ValueError(f"Cannot add value when argument is {self.kind.description} parameter, use `set` instead")
        assert isinstance(self._value, Arguments)
        self._value.set(f"{self.key}-{len(self._value)}", value)

    def remove(self, key: str | int | None = None):
        """
        Removes the value from the argument.
        :param key: The key (keyword) or index (positional) of the value (For when this argument is variadic).
        :return: The removed value
        """
        if self.kind.variadic:
            if key is None:
                raise ValueError(f"Cannot remove value when argument is {self.kind.description} parameter")
            assert isinstance(self._value, Arguments)
            if isinstance(key, int):
                key = f"{self.key}-{key}"
            assert isinstance(key, str)
            return self._value.pop(key)
        value = self.value
        self._value = _empty
        return value

    def validate(self, value: Any, throw: bool=True) -> bool:
        """
        Checks whether the provided value is valid.

        :param value: The value to be checked
        :param throw: Whether to throw a ``TypeError`` instead of returning ``False`` when value is invalid
        :return: Whether the value is valid
        """
        if not isinstance(value, self.type_var):
            if throw:
                raise TypeError(f"Type mismatch for {self.key}: expected {self.type_var}, got {type(value)}")
            return False
        elif self.allowed_values is not _empty:
            if value not in self.allowed_values:
                if throw:
                    raise TypeError(f"Value of '{value}' is invalid for {self.key}")
                return False
        return True

    def copy(self, **kwargs):
        """
        Makes a copy of the argument.

        ``value`` is the only property not given to the new Argument.

        :param kwargs: The properties to override.
        :return: A new Argument with the same properties
        """
        kwargs.setdefault("key", self.key)
        kwargs.setdefault("type_var", self.type_var)
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("allowed_values", self.allowed_values)
        kwargs.setdefault("kind", self.kind)
        return type(self)(**kwargs)


class Arguments(MutableMapping[str, Any]):
    """
    Used to store all the arguments of a class, method, or function.
    """

    def __init__(self, *args: Argument, parent:Argument|None=None, strict_keys: bool=True, silent_strict: bool=False, typing_with_value: bool=False) -> None:
        """
        Creates a new Arguments object.

        :param args: The arguments
        :param parent: The parent argument, this should only ever be set for an ``Argument`` that is variadic.
        :param strict_keys: Whether a key must exist for calls to it.
        :param silent_strict: Whether to silence errors from strict keys.
        :param typing_with_value: Whether to type created arguments with the type that it's value has.
        """
        self._positionals: list[str] = []
        self._keywords: list[str] = []
        self._args: dict[str, Argument] = {}
        self._parent = parent
        self._strict_keys = strict_keys
        self._silent_strict = silent_strict
        self._typing_with_value = typing_with_value
        for arg in args:
            self.set_arg(arg)

    @property
    def parent(self):
        return self._parent

    @property
    def strict_keys(self):
        """
        Whether the key to an argument must exist when
        validating, setting, or removing.
        :return:
        """
        return self._strict_keys

    @property
    def silent_strict(self):
        """
        Whether to silence errors from strict keys.
        :return:
        """
        return self._silent_strict

    @property
    def typing_with_value(self):
        """
        Whether to type internally created arguments with the
        type that it's value has.

        If ``False``, then will type new arguments with ``Any``.
        Otherwise, will type new arguments with ``type(value)``.
        :return:
        """
        return self._typing_with_value

    def _get_type(self, value) -> _ClassInfo:
        if self._parent is not None:
            return self._parent.type_var
        return Any if self._typing_with_value or value is None else type(value)

    def _get_kind(self):
        if self._parent is not None:
            if self._parent.kind.variadic:
                if self._parent.kind.positional:
                    return ArgumentKind.POSITIONAL_ONLY
                elif self._parent.kind.keyword:
                    return ArgumentKind.KEYWORD_ONLY
            else:
                return self._parent.kind
        return ArgumentKind.POSITIONAL_OR_KEYWORD

    def validate(self, key: str, value: Any, throw: bool=True) -> bool:
        """
        Checks to see if there is an argument for ``key``.
        If one exists, then ``value`` will be type checked.

        If ``throw`` is ``True``, then will raise a ``TypeError`` when value is invalid.

        If ``strict_keys`` is ``True``, then will return ``False`` when key is not in the map.
        However, will raise a ``KeyError`` when ``throw`` is ``True``, this error only occurs when
        ``silent_strict`` is ``False``.

        If ``strict_keys`` is ``False`` and key is not in the map, then ``True`` is returned.

        :param key: The name of the argument to get the typing set for
        :param value: The value to be checked
        :param throw: Whether to raise an error instead of returning ``False``
        :return: Whether the key-value pair is valid
        """
        if key not in self._args:
            if self._strict_keys:
                if throw and not self._silent_strict:
                    raise KeyError(f"Key '{key}' is invalid")
                return False
            return True
        return self._args[key].validate(value, throw)

    def at(self, index: int, in_keywords: bool=False):
        """
        Gets the Argument at ``index``.

        :param index: The index of the argument to get
        :param in_keywords: Whether to look into keyword arguments or positional arguments
        :return: The Argument at ``index``
        """
        key = self._keywords[index] if in_keywords else self._positionals[index]
        return self._args[key]

    def get_arg(self, key: str):
        """
        Gets the Argument for ``key``.

        If ``strict_keys`` is ``True``, then will raise ``KeyError`` if ``key`` is not in the map,
        otherwise ``None`` is returned.

        :param key: The name of the argument to get
        :return: The Argument for ``key``
        """
        if key not in self._args:
            if self._strict_keys and not self._silent_strict:
                raise KeyError(f"Key '{key}' is invalid")
            return None
        return self._args[key]

    def set_arg(self, arg: Argument) -> bool:
        """
        Adds ``arg`` to the map.

        If the key defined by ``arg`` is already present in the map,
        then, given ``strict_keys`` is ``True``, then will raise a ``KeyError``.
        This error only occurs when ``strict_keys`` is ``False``,
        otherwise ``False`` is returned.

        While if ``strict_keys`` is ``False``, then the key is overridden.

        :param arg: The argument to add
        :return: Whether the ``arg`` has been added to the map
        """
        if self._strict_keys:
            if arg.key in self._args:
                if self._silent_strict:
                    return False
                raise KeyError(f"Key '{arg.key}' is already present in the kwargs")
        if arg.kind.positional:
            self._positionals.append(arg.key)
        if arg.kind.keyword:
            self._keywords.append(arg.key)
        self._args[arg.key] = arg
        return True

    def set(self, key: str, value: Any):
        """
        Sets ``key`` to ``value``.

        :param key: The name of the argument to set
        :param value: The value to be set
        :return: The old value of the argument
        """
        if key not in self._args:
            if self._strict_keys:
                raise KeyError(f"Key '{key}' is not present in the kwargs")

            self.set_arg(Argument(key, self._get_type(value), value=value, kind=self._get_kind()))
            return _empty
        else:
            return self._args[key].set(value)

    def ensure_defaults(self, **kwargs):
        """
        Ensures that all the provided keys has a default value.
        If the key doesn't have a default value, then the given value is set
        as the default value.
        :param kwargs: The key-value pairs
        :return:
        """
        for key, value in kwargs.items():
            if key not in self._args:
                if self._strict_keys:
                    if self._silent_strict:
                        continue
                    raise KeyError(f"Key '{key}' is invalid")
                self.set_arg(Argument(key, self._get_type(value), default=value, kind=self._get_kind()))
            else:
                if not self._args[key].has_default:
                    self._args[key].set_default(value)

    def remove(self, key: str):
        """
        Removes ``key`` from the map.

        If key is not present in the map, then ``None`` is returned.
        However, a ``KeyError`` is raised when ``strict_keys`` is ``True``,
        error is only raised when ``silent_strict`` is ``False``.

        :param key: The argument to remove from the map
        :return: The removed argument
        """
        if key not in self._args:
            if self._strict_keys:
                if self._silent_strict:
                    return None
                raise KeyError(f"Key '{key}' is not present in the kwargs")
            return None
        return self._args.pop(key, None)

    def __len__(self) -> int:
        return len(self._args)

    def __contains__(self, key: str) -> bool:
        return key in self._args

    def __iter__(self):
        return iter(self._args)

    def iter_keywords(self):
        """
        Returns an iterator over the keyword arguments
        :return:
        """
        return iter(self._keywords)

    def iter_positionals(self):
        """
        Returns an iterator over the positional arguments
        :return:
        """
        return iter(self._positionals)

    def __setitem__(self, key, value, /):
        self.set(key, value)

    def __getitem__(self, key, /):
        if key not in self._args:
            raise KeyError(f"Key '{key}' is not present in the kwargs")
        return self._args[key].value

    def __delitem__(self, key, /):
        if key not in self._args:
            raise KeyError(f"Key '{key}' is not present in the kwargs")
        self._args[key].remove()
