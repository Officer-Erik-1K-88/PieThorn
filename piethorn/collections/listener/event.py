"""Event state objects passed to listener callbacks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from piethorn.collections.listener import Listener


class EventEnd(Exception):
    """Raised when an event is force-ended during listener dispatch."""

    def __init__(self, event: Event):
        """
        Create an exception for the event that requested termination.

        :param event: The ``Event`` that ended its listener chain.
        """
        super().__init__(f"Event {event.name} ended")
        self.event = event


class Event:
    """
    Runtime context passed to a listener callback.

    An event stores the arguments, return value, and originating method for the
    method call that triggered a listener. It also exposes stop flags that let a
    callback stop the current listener, the remaining listener chain, or both.

    Events built by a static ``EventBuilder`` are reused across the full caller
    chain. Events from a non-static builder are recreated between callers.
    """
    def __init__(
            self,
            builder: EventBuilder,
            caller: Listener,
    ):
        """
        Create an event for a listener callback.

        :param builder: The ``EventBuilder`` that created this event.
        :param caller: The ``Listener`` that triggered this event.
        """
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
        """Event name derived from the listener that owns the event builder."""
        return self._builder.name

    @property
    def caller(self):
        """The ``Listener`` currently dispatching this event."""
        return self._caller

    @property
    def listener(self):
        """The ``Listener`` associated with this event's builder."""
        return self._builder.listener

    @property
    def end_chain(self):
        """Whether dispatch should stop before the next listener callback."""
        return self._end_chain

    @property
    def end_current(self):
        """Whether the current ``caller_type`` should end before dispatch continues."""
        return self._end_current

    @property
    def active(self):
        """Whether this event is currently being handled by a caller."""
        return self._in_use

    @property
    def args(self):
        """Positional arguments passed to the method that triggered the event."""
        return self._args

    @property
    def kwargs(self):
        """Keyword arguments passed to the method that triggered the event."""
        return self._kwargs

    @property
    def returned(self):
        """Return value from the method that triggered the event."""
        return self._returned

    @property
    def called_method(self):
        """
        Method that triggered this event.

        This can be dangerous to use, especially for
        setters, adders, deleters, and other
        mutating methods, calling
        ``Event.called_method(*Event.args, **Event.kwargs)`` would essentially
        run the same operation a second time.
        """
        return self._called_method

    def pass_values(self, args: tuple = (), kwargs: dict | None = None, returned=None, called_method=None):
        """
        Store call context on the event before it is dispatched.

        Values are ignored while the event is active to avoid mutating an event
        that is already being handled.

        :param args: Positional arguments passed to the triggering method.
        :param kwargs: Keyword arguments passed to the triggering method.
        :param returned: Value returned by the triggering method.
        :param called_method: Method that triggered the event.
        """
        if not self.active:
            self._args = args
            self._kwargs = kwargs if kwargs is not None else {}
            self._returned = returned
            self._called_method = called_method

    def stop_current(self, force: bool = True):
        """
        End this event for the current listener chain item.

        Without forcing, this only sets ``end_current``. With ``force=True``,
        ``EventEnd`` is raised and all remaining event actions for the current
        ``caller_type`` are ended immediately.

        :param force: Whether to force end all further event actions. Defaults to ``True``.
        :raises EventEnd: When ``force`` is ``True``.
        """
        self._end_current = True
        if force:
            raise EventEnd(self)

    def stop_chain(self, force: bool = False):
        """
        End this event for the caller chain of the ``Listener``.

        Without forcing, the event actions of the current ``caller_type`` will finish
        before the listener caller chain ends. With ``force=True``,
        ``EventEnd`` is raised immediately.

        :param force: Whether to force end all further event actions. Defaults to ``False``.
        :raises EventEnd: When ``force`` is ``True``.
        """
        self._end_chain = True
        if force:
            raise EventEnd(self)

    def end(self, force: bool = False):
        """
        End this event for both the current item and the caller chain.

        This sets both ``end_current`` and ``end_chain``. With ``force=True``,
        ``EventEnd`` is raised and all remaining event actions are ended
        immediately.

        :param force: Whether to force end all further event actions.
        :raises EventEnd: When ``force`` is ``True``.
        """
        self._end_current = True
        self._end_chain = True
        if force:
            raise EventEnd(self)


