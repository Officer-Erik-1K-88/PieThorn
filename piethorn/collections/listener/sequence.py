"""Sequence ABCs that trigger listeners from sequence operations."""

from abc import abstractmethod, ABC
from typing import Iterable, MutableSequence, Sequence

from piethorn.collections.listener.listenable import Listenable
from piethorn.collections.listener.listens import listens


class ListenerSequence[T](Listenable, Sequence[T], ABC):
    """Read-only sequence base class with listener support for item access."""

    def __init__(self):
        """Create a sequence with a ``get`` listener."""
        super().__init__("get")

    @listens("get")
    @abstractmethod
    def __getitem__(self, index: int | slice):
        """
        Get an item or slice from the sequence.

        :param index: The index or slice to read.
        :return: The requested item or sequence slice.
        """
        pass


class MutableListenerSequence[T](ListenerSequence[T], MutableSequence[T]):
    """Mutable sequence base class with listeners for add, set, and remove operations."""

    def __init__(self):
        """Create a mutable sequence with ``add``, ``set``, and ``remove`` listeners."""
        super().__init__()
        for name in ("add", "set", "remove"):
            self.__listeners__.add(name)

    @listens("add")
    @abstractmethod
    def insert(self, index, value):
        """
        Insert a value into the sequence.

        :param index: The index where the value should be inserted.
        :param value: The value to insert.
        """
        pass

    @listens("set")
    @abstractmethod
    def __setitem__(self, key: int | slice, value: T | Iterable[T]):
        """
        Set an item or slice in the sequence.

        :param key: The index or slice to replace.
        :param value: The replacement value or values.
        """
        pass

    @listens("remove")
    @abstractmethod
    def __delitem__(self, index):
        """
        Delete an item or slice from the sequence.

        :param index: The index or slice to delete.
        """
        pass
