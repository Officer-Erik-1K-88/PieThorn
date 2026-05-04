"""Listener callback chains and the builder that stores them by name."""

from __future__ import annotations

import re
from typing import Any, TypeAlias, Callable, TYPE_CHECKING

from piethorn.collections.listener.event import EventBuilder, DEFAULT_EVENT_BUILDER, Event, EventEnd
from piethorn.collections.mapping import Map

if TYPE_CHECKING:
    from piethorn.collections.listener.listenable import Listenable


def _listener_name(name: int | str) -> str:
    """
    Normalize a listener name.

    :param name: A listener name or integer event index.
    :return: The normalized listener name.
    """
    if isinstance(name, int):
        return f"event_{name}"
    return name

class GetListenerError(Exception):
    """Raised when a requested ``Listener`` cannot be found."""

    pass

caller_type: TypeAlias = Callable[[Event], bool]

class Listener:
    """Named callback chain that receives ``Event`` objects when triggered."""

    def __init__(
            self,
            name: int | str,
            event_builder: EventBuilder=DEFAULT_EVENT_BUILDER,
    ):
        """
        Create a listener with an event builder.

        :param name: The listener name. Integers are normalized as ``event_{name}``.
        :param event_builder: Builder used to create events for this listener.
        """
        self._name = _listener_name(name)
        self.__callers__: list[caller_type] = []
        self._event_builder = event_builder.new_listener(self)
        self._builder = None

    @property
    def name(self):
        """The normalized name of this listener."""
        return self._name

    @property
    def event_builder(self):
        """The ``EventBuilder`` used to create events for this listener."""
        return self._event_builder

    def event(self, args: tuple, kwargs: dict, returned: Any, called_method, *, caller: Listener | None=None) -> Event:
        """
        Build the event object passed to this listener's callbacks.

        This delegates event reuse and context storage to ``event_builder``.

        :param args: The values to be passed to the ``Event.args`` property.
        :param kwargs: The key-value pairs to be passed to the ``Event.kwargs`` property.
        :param returned: The value to be passed to the ``Event.returned`` property.
        :param called_method: The method that triggered this listener.
        :param caller: The ``Listener`` that called the event. Leave empty to default to ``event_builder.listener``.
        :return: The created ``Event``.
        """
        return self.event_builder.build(args, kwargs, returned, called_method, caller=caller)

    def use(self, args: tuple, kwargs: dict, returned: Any, called_method):
        """
        Dispatch an event through this listener's callback chain.

        Each callback receives an ``Event``. Returning ``False`` from a callback
        stops the chain, and callbacks may also stop dispatch through
        ``Event.stop_current()``, ``Event.stop_chain()``, or ``Event.end()``.

        :param args: The values to be passed to the ``Event.args`` property.
        :param kwargs: The key-value pairs to be passed to the ``Event.kwargs`` property.
        :param returned: The value to be passed to the ``Event.returned`` property.
        :param called_method: The method that triggered this listener.
        """
        def flag_end_current(event):
            """Reset and report the current-listener stop flag."""
            if event.end_current:
                event._end_current = False
                return True
            return False
        def flag_end_chain(event, contin):
            """Report whether the listener chain should stop."""
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
        Allows this listener to be used as a callback for another listener.

        The incoming event is passed through this listener's caller chain. If a
        caller returns ``False`` or sets ``event.end_current``, the chain stops.

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
        """
        Append a callback to this listener's dispatch chain.

        :param caller: Callable that accepts an ``Event`` and optionally returns ``False`` to stop dispatch.
        :raises TypeError: If ``caller`` is not callable.
        """
        if not callable(caller):
            raise TypeError("Cannot add a caller that isn't callable.")
        self.__callers__.append(caller)

    def get(self, index: int):
        """
        Return the callback at a specific position in the dispatch chain.

        :param index: The index of the item to get.
        :return: The requested callback.
        """
        return self.__callers__[index]

    def remove(self, caller):
        """
        Remove a callback from this listener's dispatch chain.

        :param caller: The callback to remove.
        :raises ValueError: If ``caller`` is not in the chain.
        """
        self.__callers__.remove(caller)

    def __len__(self):
        """Return the number of callers in this listener chain."""
        return len(self.__callers__)


