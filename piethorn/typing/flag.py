from __future__ import annotations

from typing import TypeAlias

boolean_type: TypeAlias = 'bool | SetBool'

class SetBool:
    def __init__(
            self,
            value: boolean_type,
            default: bool|None=None,
            and_change: bool=True,
            start_set: bool=False,
            allow_unset_change: bool=False,
    ):
        """

        :param value: The starting value
        :param default: The default value
        :param and_change: Whether when using ``change`` it should use ``and`` or ``or``.
        :param start_set: Whether to define ``set`` as true or false.
        :param allow_unset_change: Whether to allow ``change`` to occur when it's passed a ``SetBool`` with ``set`` false
        """
        if isinstance(value, bool):
            self._value = value
            self._default = default
            self._set = start_set
        else:
            self._value = value.value
            self._default = value.default if default is None else default
            self._set = value.set or start_set
        self._and_change = and_change
        self._allow_unset_change = allow_unset_change
        if self._default is None:
            raise RuntimeError("SetBool must have a default value.")

    @property
    def value(self) -> bool:
        return self._value
    @value.setter
    def value(self, value: bool):
        self._value = value
        self._set = True

    @property
    def set(self) -> bool:
        return self._set

    @property
    def default(self) -> bool:
        # noinspection PyTypeChecker
        return self._default

    @property
    def and_change(self):
        return self._and_change

    @property
    def allow_unset_change(self):
        return self._allow_unset_change

    def reset(self):
        self._set = False
        self._value = self._default

    def change(self, new_value: SetBool):
        if self.allow_unset_change or new_value.set:
            if self.set:
                if self._and_change:
                    self.value = self.value and new_value.value
                else:
                    self.value = self.value or new_value.value
            else:
                self.value = new_value.value

    def __bool__(self):
        return self._value

    def __int__(self):
        return 1 if self._value else 0

    def __float__(self):
        return float(int(self))

    def __str__(self):
        return str(self._value)

    def __eq__(self, other):
        return self._value == other
    def __ne__(self, other):
        return self._value != other
    def __gt__(self, other):
        return self._value > other
    def __lt__(self, other):
        return self._value < other
    def __ge__(self, other):
        return self._value >= other
    def __le__(self, other):
        return self._value <= other