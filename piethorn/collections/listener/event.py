from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from piethorn.collections.listener import Listener


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
        self._end_chain: bool = False
        self._end_current: bool = False

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
        """The flag for telling ``Listener.use()`` when to end it's caller chain."""
        return self._end_chain

    @property
    def end_current(self):
        """The flag for telling ``Listener.use()`` when to ensure that the current ``caller_type`` has correctly ended."""
        return self._end_current

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

    def stop_current(self, force: bool = True):
        """
        Used to call the end of this event for the current listener chain item.

        This has no real effect outside of setting ``end_current`` to ``True``.
        However, this method does have an effect when ``force`` is ``True``.

        When ``force`` is ``True``, then the ``EventEnd`` exception will be raised,
        this will end all event actions of the current ``caller_type``.

        :param force: Whether to force end all further event actions. Defaults to ``True``.
        :raises EventEnd: When ``force`` is ``True``.
        :return:
        """
        self._end_current = True
        if force:
            raise EventEnd(self)

    def stop_chain(self, force: bool = False):
        """
        Used to call the end of this event for the caller chain of the ``Listener``.

        Sets the ``end_chain`` boolean to ``True``.

        When ``force`` is ``False``, then the event actions
        of the current ``caller_type`` will finish before
        ending the caller chain of the ``Listener``.

        :param force: Whether to force end all further event actions. Defaults to ``False``.
        :raises EventEnd: When ``force`` is ``True``.
        :return:
        """
        self._end_chain = True
        if force:
            raise EventEnd(self)

    def end(self, force: bool = False):
        """
        Used to call the end of this event.

        Calls both ``stop_current`` and ``stop_chain``.

        If ``force`` is ``True``, then the ``EventEnd`` exception will be raised,
        this will end all event actions.

        :param force: Whether to force end all further event actions.
        :raises EventEnd: When ``force`` is ``True``.
        :return:
        """
        self._end_current = True
        self._end_chain = True
        if force:
            raise EventEnd(self)


class EventBuilder:
    def __init__(
            self,
            listener: Listener | None = None,
            static: bool = False,
            copies_to_new: bool = False,
    ):
        """

        :param listener: The ``Listener`` that this ``EventBuilder`` creates ``Event``s for
        :param static: Whether this ``EventBuilder`` is only allowed to create one ``Event``
        :param copies_to_new: Whether the ``new_listener()`` method creates a new ``EventBuilder``
        """
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
        """The name that is used for each ``Event`` created."""
        return self._name

    @property
    def static(self):
        """
        Whether this ``EventBuilder`` is only allowed to create one ``Event``.

        If ``clear_event()`` is called, then this ``EventBuilder`` can create another ``Event``.
        """
        return self._static

    @property
    def copies_to_new(self):
        """Whether the ``new_listener()`` method creates a new ``EventBuilder`` or modifies this ``EventBuilder``."""
        return self._copies_to_new

    def build(self, args: tuple, kwargs: dict, returned: Any, called_method, *, caller: Listener | None = None) -> Event:
        """
        Builds an ``Event``.

        If this ``EventBuilder`` is ``static``,
        then this builder will only build one ``Event``.

        Use ``clear_event`` to clear the built ``Event``.

        :param args: The original arguments passed that were passed to the ``called_method``.
        :param kwargs: The original keyword arguments passed that were passed to the ``called_method``.
        :param returned: The value returned by ``called_method`` when passed ``args`` and ``kwargs``
        :param called_method: The method that triggered the ``Event``
        :param caller: The ``Listener`` that should be tied to the created ``Event``.
        :return:
        """
        if caller is None:
            caller = self.listener
        if not self._static or self._build is None:
            self._build = self.make_event(caller)
        self._build.pass_values(args, kwargs, returned, called_method)
        return self._build

    def make_event(self, caller: Listener) -> Event:
        """
        Creates an ``Event``.

        Unlike ``EventBuilder.build()``,
        This method doesn't store the created
        ``Event`` in this ``EventBuilder``.
        This means that this method will
        always return a new ``Event``.
        :param caller: The ``Listener`` that should be tied to the created ``Event``.
        :return: The created ``Event``.
        """
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
        """
        Creates a new ``EventBuilder`` with ``**kwargs``.

        If the value isn't defined in ``kwargs``,
        then the value is taken from this ``EventBuilder``.

        :param kwargs: The keyword arguments to pass to ``EventBuilder`` constructor.
        :return: The created ``EventBuilder``.
        """
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
