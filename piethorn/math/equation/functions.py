from __future__ import annotations

from decimal import Decimal
from typing import Callable, Iterable, Iterator, MutableSequence, Sequence, TypeAlias

from .parameters import Parameters, _boolean_param, _decimal_param

_DecimalValid: TypeAlias = Decimal | int | float | str | tuple[int, Sequence[int], int]


class Function:
    """Represent a callable or constant value that can appear in equations."""

    def __init__(
            self,
            name: str,
            value: _DecimalValid | None = None,
            parameters: Parameters | None = None,
            action: Callable[[Parameters], _DecimalValid] | None = None,
    ):
        if action is None and value is None:
            raise TypeError("One of `action` or `value` must be specified")
        if action is not None:
            if parameters is None or len(parameters) == 0:
                raise TypeError("`parameters` must be specified when `action` is specified")
        self._name = name
        self._value: Decimal | None = None if value is None else Decimal(value)
        self._parameters = parameters
        self._action = action
        assert self._value is not None or self._action is not None

    @property
    def name(self):
        """Return the function name."""
        return self._name

    @property
    def parameters(self):
        """Return this function's declared parameters."""
        return self._parameters

    def is_value(self):
        """Return whether this function is a constant value."""
        return self._value is not None

    def __call__(self, parameters: Parameters) -> Decimal:
        if parameters is None:
            raise TypeError("`parameters` must be specified")
        # Merge the provided arguments into this function's declared signature.
        # noinspection PyUnresolvedReferences
        new_parameters = self._parameters.fill(parameters)
        if not new_parameters.required_filled():
            raise TypeError("all required `parameters` must be filled")
        return Decimal(self._action(new_parameters))

    def apply(self, param_handler: Callable[[Parameters], Parameters] | None = None) -> Decimal:
        """Evaluate the function using a parameter transformer or constant value."""
        if self._action is None:
            # noinspection PyTypeChecker
            return self._value

        if param_handler is None:
            raise TypeError("`param_handler` must be specified when `action` is specified")
        # noinspection PyTypeChecker
        return Decimal(self._action(param_handler(self._parameters)))


class Functions(MutableSequence[Function]):
    """Index equation functions by name while preserving declaration order."""

    def __init__(self, *functions):
        self._functions: list[Function] = []
        self._func_names: list[str] = []
        self.extend(functions)

    def insert(self, index: int, function: Function):
        if function.name in self._func_names:
            raise KeyError(f"Function `{function.name}` already exists")
        self._functions.insert(index, function)
        self._func_names.insert(index, function.name)

    def append(self, function: Function):
        if function.name in self._func_names:
            raise KeyError(f"Function `{function.name}` already exists")
        self._functions.append(function)
        self._func_names.append(function.name)

    def extend(self, functions: Iterable[Function]):
        for func in functions:
            if func.name in self._func_names:
                continue
            self._functions.append(func)
            self._func_names.append(func.name)

    def get(self, name: str) -> Function:
        """Get the function with the given name"""
        if name in self._func_names:
            return self._functions[self.name_index(name)]
        raise KeyError(f"Parameter `{name}` not found")

    def name_index(self, name: str, start: int=0, stop: int | None=None) -> int:
        """Get the index of the given name"""
        if stop is None:
            return self._func_names.index(name, start)
        return self._func_names.index(name, start, stop)

    def names(self):
        """Return the names of all registered functions."""
        return tuple(self._func_names)

    def __getitem__(self, item: int) -> Function:
        return self._functions[item]

    def __setitem__(self, index: int, function: Function):
        if function.name in self._func_names:
            raise KeyError(f"Function `{function.name}` already exists")
        self._functions[index] = function
        self._func_names[index] = function.name

    def __delitem__(self, index: int):
        del self._functions[index]
        del self._func_names[index]

    def __len__(self):
        return len(self._functions)

    def __iter__(self) -> Iterator[Function]:
        return iter(self._functions)

    def __contains__(self, item):
        return item in self._func_names


def _default_functions() -> tuple[Function, ...]:
    """Return the builtin equation constants and helper functions."""
    return (
        Function("pi", value=Decimal("3.1415926535897932384626433832795028841971")),
        Function("e", value=Decimal("2.7182818284590452353602874713526624977572")),
        Function(
            "abs",
            parameters=Parameters((_decimal_param("value", required=True),)),
            action=lambda params: abs(params[0].get()),
        ),
        Function(
            "min",
            parameters=Parameters((
                _decimal_param("left", required=True),
                _decimal_param("right", required=True),
            )),
            action=lambda params: min(params[0].get(), params[1].get()),
        ),
        Function(
            "max",
            parameters=Parameters((
                _decimal_param("left", required=True),
                _decimal_param("right", required=True),
            )),
            action=lambda params: max(params[0].get(), params[1].get()),
        ),
        Function(
            "clamp",
            parameters=Parameters((
                _decimal_param("value", required=True),
                _decimal_param("minimum", required=True),
                _decimal_param("maximum", required=True),
            )),
            action=lambda params: min(max(params[0].get(), params[1].get()), params[2].get()),
        ),
        Function(
            "if",
            parameters=Parameters((
                _boolean_param("condition", required=True),
                _decimal_param("when_true", required=True),
                _decimal_param("when_false", required=True),
            )),
            action=lambda params: params[1].get() if params[0].get() else params[2].get(),
        ),
    )


FUNCTIONS = Functions(*_default_functions())
