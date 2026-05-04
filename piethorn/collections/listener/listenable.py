"""Base classes for objects whose methods can trigger named listeners."""

from __future__ import annotations

from typing import Any, Callable

from piethorn.collections.listener.event import EventBuilder
from piethorn.collections.listener.listener import ListenerBuilder, caller_type, Listener
from piethorn.collections.listener.listens import listens, _double_wrap_prevent, ListensFor, system_listens


def _get_listens_for(value):
    """
    Return ``ListensFor`` metadata attached by the ``listens`` decorator.
    """
    return getattr(value, "__listens_for__", None)


def _has_func_listens(func) -> bool:
    """Return whether a callable has listener metadata."""
    return _get_listens_for(func) is not None

def _has_func_wrapper(func):
    """Return whether a callable has already been wrapped by ``listens``."""
    return getattr(func, "__listens_wrapped__", False)

def _find_inherited_member_with_listens(cls, name):
    """
    Return the nearest inherited member with listener metadata.

    This supports subclasses that override a listened method without repeating
    the ``@listens`` decorator.
    """

    for base in cls.__mro__[1:]:
        if name in base.__dict__:
            value = base.__dict__[name]

            if _member_has_listens(value):
                return value

    return None

def _member_has_listens(value):
    """
    Return whether a class member or descriptor has listener metadata.

    :param value: The class dictionary value to inspect.
    :return: Whether listener metadata is present.
    """
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

def _get_inherited_listens(inherited):
    """
    Collect listener metadata from an inherited member.

    :param inherited: The inherited class member or descriptor.
    :return: Combined ``ListensFor`` metadata, or ``None`` when unavailable.
    """
    if inherited is None:
        return None
    if isinstance(inherited, property):
        if _has_func_listens(inherited.fget):
            inherited_func = inherited.fget
        elif _has_func_listens(inherited.fset):
            inherited_func = inherited.fset
        elif _has_func_listens(inherited.fdel):
            inherited_func = inherited.fdel
        else:
            inherited_func = inherited
    elif isinstance(inherited, (staticmethod, classmethod)):
        inherited_func = inherited.__func__
    else:
        inherited_func = inherited
    listens_for = ListensFor(tuple())
    listens_for2 = _get_listens_for(inherited_func)
    if listens_for2 is not None:
        listens_for.merge(listens_for2)
    if inherited_func is not inherited:
        if _has_func_listens(inherited):
            listens_for2 = _get_listens_for(inherited)
            if listens_for2 is not None:
                listens_for.merge(listens_for2)

    if listens_for2 is None:
        return None
    return listens_for

def _copy_missing_listens(value, inherited):
    """
    Copy inherited listener metadata onto an overriding member.

    Properties, static methods, and class methods are rebuilt with their
    original descriptor type so the subclass keeps the same binding behavior.
    """
    if isinstance(value, property):
        infget = None
        infset = None
        infdel = None
        if isinstance(inherited, property):
            infget = _get_inherited_listens(inherited.fget)
            infset = _get_inherited_listens(inherited.fset)
            infdel = _get_inherited_listens(inherited.fdel)
        else:
            infget = _get_inherited_listens(inherited)
        if infget is None:
            infget = _get_listens_for(value)
        else:
            if _has_func_listens(value):
                infget.merge(_get_listens_for(value))
        fget = _copy_missing_accessor_listens(value.fget, infget)
        fset = _copy_missing_accessor_listens(value.fset, infset)
        fdel = _copy_missing_accessor_listens(value.fdel, infdel)

        if fget is value.fget and fset is value.fset and fdel is value.fdel:
            return value

        return type(value)(
            fget,
            fset,
            fdel,
            value.__doc__,
        )

    if isinstance(value, (staticmethod, classmethod)):
        func = value.__func__
        new_method = _copy_missing_accessor_listens(func, _get_inherited_listens(inherited))
        if new_method is not None:
            if _has_func_listens(value):
                new_method = _double_wrap_prevent(new_method, _get_listens_for(value))
            if new_method is not func:
                return type(value)(new_method)

    if not isinstance(value, (property, staticmethod, classmethod)):
        new_method = _copy_missing_accessor_listens(value, _get_inherited_listens(inherited))
        if new_method is not None:
            return new_method

    return value


def _copy_missing_accessor_listens(func, inherited_listens):
    """
    Apply inherited listener metadata to an accessor when needed.

    :param func: The accessor function to wrap.
    :param inherited_listens: Listener metadata inherited from a parent member.
    :return: The original function, a wrapped function, or ``None``.
    """
    if func is None:
        return None

    if inherited_listens is None:
        return func

    if _has_func_wrapper(func):
        return _double_wrap_prevent(func, inherited_listens)

    return listens(inherited_listens_for=inherited_listens)(func)