class EventBuilder:
    """Creates ``Event`` objects for a listener."""

    def __init__(
            self,
            listener: Listener | None = None,
            static: bool = False,
            copies_to_new: bool = False,
    ):
        """
        Create a builder that controls event reuse for a listener.

        :param listener: The ``Listener`` that this ``EventBuilder`` creates ``Event`` objects for.
        :param static: Whether to reuse one event until ``clear_event`` is called.
        :param copies_to_new: Whether ``new_listener()`` returns a copied builder.
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
        """Listener that receives events created by this builder."""
        return self._listener

    @property
    def name(self):
        """Display-style event name derived from the assigned listener name."""
        return self._name

    @property
    def static(self):
        """
        Whether this builder can only build one event until ``clear_event`` is called.

        A static builder returns its existing event while one is cached.
        Clearing the event allows the builder to create another event.
        """
        return self._static

    @property
    def copies_to_new(self):
        """Whether ``new_listener()`` copies this builder instead of mutating it."""
        return self._copies_to_new

    def build(self, args: tuple, kwargs: dict, returned: Any, called_method, *, caller: Listener | None = None) -> Event:
        """
        Return an event populated with the triggering call context.

        If this builder is static, it returns the existing built event until
        ``clear_event`` is called. Otherwise, it creates a new event on each
        build call.

        :param args: The original arguments passed that were passed to the ``called_method``.
        :param kwargs: The original keyword arguments passed that were passed to the ``called_method``.
        :param returned: The value returned by ``called_method`` when passed ``args`` and ``kwargs``
        :param called_method: The method that triggered the ``Event``
        :param caller: The ``Listener`` that should be tied to the created ``Event``.
        :return: A populated ``Event`` for listener callbacks.
        """
        if caller is None:
            caller = self.listener
        if not self._static or self._build is None:
            self._build = self.make_event(caller)
        self._build.pass_values(args, kwargs, returned, called_method)
        return self._build

    def make_event(self, caller: Listener) -> Event:
        """
        Create a fresh event without storing it on this builder.

        :param caller: The ``Listener`` that should be tied to the created ``Event``.
        :return: The created ``Event``.
        """
        return Event(self, caller)

    def clear_event(self, destabilize_event: bool = False) -> Event | None:
        """
        Remove the cached event from this builder.

        ``Listener.use`` calls this when dispatch ends. Active events cannot be
        cleared because callbacks may still depend on their context.

        :param destabilize_event: Whether to make the cleared ``Event`` unusable.
        :return: The removed ``Event``.
        """
        event = self._build
        if event is not None:
            if event.active:
                # TODO: Make it so that we can terminate event life cycle without the need of throwing an error.
                raise RuntimeError("Cannot clear an active event. This may change in the future.")
            if destabilize_event:
                event._builder = None
        self._build = None
        return event

    def copy(self, **kwargs) -> EventBuilder:
        """
        Create a builder with this builder's settings as defaults.

        Supported keyword overrides are ``listener``, ``static``, and
        ``copies_to_new``.

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
        """
        Assign the listener used by events from this builder.

        :param listener: The ``Listener`` this builder should create events for.
        """
        self._listener = listener
        name = listener.name if listener.name.lower().startswith("event_") else f"event_{listener.name}"
        self._name = name.replace("_", " ").title().replace(" ", "")
        self._build = None

    def new_listener(self, listener: Listener) -> EventBuilder:
        """
        Return a builder assigned to ``listener``.

        If ``copies_to_new`` is true, this returns a copy of the builder with
        the new listener. Otherwise, it updates this builder in place.

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
