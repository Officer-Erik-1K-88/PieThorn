from abc import abstractmethod, ABC
from typing import Callable, Iterable, TypeVar, Any, Sequence, MutableSequence, overload

from piethorn.collections.views import SequenceView, MapView
from piethorn.typing import argument


def _listener_name(name: int | str) -> str:
    if isinstance(name, int):
        return f"event_{name}"
    return name

class Event:
    def __init__(
            self,
            builder: _EventBuilder,
            caller: Listener,
    ):
        self._builder = builder
        self._caller = caller
        self._args: tuple = ()
        self._kwargs: dict = {}
        self._in_use: bool = False

    @property
    def name(self):
        return self._builder.name

    @property
    def caller(self):
        return self._caller

    @property
    def listener(self):
        return self._builder.caller

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def pass_values(self, args: tuple=(), kwargs: dict | None=None):
        if not self._in_use:
            self._args = args
            self._kwargs = kwargs if kwargs is not None else {}


class _EventBuilder:
    def __init__(
            self,
            caller: Listener,
            static: bool = False,
    ):
        self._caller: Listener = caller
        name = caller.name if caller.name.lower().startswith("event") else f"event_{caller.name}"
        self._name = name.replace("_", " ").title().replace(" ", "")
        self._static = static
        self._values: dict[str, Any] = {}
        self._values_view = MapView(self._values)
        self._build = None

    @property
    def caller(self):
        return self._caller

    @property
    def name(self):
        return self._name

    @property
    def static(self):
        return self._static

    @property
    def values(self):
        return self._values_view

    def add_value(self, key: str, value: Any):
        self._values[key] = value

    def build(self, caller: Listener, args, kwargs) -> Event:
        if not self._static or self._build is None:
            self._build = Event(self, caller)
        self._build.pass_values(args, kwargs)
        return self._build


class Listener:
    def __init__(self, name: int | str, gives_static_events: bool = False):
        self._name = _listener_name(name)
        self.__callers__: list[Callable[[Event], bool]] = []
        self._event = _EventBuilder(self, gives_static_events)

    @property
    def name(self):
        return self._name

    @property
    def event(self):
        return self._event

    def generate_event(self, args: tuple, kwargs: dict, *, caller: Listener | None=None) -> Event:
        return self._event.build(caller if caller is not None else self, args, kwargs)

    def use(self, *args, **kwargs):
        for calling in self.__callers__:
            if callable(calling):
                caller_event = self._event.build(self, args, kwargs)
                caller_event._in_use = True
                cont = calling(caller_event)
                caller_event._in_use = False
                if not cont:
                    break

    def add(self, caller: Callable[[Event], bool]):
        if not callable(caller):
            raise TypeError("Cannot add a caller that isn't callable.")
        self.__callers__.append(caller)

    def get(self, index: int):
        return self.__callers__[index]

    def remove(self, caller):
        self.__callers__.remove(caller)

    def __len__(self):
        return self.__callers__.__len__()


class Listenable:
    def __init__(self, event_count: int = 1, *named: str):
        self.__listeners__: dict[str, Listener] = {}

        if event_count >= 1:
            for i in range(event_count):
                listener = Listener(i)
                self.__listeners__[listener.name] = listener
        for name in named:
            listener = Listener(name)
            self.__listeners__[listener.name] = listener

    def get_listener(self, name: int | str):
        """
        Gets a Listener for use.

        :param name: The name of the Listener to get.
        :return: The Listener with the provided name.
        """
        return self.__listeners__[_listener_name(name)]

    def add_listener(self, name: int | str, caller: Callable):
        """
        Adds a function to a Listener.

        :param name: The name of the Listener to add a caller to.
        :param caller: The function to call when it's listener's use method is called.
        """
        self.get_listener(name).add(caller)

    def remove_listener(self, name: int | str, caller: Callable):
        """
        Removes a function from a Listener.

        :param name: The name of the Listener to remove a caller from.
        :param caller: The function to remove.
        :return:
        """
        self.get_listener(name).remove(caller)

    def __len__(self):
        return self.__listeners__.__len__()


class ListenerSequence[T](Listenable, Sequence[T], ABC):
    def __init__(self):
        super().__init__(0, "get")

    @abstractmethod
    def __getter__(self, index):
        pass

    def __getitem__(self, index: int | slice):
        value = self.__getter__(index)
        self.get_listener("get").use(value, index)
        return value


class MutableListenerSequence[T](ListenerSequence[T], MutableSequence[T]):
    def __init__(self):
        super().__init__()
        for name in ("add", "set", "remove"):
            listener = Listener(name)
            self.__listeners__[listener.name] = listener

    @abstractmethod
    def __setter__(self, index: int | slice, value: T | Iterable[T]) -> T:
        pass

    @abstractmethod
    def __adder__(self, index: int | slice, value: T | Iterable[T]):
        pass

    @abstractmethod
    def __remover__(self, index: int | slice | argument.Argument.empty) -> tuple[T, bool]:
        pass

    def insert(self, index, value):
        self.__adder__(index, value)
        self.get_listener("add").use(index, value)

    def __setitem__(self, key: int | slice, value: T | Iterable[T]):
        self.get_listener("set").use(key, self.__setter__(key, value), value)

    def __delitem__(self, index):
        value, removed = self.__remover__(index)
        self.get_listener("remove").use(index, value, removed)