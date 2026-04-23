from __future__ import annotations

from decimal import Decimal
from typing import Generic, TypeVar

T = TypeVar("T")


class EquationPiece(Generic[T]):
    """Wrap a typed token value used by the equation parser."""

    def __init__(self, value: T):
        self._value = value
        self._parent = None

    @property
    def value(self) -> T:
        """Return the wrapped token value."""
        return self._value

    @property
    def parent(self) -> EquationPiece | None:
        """Return the parent equation piece."""
        return self._parent

    def has_parent(self) -> bool:
        """Return True if the equation piece has a parent."""
        return self._parent is not None


class Variable(EquationPiece[str]):
    """Represent a variable token referenced inside an equation string."""

    def __init__(self, name: str, default: str = None):
        super().__init__(name)
        self._default = default

    @property
    def default(self):
        return self._default

    def has_default(self):
        return self.default is not None


class Number(EquationPiece[Decimal]):
    """Represent a decimal literal parsed from an equation."""

    def __init__(self, number: Decimal):
        super().__init__(number)
