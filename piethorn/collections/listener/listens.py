from __future__ import annotations

from functools import wraps
from typing import TypeAlias

from piethorn.collections.listener.listener import _listener_name

boolean_type: TypeAlias = 'bool | SetBool'

class SetBool:
    def __init__(
            self,
            value: boolean_type,
            default: bool|None=None,
            and_change: bool=True,
            start_set: bool=False,
            allow_unset_change: bool=False,
    ):
        if isinstance(value, bool):
            self._value = value
            self._default = default
            self._set = start_set
        else:
            self._value = value.value
            self._default = value.default if default is None else default
            self._set = value.set or start_set
        self._and_change = and_change
        self._allow_unset_change = allow_unset_change
        if self._default is None:
            raise RuntimeError("SetBool must have a default value.")

    @property
    def value(self) -> bool:
        return self._value
    @value.setter
    def value(self, value: bool):
        self._value = value
        self._set = True

    @property
    def set(self) -> bool:
        return self._set

    @property
    def default(self) -> bool:
        # noinspection PyTypeChecker
        return self._default

    @property
    def and_change(self):
        return self._and_change

    @property
    def allow_unset_change(self):
        return self._allow_unset_change

    def reset(self):
        self._set = False
        self._value = self._default

    def change(self, new_value: SetBool):
        if self.allow_unset_change or new_value.set:
            if self.set:
                if self._and_change:
                    self.value = self.value and new_value.value
                else:
                    self.value = self.value or new_value.value
            else:
                self.value = new_value.value

    def __bool__(self):
        return self._value

    def __int__(self):
        return 1 if self._value else 0

    def __float__(self):
        return float(int(self))

    def __str__(self):
        return str(self._value)

    def __eq__(self, other):
        return self._value == other
    def __ne__(self, other):
        return self._value != other
    def __gt__(self, other):
        return self._value > other
    def __lt__(self, other):
        return self._value < other
    def __ge__(self, other):
        return self._value >= other
    def __le__(self, other):
        return self._value <= other