class Listenable:
    """Base class for instances that own and dispatch named listeners."""

    def __init_subclass__(cls, **kwargs):
        """Preserve ``@listens`` metadata when subclasses override listened members."""
        super().__init_subclass__(**kwargs)

        for name, value in list(cls.__dict__.items()):
            inherited = _find_inherited_member_with_listens(cls, name)

            if inherited is None:
                continue

            new_value = _copy_missing_listens(value, inherited)

            if new_value is not value:
                setattr(cls, name, new_value)

    def __init__(self, *named: str, listener_builder: ListenerBuilder | None = None, auto_create: bool = False):
        """
        Create a listenable object with the given listener names.

        :param named: The names of each event listener to be created.
        :param listener_builder: The ``ListenerBuilder`` that stores and creates ``Listener`` objects.
        :param auto_create: Whether to automatically create a ``Listener`` when one doesn't exist, but a ``caller_type`` is being added to it.
        """
        self.__listeners__: ListenerBuilder = listener_builder if listener_builder is not None else ListenerBuilder()
        self.__listeners__._listenable = self
        self._auto_create = auto_create

        for name in named:
            self.__listeners__.add(name)

    @property
    def auto_create(self) -> bool:
        """
        Whether ``add_listener`` creates missing listener entries on demand.
        """
        return self._auto_create

    @property
    def listener_count(self):
        """Number of listeners currently registered on this instance."""
        return  len(self.__listeners__)

    @system_listens("get_listener", straight_call_on_recurse_denied=True)
    def get_listener(self, name: int | str) -> Listener:
        """
        Return a registered listener by name or normalized integer event id.

        :param name: The name of the ``Listener`` to get.
        :return: The ``Listener`` with the provided name.
        """
        return self.__listeners__.get(name)

    def has_listener(self, name: int | str) -> bool:
        """
        Return whether this instance has a listener for ``name``.

        :param name: The name of the ``Listener`` to check.
        :return: Whether the listener exists.
        """
        return self.__listeners__.has(name)

    @system_listens("add_listener")
    def add_listener(self, name: int | str, caller: caller_type):
        """
        Register a callback on one of this object's listeners.

        :param name: The name of the ``Listener`` to add a caller to.
        :param caller: Function called with an ``Event`` when the listener fires.
        """
        if self.auto_create:
            self.__listeners__.add(name, replace=False).add(caller)
        else:
            self.get_listener(name).add(caller)

    @system_listens("remove_listener")
    def remove_listener(self, name: int | str, caller):
        """
        Remove a callback from one of this object's listeners.

        :param name: The name of the ``Listener`` to remove a caller from.
        :param caller: The function to remove.
        """
        self.get_listener(name).remove(caller)

    @system_listens("event_trigger")
    def event_trigger(self, name: int | str, args: tuple, kwargs: dict, returned: Any, called_method: Callable):
        """
        Dispatch a stored method-call context through a named listener.

        :param name: The name of the ``Listener`` to trigger.
        :param args: The original arguments passed that were passed to the ``called_method``.
        :param kwargs: The original keyword arguments passed that were passed to the ``called_method``.
        :param returned: The value returned by ``called_method`` when passed ``args`` and ``kwargs``
        :param called_method: The method that triggered the ``Event``
        """
        self.get_listener(name).use(args, kwargs, returned, called_method)


class ListenerHolder(Listenable):
    """Container-style wrapper around a ``ListenerBuilder`` registry."""

    def __init__(self, *named: str, listener_builder: ListenerBuilder | None = None, auto_create: bool = False):
        """
        Create a holder for manually managed listener entries.

        :param named: The names of each event listener to be created.
        :param listener_builder: The registry used to store listeners.
        :param auto_create: Whether missing listeners are created by ``add_listener``.
        """
        super().__init__(*named, listener_builder=listener_builder, auto_create=auto_create)

    def create(self, name: int | str, event_builder: EventBuilder | None = None, *, replace: bool = False):
        """
        Create or return a listener in this holder.

        Existing listeners are reused when ``replace`` is ``False``. Passing
        ``replace=True`` overwrites the existing listener.

        :param name: The name of the listener. If name is an integer, then the name is set as ``event_`` followed by that integer.
        :param event_builder: The ``EventBuilder`` object that will be used to create ``Event`` objects for the listener.
        :param replace: Whether to replace the existing listener if one exists.
        :return: The new ``Listener`` object.
        """
        return self.__listeners__.add(name, event_builder, replace=replace)

    def remove(self, name: int | str, default=None):
        """
        Remove and return a listener from this holder.

        :param name: The name of the listener. If name is an integer, then ``event_{name}`` is checked.
        :param default: The default value to return if the listener does not exist.
        :return: The removed listener, or ``default`` when the name is missing.
        """
        return self.__listeners__.remove(name, default)

    def __getitem__(self, item: int | str):
        """
        Get a listener by name or event index.

        :param item: The listener name or event index.
        :return: The requested ``Listener``.
        """
        return self.__listeners__.get(item)

    def __len__(self):
        """Return the number of listeners in this holder."""
        return len(self.__listeners__)

    def __iter__(self):
        """Iterate over listeners in this holder."""
        return iter(self.__listeners__)


GLOBAL_LISTENERS = ListenerHolder(auto_create=True)
