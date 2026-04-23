from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence


class Param(ABC):
    """Define the interface for named or positional equation parameters."""

    @property
    @abstractmethod
    def name(self):
        """The name of the parameter"""
        pass

    @property
    @abstractmethod
    def takes_boolean(self):
        """Whether the parameter accepts boolean expressions."""
        pass

    @property
    @abstractmethod
    def default(self):
        """The default value that is returned if there is no value"""
        pass

    @property
    @abstractmethod
    def value(self):
        """The value of the parameter"""
        pass

    @property
    @abstractmethod
    def required(self):
        """Whether the parameter is required"""
        pass

    @property
    def position_dependent(self):
        """Whether the parameter is position dependent, meaning it has no name"""
        return self.name == ""

    def get(self):
        """Get the value of the parameter"""
        if self.value is None:
            return self.default
        return self.value

    def is_empty(self):
        """Whether the parameter is empty"""
        return self.get() is None

    def new(self, value):
        """Create a new parameter with the given value"""
        return Parameter(
            self.name,
            self.takes_boolean,
            self.default,
            value,
            self.required,
        )


class Parameter(Param):
    """Store a concrete parameter definition and optional bound value."""

    def __init__(self, name: str, takes_boolean: bool = False, default=None, value=None, required=False):
        self._name = name
        self._takes_boolean = takes_boolean
        self._default = default
        self._value = value
        self._required = required

    @property
    def name(self):
        """The name of the parameter"""
        return self._name

    @property
    def takes_boolean(self):
        """Whether the parameter accepts boolean expressions."""
        return self._takes_boolean

    @property
    def default(self):
        """The default value that is returned if there is no value"""
        return self._default

    @property
    def value(self):
        """The value of the parameter"""
        return self._value

    @property
    def required(self):
        """Whether the parameter is required"""
        return self._required


class Parameters(Sequence[Param]):
    """Provide ordered parameter definitions with name-based lookup helpers."""

    def __init__(self, parameters: tuple[Param, ...] | None=None):
        self._parameters: tuple[Param,...] = tuple() if parameters is None else parameters
        self._param_names: dict[str, int] = {}
        # Precompute name-to-index lookup for non-positional parameters.
        i = 0
        for parameter in self._parameters:
            if not parameter.position_dependent:
                self._param_names[parameter.name] = i
            i += 1

    def check(self, parameters: Parameters):
        """
        Check if the given parameters has all required parameters filled.

        The given `Parameters` must have the same number of parameters as this `Parameters` instance.
        """
        if len(parameters) != len(self):
            return False
        i = 0
        for parameter in self._parameters:
            if parameter.position_dependent:
                if parameter.required:
                    if parameters[i].is_empty():
                        return False
            else:
                if parameter.required:
                    if parameters[i].is_empty():
                        return False
            i += 1
        return True

    def fill(self, parameters: Parameters):
        """
        Create a new `Parameters` with the same parameters as this
        instance and the given `Parameters` instance.

        Any parameters in the given `Parameters` instance that is
        not in this instance will not be added to the new `Parameters`.

        Only the values of the given `Parameters` instance will be
        filled in the new `Parameters`.
        """
        new_list = list(self._parameters)

        # Copy only supplied values into the declared parameter layout.
        i = 0
        for parameter in parameters:
            if parameter.position_dependent:
                if i < len(new_list):
                    new_list[i] = new_list[i].new(parameter.value)
            else:
                if parameter.name in self:
                    index = self._param_names[parameter.name]
                    new_list[index] = new_list[index].new(parameter.value)
            i += 1
        return Parameters(tuple(new_list))

    def required_filled(self):
        """
        Check if this `Parameters` instance has all required parameters
        filled.
        :return:
        """
        for parameter in self._parameters:
            if parameter.required:
                if parameter.is_empty():
                    return False
        return True

    def get_named_parameter(self, name: str) -> Param:
        """Get the parameter with the given name"""
        if name in self._param_names:
            return self._parameters[self._param_names[name]]
        raise KeyError(f"Parameter `{name}` not found")

    def __getitem__(self, item) -> Param:
        return self._parameters[item]

    def __len__(self):
        return len(self._parameters)

    def __iter__(self):
        for parameter in self._parameters:
            yield parameter

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self._param_names
        return item in self._parameters

    def __add__(self, other):
        if isinstance(other, Parameters):
            return Parameters(self._parameters + other._parameters)
        elif isinstance(other, tuple):
            return Parameters(self._parameters + other)
        elif isinstance(other, Iterable):
            return Parameters(self._parameters + tuple(other))
        return Parameters(self._parameters + (other,))

    def __radd__(self, other):
        if isinstance(other, Parameters):
            return Parameters(other._parameters + self._parameters)
        elif isinstance(other, tuple):
            return Parameters(other + self._parameters)
        elif isinstance(other, Iterable):
            return Parameters(tuple(other) + self._parameters)
        return Parameters((other,) + self._parameters)


def _decimal_param(name: str, *, default=None, required: bool = False) -> Parameter:
    """Build a numeric parameter definition for builtin equation functions."""
    return Parameter(name, default=default, required=required)


def _boolean_param(name: str, *, default=None, required: bool = False) -> Parameter:
    """Build a boolean parameter definition for builtin equation functions."""
    return Parameter(name, takes_boolean=True, default=default, required=required)
