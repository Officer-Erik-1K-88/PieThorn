from __future__ import annotations

from typing import Iterable, MutableSequence, overload

from .functions import FUNCTIONS, Function
from .parameters import Param, Parameters
from .tokens import EquationPiece, Variable
from .errors import ChildError


class ParsedEquation(EquationPiece[list[EquationPiece]], MutableSequence[EquationPiece]):
    """Store the mutable parsed token tree for an equation expression."""

    def __init__(self, parsed_equation: Iterable[EquationPiece]=None):
        super().__init__([] if parsed_equation is None else list(parsed_equation))
        self._variable_count = 0
        self._variable_count_default = 0
        self._in_sub = False
        self._in_function = False

    @property
    def var_count(self):
        return self._variable_count
    @property
    def var_count_default(self):
        return self._variable_count_default

    @property
    def in_sub(self):
        """Return whether parsing is currently inside a sub-expression."""
        return self._in_sub

    def enter_sub(self):
        """Mark the current parsed equation as entering a sub-expression."""
        self.get_current()._in_sub = True

    def exit_sub(self):
        """Leave the current sub-expression, if one is active."""
        try:
            current = self.get_current()
            current._in_sub = False
            if current is not self:
                if current._parent is not None:
                    current._parent._in_sub = False
                else:
                    self._in_sub = False
        except ChildError:
            self._in_sub = False

    def get_sub(self, throw_on_not_found=False, throw_on_zero=False):
        """Return the active child sub-expression, creating it when allowed."""
        if self._in_sub:
            if len(self._value) == 0:
                if throw_on_zero:
                    raise ChildError("The parent ParsedEquation is empty")
                # Lazily create the nested expression container on first access.
                child = ParsedEquation()
                self._value.append(child)
                self._added(child)
            last_val = self._value[len(self._value) - 1]
            if not isinstance(last_val, ParsedEquation):
                if throw_on_not_found:
                    raise ChildError(f"The last value `{last_val}` is not a ParsedEquation")
                last_val = ParsedEquation()
                self._value.append(last_val)
                self._added(last_val)
            if last_val.in_sub:
                return last_val.get_sub(throw_on_not_found, throw_on_zero)
            return last_val
        raise ChildError("Not in a child process")

    def get_current(self, sub_tonf=False, sub_toz=False) -> ParsedEquation:
        """Return the currently active parse target."""
        # Route writes into the deepest active scope: sub-expression first,
        # then the current function argument, otherwise the root expression.
        if self._in_sub:
            return self.get_sub(sub_tonf, sub_toz)
        if self._in_function:
            func = self.get_function()
            if len(func.parameters) != 0:
                return func.get_param().get_current(sub_tonf, sub_toz)
        return self

    @property
    def in_function(self):
        """Return whether parsing is currently inside a function call."""
        return self._in_function

    def enter_function(self, name: str, index: int):
        """Begin capturing arguments for the named function."""
        current = self.get_current(sub_tonf=True, sub_toz=True)
        func = EquationFunc(index, name)
        current._value.append(func)
        current._added(func)
        current._in_function = True

    def exit_function(self):
        """Leave the current function-call parsing context."""
        current = self.get_current(sub_tonf=True, sub_toz=True)
        current._in_function = False
        if current is not self:
            if current._parent is not None:
                current._parent._in_function = False
            else:
                self._in_function = False
        #self.get_function_parent()._in_function = False

    def get_function_parent(self):
        """Return the ParsedEquation node that owns the active function call."""
        if self._in_sub:
            return self.get_sub(True, True).get_function_parent()
        if self._in_function:
            return self
        if self._parent is not None:
            return self._parent.get_function_parent()
        raise ChildError("Not in a child process")

    def get_function(self):
        """Return the active parsed function call."""
        if self._in_function:
            if len(self._value) == 0:
                raise ChildError("The parent ParsedEquation is empty")
            last_val = self._value[len(self._value) - 1]
            if not isinstance(last_val, EquationFunc):
                raise ChildError(f"The last value `{last_val}` is not a EquationFunc")
            return last_val
        raise ChildError("Not in a child process")

    def index(self, value, start=0, stop=None):
        """Return the index of ``value`` in the active parse target."""
        curr_value = self.get_current(True, True)._value
        if stop is None:
            return curr_value.index(value, start)
        return curr_value.index(value, start, stop)

    def count(self, value):
        """Count ``value`` within the active parse target."""
        return self.get_current(True, True)._value.count(value)

    def _count_variable(self, variable: Variable, rev: bool = False):
        """Count ``variable`` within the active parse target and it's parents."""
        self._variable_count += -1 if rev else 1
        if variable.has_default():
            self._variable_count_default += -1 if rev else 1
        if self.has_parent() and isinstance(self._parent, ParsedEquation):
            self._parent._count_variable(variable)

    def _added(self, value: EquationPiece):
        value._parent = self
        if isinstance(value, Variable):
            self._count_variable(value)

    def _removed(self, value: EquationPiece):
        value._parent = None
        if isinstance(value, Variable):
            self._count_variable(value, True)

    def insert(self, index: int, value: EquationPiece):
        """Insert a parsed token into the active parse target."""
        current = self.get_current(True, True)
        current._value.insert(index, value)
        current._added(value)

    def append(self, value: EquationPiece):
        """Append a parsed token to the active parse target."""
        current = self.get_current()
        current._value.append(value)
        current._added(value)

    def extend(self, values: Iterable[EquationPiece]):
        """Append multiple parsed tokens to the active parse target."""
        current = self.get_current()
        if values is current:
            raise ValueError("Cannot extend because `values` is `current` ParsedEquation")
        for v in values:
            current._value.append(v)
            current._added(v)

    def reverse(self):
        """Not available on ParsedEquation"""
        raise NotImplementedError("`reverse` not implemented")

    def clear(self):
        """Clear the active parse target and exit nested parse states."""
        current = self.get_current(True, True)
        for v in current._value:
            current._removed(v)
        current._value.clear()
        current._in_function = False
        current._in_sub = False

    def pop(self, index: int=-1):
        """Remove and return an item from the active parse target."""
        current = self.get_current(True, True)
        value = current._value.pop(index)
        current._removed(value)
        return value

    def remove(self, value):
        """Remove the first matching token from the active parse target."""
        current = self.get_current(True, True)
        index = current._value.index(value)
        v = current._value.pop(index)
        current._removed(v)

    def __iadd__(self, values):
        self.extend(values)
        return self

    @overload
    def __getitem__(self, index: int) -> EquationPiece: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequence[EquationPiece]: ...
    def __getitem__(self, index):
        current = self.get_current(True, True)
        value = current._value[index]
        if isinstance(value, EquationPiece):
            return value
        ret = ParsedEquation(value)
        ret._parent = current
        return ret

    @overload
    def __setitem__(self, index: int, value: EquationPiece) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[EquationPiece]) -> None: ...
    def __setitem__(self, index, value):
        current = self.get_current(True, True)
        if isinstance(value, EquationPiece):
            assert isinstance(index, int)
            current._added(value)
        elif isinstance(value, Iterable):
            assert isinstance(index, slice)
            for v in value:
                current._added(v)
        else:
            raise TypeError("`value` must be an EquationPiece or Iterable")
        # noinspection PyTypeChecker
        old = current._value[index]
        if isinstance(old, EquationPiece):
            current._removed(old)
        elif isinstance(old, Iterable):
            for v in old:
                current._removed(v)
        # noinspection PyTypeChecker
        current._value[index] = value

    @overload
    def __delitem__(self, index: int) -> None: ...
    @overload
    def __delitem__(self, index: slice) -> None: ...
    def __delitem__(self, index):
        current = self.get_current(True, True)
        value = current._value[index]
        if isinstance(value, EquationPiece):
            current._removed(value)
        elif isinstance(value, Iterable):
            for v in value:
                current._removed(v)
        del current._value[index]

    def __len__(self):
        try:
            return len(self.get_current(True, True)._value)
        except ChildError:
            return 0

    def __iter__(self):
        try:
            return iter(self.get_current(True, True)._value)
        except ChildError:
            return iter(())

    def __contains__(self, value):
        try:
            return self.get_current(True, True)._value.__contains__(value)
        except ChildError:
            return False

    def __reversed__(self):
        return self.get_current(True, True)._value.__reversed__()


