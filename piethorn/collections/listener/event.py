from __future__ import annotations

from typing import Any


class EventEnd(Exception):
    def __init__(self, event: Event):
        super().__init__(f"Event {event.name} ended")
        self.event = event


class Event:
    """
    Actions
    -------

    The actions of an ``Event`` is defined by whether it's ``EventBuilder`` is
    static. If it is static, then the event's actions are deemed to span across
    the entire caller chain of the ``Listener``. While when it isn't static,
    the event's actions are deemed to only span the workings of a single ``caller_type``.
    """
    from piethorn.collections.listener import Listener

    def __init__(
            self,
            builder: EventBuilder,
            caller: Listener,
    ):
        self._builder = builder
        self._caller = caller
        self._args: tuple = ()
        self._kwargs: dict = {}
        self._returned = None
        self._called_method = None
        self._in_use: bool = False
        self._end: bool = False

    @property
    def name(self):
        """The name of the event"""
        return self._builder.name

    @property
    def caller(self):
        """The ``Listener`` that called this event"""
        return self._caller

    @property
    def listener(self):
        """The ``Listener`` that built this event"""
        return self._builder.listener

    @property
    def end_chain(self):
        return self._end

    @property
    def active(self):
        return self._in_use

    @property
    def args(self):
        """The arguments passed to the action that called this event"""
        return self._args

    @property
    def kwargs(self):
        """The keyword arguments passed to the action that called this event"""
        return self._kwargs

    @property
    def returned(self):
        """The value that was returned by the action that called this event"""
        return self._returned

    @property
    def called_method(self):
        """
        The method that called this event.

        This can be dangerous to use, especially
        when it is a setter, adder, or deleter as
        if ``Event.called_method(*Event.args, **Event.kwargs)``
        is called, then it would essentially be calling the same
        function a second time.
        """
        return self._called_method

    def pass_values(self, args: tuple = (), kwargs: dict | None = None, returned=None, called_method=None):
        if not self.active:
            self._args = args
            self._kwargs = kwargs if kwargs is not None else {}
            self._returned = returned
            self._called_method = called_method

    def end(self, force: bool = False, end_chain_when_forced: bool = False):
        """
        Used to call the end of this event.

        If ``force`` is ``True``, then the ``EventEnd`` exception will be raised,
        this will end all event actions of the current ``caller_type``,
        but will not trigger ``end_chain``.
        To have ``end_chain`` set to ``True`` when ``force``, then ``end_chain_when_forced``
        must be ``True``, it's default to ``False``.

        While if ``force`` is ``False``, then the ``end_chain`` boolean will be set to ``True``
        and will finish event actions of the current ``caller_type`` before ending the caller chain of the ``Listener``.

        :param force: Whether to force end all further event actions.
        :param end_chain_when_forced: Whether to end the caller chain of the ``Listener`` when ``force`` is ``True``.
        :return:
        """
        if force:
            if end_chain_when_forced:
                self._end = True
            raise EventEnd(self)
        else:
            self._end = True


class EventBuilder:
    from piethorn.collections.listener import Listener
    def __init__(
            self,
            listener: Listener | None = None,
            static: bool = False,
            copies_to_new: bool = False,
    ):
        from piethorn.collections.listener import Listener
        self._listener: Listener | None = None
        self._name = "UNKNOWN_EVENT"
        self._static = static
        self._copies_to_new = copies_to_new
        self._build = None
        if listener is not None:
            self._set_listener(listener)

    @property
    def listener(self):
        """The ``Listener`` that this ``EventBuilder`` is attributed to"""
        return self._listener

    @property
    def name(self):
        return self._name

    @property
    def static(self):
        return self._static

    @property
    def copies_to_new(self):
        return self._copies_to_new

    def build(self, args: tuple, kwargs: dict, returned: Any, called_method, *, caller: Listener | None = None) -> Event:
        """
        Builds an ``Event``.

        If this ``EventBuilder`` is ``static``,
        then this builder will only build one ``Event``.

        Use ``clear_event`` to clear the built ``Event``.

        :param args:
        :param kwargs:
        :param returned:
        :param called_method:
        :param caller:
        :return:
        """
        if caller is None:
            caller = self.listener
        if not self._static or self._build is None:
            self._build = self.make_event(caller)
        self._build.pass_values(args, kwargs, returned, called_method)
        return self._build

    def make_event(self, caller: Listener) -> Event:
        return Event(self, caller)

    def clear_event(self, destabilize_event: bool = False) -> Event | None:
        """
        Used to clear the built ``Event``.

        This method is mainly used in ``Listener.use``
        to clear the built ``Event`` at the end
        of the built ``Event``'s life cycle.

        :param destabilize_event: Whether to make the cleared ``Event`` unusable.
        :return: The removed ``Event``.
        """
        event = self._build
        self._build = None
        if event is not None:
            if destabilize_event:
                event._builder = None
            if event.active:
                # TODO: Make it so that we can terminate event life cycle without the need of throwing an error.
                raise RuntimeError("Cannot clear an active event. This may change in the future.")
        return event

    def copy(self, **kwargs) -> EventBuilder:
        event_builder = EventBuilder(
            listener=kwargs.pop("listener", self.listener),
            static=kwargs.pop("static", self.static),
            copies_to_new=kwargs.pop("copies_to_new", self.copies_to_new),
        )
        return event_builder

    def _set_listener(self, listener: Listener):
        self._listener = listener
        name = listener.name if listener.name.lower().startswith("event_") else f"event_{listener.name}"
        self._name = name.replace("_", " ").title().replace(" ", "")
        self._build = None

    def new_listener(self, listener: Listener) -> EventBuilder:
        """
        Updates this ``EventBuilder``'s ``Listener``.

        If ``copies_to_new`` is true, then this method will
        create a ``copy`` of this ``EventBuilder`` with the
        new ``Listener``.

        :param listener: The new ``Listener``.
        :return: This ``EventBuilder`` or a new ``EventBuilder``.
        """
        event_builder = self
        if self.copies_to_new:
            event_builder = self.copy(listener=listener)
        else:
            if listener is not self.listener:
                event_builder._set_listener(listener)
        return event_builder


DEFAULT_EVENT_BUILDER = EventBuilder(static=True, copies_to_new=True)