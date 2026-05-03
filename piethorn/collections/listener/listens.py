from __future__ import annotations

from functools import wraps

from piethorn.collections.listener.listener import _listener_name


class ListensFor:
    def __init__(self, names: tuple[int | str, ...], allow_recurse: bool = True, throw_on_recurse_denied: bool = True):
        self._names = names
        self._allow_recurse: bool = allow_recurse
        self._throw_on_recurse_denied: bool = throw_on_recurse_denied
        self._in_use = False
        self._is_default = False

    @property
    def names(self):
        return self._names
    @names.setter
    def names(self, names: tuple[int | str, ...]):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._names = names

    @property
    def allow_recurse(self):
        return self._allow_recurse
    @allow_recurse.setter
    def allow_recurse(self, allow_recurse: bool):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._allow_recurse = allow_recurse

    @property
    def throw_on_recurse_denied(self):
        return self._throw_on_recurse_denied
    @throw_on_recurse_denied.setter
    def throw_on_recurse_denied(self, allow_recurse: bool):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._throw_on_recurse_denied = allow_recurse

    @property
    def active(self):
        return self._in_use

    def merge(self, listens_for: ListensFor):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self.names = tuple(dict.fromkeys((*listens_for.names, *self.names)))
        if not listens_for._is_default:
            self.allow_recurse = (self.allow_recurse or listens_for.allow_recurse)
            self.throw_on_recurse_denied = (self.throw_on_recurse_denied or listens_for.throw_on_recurse_denied)

DEFAULT_LISTENS_FOR = ListensFor(tuple())
DEFAULT_LISTENS_FOR._is_default = True

def _double_wrap_prevent(func, listens_for: ListensFor):
    if hasattr(func, "__listens_for__"):
        func.__listens_for__.merge(listens_for)
    else:
        func.__listens_for__ = listens_for
    return func

def listens(
        *listens_for_names: int | str,
        allow_recurse: bool=DEFAULT_LISTENS_FOR.allow_recurse,
        throw_on_recurse_denied: bool=DEFAULT_LISTENS_FOR.throw_on_recurse_denied,
        inherited_listens_for: ListensFor = DEFAULT_LISTENS_FOR
):
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

    Class methods and static methods trigger global listeners
    unless manually passed a Listenable instance as their first argument.

    When combined with descriptors such as ``property``,
    ``listens`` should be placed closest to the function
    so it wraps the raw function before ``property`` receives it.
    For example:
    ```
    @property
    @listens("get")
    ```

    There is recursion protection. This is to prevent triggering the listener events while
    still in the process of running said events. Because of this, there are two settings:

    ``allow_recurse``: This is used to prevent the wrapped function from firing.

    ``throw_on_recurse_denied``: This is used to signal if a ``RecursionError``
    should be fired when caught in event running when the function is called
    and that ``allow_recurse`` is ``False``.

    :param listens_for_names: The names of each listener that will be triggered on use of the decorated method.
    :param allow_recurse: Whether to allow for recursion.
    :param throw_on_recurse_denied: Whether to raise a ``RecursionError`` when ``allow_recurse`` is ``False`` and is in recursion.
    :param inherited_listens_for: The ``ListensFor`` instance to inherit information from.
    :return:
    """
    if len(listens_for_names) == 0:
        raise TypeError("There must be at least one listener to listen for.")
    listens_for = ListensFor(
        names=tuple(_listener_name(name) for name in listens_for_names),
        allow_recurse=allow_recurse,
        throw_on_recurse_denied=throw_on_recurse_denied,
    )
    listens_for.merge(inherited_listens_for)
    def decorator(func):
        # Prevent double-wrapping.
        if getattr(func, "__listens_wrapped__", False):
            return _double_wrap_prevent(func, listens_for)

        @wraps(func)
        def wrapper(*args, **kwargs):
            from piethorn.collections.listener.listenable import Listenable, GLOBAL_LISTENERS
            lf = getattr(wrapper, "__listens_for__", listens_for)
            if lf.active and not lf.allow_recurse:
                if lf.throw_on_recurse_denied:
                    raise RecursionError("Recursion not allowed on method '%s'." % func.__name__)
                return None
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

            if not lf.active:
                lf._in_use = True
                try:
                    for name in lf.names:
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
                finally:
                    lf._in_use = False

            return return_value

        wrapper.__listens_for__ = listens_for
        wrapper.__listens_wrapped__ = True
        return wrapper

    return decorator