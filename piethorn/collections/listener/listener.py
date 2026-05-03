from __future__ import annotations

import re
from typing import Any, TypeAlias, Callable, TYPE_CHECKING

from piethorn.collections.listener.event import EventBuilder, DEFAULT_EVENT_BUILDER, Event, EventEnd
from piethorn.collections.mapping import Map

if TYPE_CHECKING:
    from piethorn.collections.listener.listenable import Listenable


def _listener_name(name: int | str) -> str:
    if isinstance(name, int):
        return f"event_{name}"
    return name

class GetListenerError(Exception):
    pass

caller_type: TypeAlias = Callable[[Event], bool]

class Listener:
    def __init__(
            self,
            name: int | str,
            event_builder: EventBuilder=DEFAULT_EVENT_BUILDER,
    ):
        self._name = _listener_name(name)
        self.__callers__: list[caller_type] = []
        self._event_builder = event_builder.new_listener(self)
        self._builder = None

    @property
    def name(self):
        return self._name

    @property
    def event_builder(self):
        return self._event_builder

    def event(self, args: tuple, kwargs: dict, returned: Any, called_method, *, caller: Listener | None=None) -> Event:
        """
        Builds an event with ``event_builder``.

        Refer to ``EventBuilder.build`` for further information on how events are built.

        :param args: The values to be passed to the ``Event.args`` property.
        :param kwargs: The key-value pairs to be passed to the ``Event.kwargs`` property.
        :param returned: The value to be passed to the ``Event.returned`` property.
        :param called_method:
        :param caller: The ``Listener`` that called the event. Leave empty to default to ``event_builder.listener``.
        :return: The created ``Event``.
        """
        return self.event_builder.build(args, kwargs, returned, called_method, caller=caller)

    def use(self, args: tuple, kwargs: dict, returned: Any, called_method):
        """
        Calls this ``Listener``'s caller chain.

        The caller chain is the list of ``caller_type``s
        that are to be called when the ``Listener`` is triggered.

        The boolean returned by a ``caller_type`` is used to determine whether
        the next ``caller_type`` is called. So, if it returns ``False``, then
        no further callers in the caller chain will be called.

        :param args: The values to be passed to the ``Event.args`` property.
        :param kwargs: The key-value pairs to be passed to the ``Event.kwargs`` property.
        :param returned: The value to be passed to the ``Event.returned`` property.
        :param called_method:
        :return:
        """
        def flag_end_current(event):
            if event.end_current:
                event._end_current = False
                return True
            return False
        def flag_end_chain(event, contin):
            if event.end_chain or contin is False:
                return True
            return False
        try:
            for calling in self.__callers__:
                if not callable(calling):
                    continue
                flag_break = False

                try:
                    if not self._event_builder.static:
                        self._event_builder.clear_event()

                    caller_event = self.event(args, kwargs, returned, called_method)
                    caller_event._in_use = True

                    try:
                        cont = calling(caller_event)
                    finally:
                        caller_event._in_use = False

                    flag_continue = flag_end_current(caller_event)
                    flag_break = flag_end_chain(caller_event, cont)

                    if flag_break:
                        break
                    if flag_continue:
                        continue
                except EventEnd as e:
                    e.event._in_use = False
                    flag_continue = flag_end_current(e.event)
                    flag_break = flag_end_chain(e.event, True)
                    if flag_break:
                        break
                    if flag_continue:
                        continue

                if flag_break:
                    break
        finally:
            self._event_builder.clear_event()

    def __call__(self, event: Event) -> bool:
        """
        A ``Listener`` callable so that they can be passed as a ``caller_type``.

        If ``event.end_current`` is ``True``, then will end the caller chain.

        :param event: The event from the calling ``Listener``.
        :return: Whether the calling listener should continue its caller chain.
        """
        cont = True
        for calling in self.__callers__:
            if callable(calling):
                cont = calling(event)
                if event.end_current or cont is False:
                    break
        return cont

    def add(self, caller: caller_type):
        if not callable(caller):
            raise TypeError("Cannot add a caller that isn't callable.")
        self.__callers__.append(caller)

    def get(self, index: int):
        return self.__callers__[index]

    def remove(self, caller):
        self.__callers__.remove(caller)

    def __len__(self):
        return len(self.__callers__)


class ListenerBuilder:
    def __init__(
            self,
            default_event_builder: EventBuilder=DEFAULT_EVENT_BUILDER,
    ):
        self.__listeners__: Map[str, Listener] = Map()
        self._listenable: Listenable | None = None
        self._event_builder: EventBuilder = default_event_builder

    def at(self, index: int) -> Listener:
        """
        Gets the ``Listener`` at ``index``.

        :param index: The index of the listener
        :raises GetListenerError: If there is no listener at ``index``.
        :return:
        """
        try:
            return self.__listeners__.value_at_index(index)
        except IndexError:
            raise GetListenerError("There is no Listener at index '%s'" % index)

    def get(self, name: int | str) -> Listener:
        """
        Gets the listener at ``name``.

        :param name: The name of the listener. If name is an integer, then ``event_{name}`` is checked.
        :raises GetListenerError: If there is no listener with ``name``.
        :return:
        """
        check_name = _listener_name(name)
        try:
            return self.__listeners__[check_name]
        except KeyError:
            if isinstance(name, str):
                match = re.fullmatch('event_([0-9]+)', check_name, flags=re.IGNORECASE)
                if match:
                    try:
                        return self.__listeners__.value_at_index(int(match.group(1)))
                    except IndexError:
                        pass
            raise GetListenerError("Listener '%s' not found" % check_name)

    def get_at(self, name: int | str) -> Listener:
        """
        This method combines ``get`` and ``at`` methods.

        It first tries to get the listener at ``name``.
        If that fails, then will attempt to use ``name``
        as the index of the listener. ``name`` can only
        be used as an index if ``name`` is an integer
        or is of the pattern ``event_[0-9]+``.

        :param name: The name of the listener. Or the index of the listener.
        :raises GetListenerError:
        :return:
        """
        try:
            return self.get(name)
        except GetListenerError as e:
            index = name
            if isinstance(name, str):
                match = re.fullmatch('event_([0-9]+)', name, flags=re.IGNORECASE)
                if match:
                    index = int(match.group(1))
            if isinstance(index, int):
                return self.at(index)
            raise e

    def has(self, name: int | str) -> bool:
        """
        Checks if a ``Listener`` with the given ``name`` exists.
        :param name: The name of the listener. If name is an integer, then ``event_{name}`` is checked.
        :return:
        """
        return self.__listeners__.has_key(_listener_name(name))

    def build(self, name: int | str, event_builder: EventBuilder | None=None):
        return Listener(name, event_builder if event_builder is not None else self._event_builder)

    def add(self, name: int | str, event_builder: EventBuilder | None=None, *, replace: bool = False):
        listener = self.build(name, event_builder)
        if not replace and listener.name in self.__listeners__:
            return self.__listeners__[listener.name]
        listener._builder = self
        self.__listeners__[listener.name] = listener
        return listener

    def pop(self, index: int, default=None):
        try:
            listener = self.at(index)
        except GetListenerError:
            return default
        else:
            return self.remove(listener.name, default)

    def remove(self, name: int | str, default=None):
        return self.__listeners__.pop(_listener_name(name), default)

    def __len__(self):
        return len(self.__listeners__)

    def __iter__(self):
        return iter(self.__listeners__.values())