class ListenerBuilder:
    """Mutable registry for named ``Listener`` instances."""

    def __init__(
            self,
            default_event_builder: EventBuilder=DEFAULT_EVENT_BUILDER,
    ):
        """
        Create a listener builder.

        :param default_event_builder: Builder used when a listener-specific builder is not provided.
        """
        self.__listeners__: Map[str, Listener] = Map()
        self._listenable: Listenable | None = None
        self._event_builder: EventBuilder = default_event_builder

    def at(self, index: int) -> Listener:
        """
        Return the listener stored at a positional index.

        :param index: The index of the listener.
        :raises GetListenerError: If there is no listener at ``index``.
        :return: The listener at ``index``.
        """
        try:
            return self.__listeners__.value_at_index(index)
        except IndexError:
            raise GetListenerError("There is no Listener at index '%s'" % index)

    def get(self, name: int | str) -> Listener:
        """
        Return a listener by normalized name.

        Integer names normalize to ``event_{name}``. String names that match
        ``event_[0-9]+`` may also fall back to positional lookup when no exact
        key exists.

        :param name: The name of the listener. If name is an integer, then ``event_{name}`` is checked.
        :raises GetListenerError: If there is no listener with ``name``.
        :return: The matching listener.
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
        Return a listener by name first, then by index when possible.

        This is useful for APIs that accept either a listener name or an event
        index. String values only act as indexes when they match
        ``event_[0-9]+``.

        :param name: The name of the listener. Or the index of the listener.
        :raises GetListenerError: If no listener can be resolved.
        :return: The resolved listener.
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
        Return whether a listener exists for a normalized name.

        :param name: The name of the listener. If name is an integer, then ``event_{name}`` is checked.
        :return: Whether the listener exists.
        """
        return self.__listeners__.has_key(_listener_name(name))

    def build(self, name: int | str, event_builder: EventBuilder | None=None):
        """
        Create a listener without adding it to this builder.

        Use ``add`` when the listener should be stored in this registry.

        :param name: The name of the listener. If name is an integer, then the name is set as ``event_{name}``.
        :param event_builder: The ``EventBuilder`` object that will be used to create the ``Event``s of the listener.
        :return: The new ``Listener`` object.
        """
        return Listener(name, event_builder if event_builder is not None else self._event_builder)

    def add(self, name: int | str, event_builder: EventBuilder | None=None, *, replace: bool = False):
        """
        Store and return a listener for ``name``.

        Existing listeners are reused when ``replace`` is ``False``. Passing
        ``replace=True`` creates a new listener and overwrites the old entry.

        :param name: The name of the listener. If name is an integer, then the name is set as ``event_{name}``.
        :param event_builder: The ``EventBuilder`` object that will be used to create the ``Event``s of the listener.
        :param replace: Whether to replace the existing listener if one exists.
        :return: The new ``Listener`` object.
        """
        listener = self.build(name, event_builder)
        if not replace and listener.name in self.__listeners__:
            return self.__listeners__[listener.name]
        listener._builder = self
        self.__listeners__[listener.name] = listener
        return listener

    def pop(self, index: int, default=None):
        """
        Remove and return the listener stored at ``index``.

        :param index: The index of the listener to remove.
        :param default: The default value to return if the listener does not exist.
        :return: The removed listener, or ``default`` when the index is missing.
        """
        try:
            listener = self.at(index)
        except GetListenerError:
            return default
        else:
            return self.remove(listener.name, default)

    def remove(self, name: int | str, default=None):
        """
        Remove and return the listener stored under ``name``.

        :param name: The name of the listener. If name is an integer, then ``event_{name}`` is checked.
        :param default: The default value to return if the listener does not exist.
        :return: The removed listener, or ``default`` when the name is missing.
        """
        return self.__listeners__.pop(_listener_name(name), default)

    def __len__(self):
        """Return the number of listeners stored by this builder."""
        return len(self.__listeners__)

    def __iter__(self):
        """Iterate over stored ``Listener`` instances."""
        return iter(self.__listeners__.values())