class ListensFor:
    def __init__(
            self,
            names: tuple[int | str, ...],
            allow_recurse: boolean_type = True,
            throw_on_recurse_denied: boolean_type = True,
            straight_call_on_recurse_denied: boolean_type = False,
            in_use_on_instance: boolean_type = True,
    ):
        self._names: tuple[int | str, ...] = names
        self._allow_recurse = SetBool(allow_recurse, True, start_set=not allow_recurse)
        self._throw_on_recurse_denied = SetBool(throw_on_recurse_denied, True, start_set=not throw_on_recurse_denied)
        self._straight_call_on_recurse_denied = SetBool(straight_call_on_recurse_denied, False, start_set=bool(straight_call_on_recurse_denied))
        self._in_use_on_instance = SetBool(in_use_on_instance, True, start_set=not in_use_on_instance)
        self._in_use = False
        self._instance_in_uses: dict[str, bool] = {}
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
        return self._allow_recurse.value
    @allow_recurse.setter
    def allow_recurse(self, allow_recurse: bool):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._allow_recurse.value = allow_recurse

    @property
    def throw_on_recurse_denied(self):
        return self._throw_on_recurse_denied.value
    @throw_on_recurse_denied.setter
    def throw_on_recurse_denied(self, allow_recurse: bool):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._throw_on_recurse_denied.value = allow_recurse

    @property
    def straight_call_on_recurse_denied(self):
        return self._straight_call_on_recurse_denied.value
    @straight_call_on_recurse_denied.setter
    def straight_call_on_recurse_denied(self, straight_call_on_recurse_denied: bool):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._straight_call_on_recurse_denied.value = straight_call_on_recurse_denied
    
    @property
    def in_use_on_instance(self):
        return self._in_use_on_instance.value
    @in_use_on_instance.setter
    def in_use_on_instance(self, in_use_on_instance: bool):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._in_use_on_instance.value = in_use_on_instance

    @property
    def active(self):
        return self._in_use
    @active.setter
    def active(self, active: bool):
        self._in_use = active

    @property
    def instance_in_uses(self):
        return self._instance_in_uses

    def merge(self, listens_for: ListensFor):
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self.names = tuple(dict.fromkeys((*self.names, *listens_for.names)))
        if not listens_for._is_default:
            self._allow_recurse.change(listens_for._allow_recurse)
            self._throw_on_recurse_denied.change(listens_for._throw_on_recurse_denied)
            self._straight_call_on_recurse_denied.change(listens_for._straight_call_on_recurse_denied)
            self._in_use_on_instance.change(listens_for._in_use_on_instance)


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
        straight_call_on_recurse_denied: bool=DEFAULT_LISTENS_FOR.straight_call_on_recurse_denied,
        in_use_on_instance: bool=DEFAULT_LISTENS_FOR.in_use_on_instance,
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
    still in the process of running said events. Because of this, there are three settings:

    ``allow_recurse``: This is used to prevent the wrapped function from firing.

    ``throw_on_recurse_denied``: This is used to signal if a ``RecursionError``
    should be fired when caught in event running when the function is called
    and that ``allow_recurse`` is ``False``. If ``throw_on_recurse_denied``
    is ``False``, then the value returned by the wrapped function will be ``None``.

    ``straight_call_on_recurse_denied``: This is the alternative to when ``None`` is
    returned. This should give the same functionality for when ``allow_recurse`` is
    ``True``, but having this as ``True`` and ``allow_recurse`` as ``False`` is
    faster than having ``allow_recurse`` as ``True``.

    :param listens_for_names: The names of each listener that will be triggered on use of the decorated method.
    :param allow_recurse: Whether to allow for recursion.
    :param throw_on_recurse_denied: Whether to raise a ``RecursionError`` when ``allow_recurse`` is ``False`` and is in recursion.
    :param straight_call_on_recurse_denied: Whether to call the wrapped function instead of returning ``None`` on recurse denied.
    :param in_use_on_instance: Whether to store in use data on the instance. It is recommended that this is ``False`` for when on static methods. Defaults to ``True``.
    :param inherited_listens_for: The ``ListensFor`` instance to inherit information from.
    :return:
    """
    listens_for = ListensFor(
        names=tuple(_listener_name(name) for name in listens_for_names),
        allow_recurse=allow_recurse,
        throw_on_recurse_denied=throw_on_recurse_denied,
        straight_call_on_recurse_denied=straight_call_on_recurse_denied,
        in_use_on_instance=in_use_on_instance,
    )
    listens_for.merge(inherited_listens_for)
    if len(listens_for.names) == 0:
        raise TypeError("There must be at least one listener to listen for.")
    def decorator(func):
        # Prevent double-wrapping.
        if getattr(func, "__listens_wrapped__", False):
            return _double_wrap_prevent(func, listens_for)

        @wraps(func)
        def wrapper(*args, **kwargs):
            from piethorn.collections.listener.listenable import Listenable, GLOBAL_LISTENERS
            lf = getattr(wrapper, "__listens_for__", listens_for)
            instance_or_cls = args[0] if args else None

            active_store_place = f"{func.__name__}_{id(wrapper)}"
            if lf.in_use_on_instance:
                active = lf.instance_in_uses.get(active_store_place, False)
            else:
                active = lf.active
            if active and not lf.allow_recurse:
                if lf.throw_on_recurse_denied:
                    raise RecursionError("Recursion not allowed on method '%s'." % func.__name__)
                return func(*args, **kwargs) if lf.straight_call_on_recurse_denied else None

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

            if not active:
                lf.active = True
                if lf.in_use_on_instance:
                    lf.instance_in_uses[active_store_place] = True
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
                    lf.active = False
                    if lf.in_use_on_instance:
                        lf.instance_in_uses[active_store_place] = False
            return return_value

        wrapper.__listens_for__ = listens_for
        wrapper.__listens_wrapped__ = True
        return wrapper

    return decorator

def system_listens(
        *names: int | str,
        throw_on_recurse_denied: bool=False,
        straight_call_on_recurse_denied: bool=False,
):
    """
    This decorator should be used for when listening to
    methods in the listener system. For example: ``Listenable.get_listeners()``.
    :param names: The names of each listener that will be triggered on use of the decorated method.
    :param throw_on_recurse_denied: Whether to raise a ``RecursionError`` when ``allow_recurse`` is ``False`` and is in recursion.
    :param straight_call_on_recurse_denied: Whether to call the wrapped function instead of returning ``None`` on recurse denied.
    :return:
    """
    return listens(
        *names,
        allow_recurse=False,
        throw_on_recurse_denied=throw_on_recurse_denied,
        straight_call_on_recurse_denied=straight_call_on_recurse_denied
    )