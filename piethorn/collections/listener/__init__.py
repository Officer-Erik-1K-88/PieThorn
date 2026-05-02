from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Iterable, MutableSequence, Sequence

from piethorn.collections.listener.event import Event, EventBuilder, EventEnd, DEFAULT_EVENT_BUILDER
from piethorn.collections.listener.listenable import Listenable, ListenerHolder, GLOBAL_LISTENERS
from piethorn.collections.listener.listener import Listener, ListenerBuilder, GetListenerError
from piethorn.collections.listener.listens import listens

__all__ = [
    # Event stuff
    "Event",
    "EventBuilder",
    "DEFAULT_EVENT_BUILDER",
    "EventEnd",
    # Listener stuff
    "GetListenerError",
    "Listener",
    "ListenerBuilder",
    # Listenable stuff
    "Listenable",
    "ListenerHolder",
    "GLOBAL_LISTENERS",
    # Decorators
    "listens",
    # Abstract Classes
    "ListenerSequence",
    "MutableListenerSequence",
]

class ListenerSequence[T](Listenable, Sequence[T], ABC):
    def __init__(self):
        super().__init__("get")

    @listens("get")
    @abstractmethod
    def __getitem__(self, index: int | slice):
        pass


class MutableListenerSequence[T](ListenerSequence[T], MutableSequence[T]):
    def __init__(self):
        super().__init__()
        for name in ("add", "set", "remove"):
            self.__listeners__.add(name)

    @listens("add")
    @abstractmethod
    def insert(self, index, value):
        pass

    @listens("set")
    @abstractmethod
    def __setitem__(self, key: int | slice, value: T | Iterable[T]):
        pass

    @listens("remove")
    @abstractmethod
    def __delitem__(self, index):
        pass