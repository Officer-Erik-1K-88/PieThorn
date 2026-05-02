from __future__ import annotations

import re
from typing import Any, TypeAlias, Callable

from piethorn.collections.listener.event import EventBuilder, DEFAULT_EVENT_BUILDER, Event, EventEnd
from piethorn.collections.mapping import Map


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
        try:
            for calling in self.__callers__:
                if not callable(calling):
                    continue

                try:
                    if not self._event_builder.static:
                        self._event_builder.clear_event()

                    caller_event = self.event(args, kwargs, returned, called_method)
                    caller_event._in_use = True

                    try:
                        cont = calling(caller_event)
                    finally:
                        caller_event._in_use = False

                    if caller_event.end_chain or cont is False:
                        break
                except EventEnd as e:
                    e.event._in_use = False
                    if e.event.end_chain:
                        break
        finally:
            self._event_builder.clear_event()

    def __call__(self, event: Event) -> bool:
        """
        A ``Listener`` callable so that they can be passed as a ``caller_type``.

        :param event: The event from the calling ``Listener``.
        :return: Whether the calling listener should continue its caller chain.
        """
        cont = True
        for calling in self.__callers__:
            if callable(calling):
                cont = calling(event)
                if cont is False:
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

    def get(self, name: int | str) -> Listener:
        if isinstance(name, int):
            try:
                return self.__listeners__.value_at_index(name)
            except IndexError:
                pass
        check_name = _listener_name(name)
        try:
            return self.__listeners__[check_name]
        except KeyError as e:
            if isinstance(name, str):
                match = re.fullmatch('event_([0-9]+)', check_name, flags=re.IGNORECASE)
                if match:
                    try:
                        return self.__listeners__.value_at_index(int(match.group(1)))
                    except IndexError:
                        pass
            raise GetListenerError("Listener '%s' not found" % check_name)

    def has(self, name: int | str) -> bool:
        try:
            self.get(name)
            return True
        except GetListenerError:
            return False

    def build(self, name: int | str, event_builder: EventBuilder | None=None):
        return Listener(name, event_builder if event_builder is not None else self._event_builder)

    def add(self, name: int | str, event_builder: EventBuilder | None=None, *, replace: bool = False):
        listener = self.build(name, event_builder)
        if not replace and listener.name in self.__listeners__:
            return self.__listeners__[listener.name]
        listener._builder = self
        self.__listeners__[listener.name] = listener
        return listener

    def remove(self, name: int | str, default=None):
        if isinstance(name, int):
            try:
                listener = self.__listeners__.value_at_index(name)
            except IndexError:
                return self.__listeners__.pop(_listener_name(name), default)
            else:
                return self.__listeners__.pop(listener.name, default)
        return self.__listeners__.pop(_listener_name(name), default)

    def __len__(self):
        return len(self.__listeners__)

    def __iter__(self):
        return iter(self.__listeners__.values())