class FuncParam(ParsedEquation, Param):
    """Represent a function argument whose value is itself a parsed equation."""

    def __init__(
            self,
            name: str,
            takes_boolean: bool,
            required: bool,
            default=None,
            value: Iterable[EquationPiece]=None,
    ):
        super().__init__(value)
        self._name = name
        self._takes_boolean = takes_boolean
        self._required = required
        self._default = default

    @property
    def name(self):
        """Return the parameter name."""
        return self._name

    @property
    def takes_boolean(self):
        """Return whether the parameter accepts boolean expressions."""
        return self._takes_boolean

    @property
    def required(self):
        """Return whether this parameter must be supplied."""
        return self._required

    @property
    def default(self):
        """Return the default parsed value for this parameter."""
        return self._default


class EquationFunc(EquationPiece[int]):
    """Reference a registered function and its parsed argument values."""

    def __init__(self, index: int, name: str):
        super().__init__(index)
        self._name = name
        self._parameters = Parameters()

    @property
    def name(self) -> str:
        """Return the referenced function name."""
        return self._name

    @property
    def parameters(self) -> Parameters:
        """Return parsed parameters collected for this function call."""
        return self._parameters

    def get(self) -> Function:
        """Return the registered function referenced by this token."""
        return FUNCTIONS[self.value]

    def get_param(self) -> FuncParam:
        """Return the most recently added parameter parse target."""
        param = self._parameters[len(self._parameters) - 1]
        if isinstance(param, FuncParam):
            return param
        raise TypeError("EquationFunc's 'parameters' property isn't composed correctly")

    def add_param(self, param: FuncParam):
        """Append a parsed parameter to this function call."""
        self._parameters = self._parameters + (param,)
