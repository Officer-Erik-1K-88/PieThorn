from __future__ import annotations

import re
from abc import abstractmethod, ABC
from functools import wraps
from typing import Callable, Iterable, Any, Sequence, MutableSequence, TypeAlias

from piethorn.collections.mapping import Map


def _listener_name(name: int | str) -> str:
    if isinstance(name, int):
        return f"event_{name}"
    return name

class GetListenerError(Exception):
    pass

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

        This can be dangerous to use, expectantly
        when it is a setter, adder, or deleter as
        if ``Event.called_method(*Event.args, **Event.kwargs)``
        is called, then it would essentially be calling the same
        function a second time.
        """
        return self._called_method

    def pass_values(self, args: tuple=(), kwargs: dict | None=None, returned=None, called_method=None):
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
    def __init__(
            self,
            listener: Listener | None = None,
            static: bool = False,
            copies_to_new: bool = False,
    ):
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

    def build(self, args: tuple, kwargs: dict, returned: Any, called_method, *, caller: Listener|None=None) -> Event:
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

    def clear_event(self, destabilize_event: bool=False) -> Event | None:
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
                # TODO: Make it so that we can terminate event life cycle.
                pass
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

    def add(self, name: int | str, event_builder: EventBuilder | None=None):
        listener = self.build(name, event_builder)
        listener._builder = self
        self.__listeners__[listener.name] = listener

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


def listens(*listens_for: int | str):
    """
    Defines the listeners that listen for the
    method that this decorates.

    At least one listener name is expected.

    This decorator should only be used on methods of
    classes that extend ``Listenable``.
    If the decorated callable is not called on a ``Listenable`` instance, the
    event is sent to ``GLOBAL_LISTENERS`` instead.

    When the decorator is passed to some method on ``Listenable``,
    then the ``self`` argument will not be passed to ``Event.args``
    (in this case, we then wrap the ``Event.called_method`` in a way that allows it to
    be called as if it was ``self.some_function()``).
    However, when it's not on some ``Listenable`` instance,
    then the ``self`` argument is passed to ``Event.args``.

    This decorator can be used with other decorators like ``property``,
    all that is needed to be done is that this decorator must be the first
    in the list. For example:
    ```
    @property
    @listens("get")
    ```

    :param listens_for: The names of each listener that will be triggered on use of the decorated method.
    :return:
    """
    if len(listens_for) == 0:
        raise TypeError("There must be at least one listener to listen for.")
    listens_for = tuple(_listener_name(name) for name in listens_for)
    def decorator(func):
        # Prevent double-wrapping.
        if getattr(func, "__listens_wrapped__", False):
            existing = getattr(func, "__listens_for__", ())
            func.__listens_for__ = tuple(dict.fromkeys((*existing, *listens_for)))
            return func

        @wraps(func)
        def wrapper(*args, **kwargs):
            instance_or_cls = args[0] if args else None
            first_arg_normal = True
            if isinstance(instance_or_cls, Listenable):
                listenable = instance_or_cls
                first_arg_normal = False
            else:
                listenable = GLOBAL_LISTENERS

            if first_arg_normal:
                real_args = args
                called_method = func
            else:
                called_method = lambda *a1, **kw1: func(instance_or_cls, *a1, **kw1)
                real_args = args[1:]

            return_value = called_method(*real_args, **kwargs)

            for name in getattr(wrapper, "__listens_for__", listens_for):
                if listenable.has_listener(name):
                    listenable.event_trigger(
                        name,
                        real_args,
                        kwargs,
                        return_value,
                        called_method
                    )
                elif listenable is not GLOBAL_LISTENERS and GLOBAL_LISTENERS.has_listener(name):
                    GLOBAL_LISTENERS.event_trigger(
                        name,
                        real_args,
                        kwargs,
                        return_value,
                        called_method
                    )

            return return_value

        wrapper.__listens_for__ = tuple(listens_for)
        wrapper.__listens_wrapped__ = True
        return wrapper

    return decorator

def _get_listens_for(value):
    """
    Gets listener metadata.
    """
    return getattr(value, "__listens_for__", None)


def _has_func_listens(func) -> bool:
    return _get_listens_for(func) is not None


def _find_inherited_member_with_listens(cls, name):
    """
    Searches parent classes for a method/property with listener metadata.
    """

    for base in cls.__mro__[1:]:
        if name in base.__dict__:
            value = base.__dict__[name]

            if _member_has_listens(value):
                return value

    return None

def _member_has_listens(value):
    if isinstance(value, property):
        return (
            _has_func_listens(value.fget)
            or _has_func_listens(value.fset)
            or _has_func_listens(value.fdel)
        )

    if isinstance(value, staticmethod):
        return _has_func_listens(value.__func__)

    if isinstance(value, classmethod):
        return _has_func_listens(value.__func__)

    return _has_func_listens(value)


def _copy_missing_listens(value, inherited):
    """
    Applies @listens(...) while preserving descriptor type.
    """
    if isinstance(value, property) and isinstance(inherited, property):
        fget = _copy_missing_accessor_listens(value.fget, inherited.fget)
        fset = _copy_missing_accessor_listens(value.fset, inherited.fset)
        fdel = _copy_missing_accessor_listens(value.fdel, inherited.fdel)

        if fget is value.fget and fset is value.fset and fdel is value.fdel:
            return value

        return property(
            fget,
            fset,
            fdel,
            value.__doc__,
        )

    if isinstance(value, (staticmethod, classmethod)) and isinstance(inherited, (staticmethod, classmethod)):
        func = value.__func__
        inherited_func = inherited.__func__

        inherited_listens = _get_listens_for(inherited_func)

        if inherited_listens is not None and not _has_func_listens(func):
            new_method =listens(*inherited_listens)(func)
            if isinstance(value, staticmethod):
                return staticmethod(new_method)
            elif isinstance(value, classmethod):
                return classmethod(new_method)

    if not isinstance(value, (property, staticmethod, classmethod)):
        inherited_listens = _get_listens_for(inherited)

        if inherited_listens is not None and not _has_func_listens(value):
            return listens(*inherited_listens)(value)

    return value


def _copy_missing_accessor_listens(func, inherited_func):
    if func is None:
        return None

    inherited_listens = _get_listens_for(inherited_func)

    if inherited_listens is None:
        return func

    if _has_func_listens(func):
        return func

    return listens(*inherited_listens)(func)


class Listenable:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        for name, value in list(cls.__dict__.items()):
            inherited = _find_inherited_member_with_listens(cls, name)

            if inherited is None:
                continue

            new_value = _copy_missing_listens(value, inherited)

            if new_value is not value:
                setattr(cls, name, new_value)

    def __init__(self, *named: str, listener_builder: ListenerBuilder | None = None):
        """

        :param event_count: The number of unnamed events.
        :param named: The names of each event listener to be created.
        """
        self.__listeners__: ListenerBuilder = listener_builder if listener_builder is not None else ListenerBuilder()
        self.__listeners__._listenable = self

        for name in named:
            self.__listeners__.add(name)

    @property
    def listener_count(self):
        return  len(self.__listeners__)

    def get_listener(self, name: int | str) -> Listener:
        """
        Gets a ``Listener`` for use.

        :param name: The name of the ``Listener`` to get. May also be the index of the ``Listener``.
        :return: The ``Listener`` with the provided name.
        """
        return self.__listeners__.get(name)

    def has_listener(self, name: int | str) -> bool:
        return self.__listeners__.has(name)

    def add_listener(self, name: int | str, caller: caller_type):
        """
        Adds a function to a ``Listener``.

        :param name: The name of the ``Listener`` to add a caller to.
        :param caller: The function to call when it's ``listener``'s use method is called.
        """
        self.get_listener(name).add(caller)

    def remove_listener(self, name: int | str, caller):
        """
        Removes a function from a ``Listener``.

        :param name: The name of the ``Listener`` to remove a caller from.
        :param caller: The function to remove.
        :return:
        """
        self.get_listener(name).remove(caller)

    def event_trigger(self, name: int | str, args: tuple, kwargs: dict, returned: Any, called_method: Callable):
        self.get_listener(name).use(args, kwargs, returned, called_method)


class ListenerHolder(Listenable):
    def __init__(self, *named: str, listener_builder: ListenerBuilder | None = None):
        """

        :param event_count: The number of unnamed events.
        :param named: The names of each event listener to be created.
        """
        super().__init__(*named, listener_builder=listener_builder)

    def create(self, name: int | str, event_builder: EventBuilder | None = None):
        self.__listeners__.add(name, event_builder)

    def remove(self, name: int | str, default=None):
        return self.__listeners__.remove(name, default)

    def __getitem__(self, item: int | str):
        return self.__listeners__.get(item)

    def __len__(self):
        return len(self.__listeners__)

    def __iter__(self):
        return iter(self.__listeners__)


GLOBAL_LISTENERS = ListenerHolder()


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