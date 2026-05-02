from __future__ import annotations

from typing import Any, Callable

from piethorn.collections.listener.event import EventBuilder
from piethorn.collections.listener.listener import ListenerBuilder, caller_type, Listener
from piethorn.collections.listener.listens import listens


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

    def create(self, name: int | str, event_builder: EventBuilder | None = None, *, replace: bool = False):
        return self.__listeners__.add(name, event_builder, replace=replace)

    def remove(self, name: int | str, default=None):
        return self.__listeners__.remove(name, default)

    def __getitem__(self, item: int | str):
        return self.__listeners__.get(item)

    def __len__(self):
        return len(self.__listeners__)

    def __iter__(self):
        return iter(self.__listeners__)


GLOBAL_LISTENERS = ListenerHolder()