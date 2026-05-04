"""Decorators that turn method calls into listener events."""

from __future__ import annotations

from functools import wraps

from piethorn.collections.listener.listener import _listener_name
from piethorn.typing.flag import boolean_type, SetBool


class ListensFor:
    """Listener metadata attached to functions wrapped by ``listens``."""

    def __init__(
            self,
            names: tuple[int | str, ...],
            allow_recurse: boolean_type = True,
            throw_on_recurse_denied: boolean_type = True,
            straight_call_on_recurse_denied: boolean_type = False,
            in_use_on_instance: boolean_type = True,
    ):
        """
        Create listener metadata.

        :param names: Listener names to trigger.
        :param allow_recurse: Whether listener events may recurse while already active.
        :param throw_on_recurse_denied: Whether to raise when recursion is denied.
        :param straight_call_on_recurse_denied: Whether to call the function directly when recursion is denied.
        :param in_use_on_instance: Whether active state is tracked per instance.
        """
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
        """Listener names triggered by the decorated callable."""
        return self._names
    @names.setter
    def names(self, names: tuple[int | str, ...]):
        """Set the listener names triggered by the decorated callable."""
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._names = names

    @property
    def allow_recurse(self):
        """Whether listener events may recurse while this metadata is active."""
        return self._allow_recurse.value
    @allow_recurse.setter
    def allow_recurse(self, allow_recurse: bool):
        """Set whether listener events may recurse while this metadata is active."""
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._allow_recurse.value = allow_recurse

    @property
    def throw_on_recurse_denied(self):
        """Whether denied recursion raises ``RecursionError``."""
        return self._throw_on_recurse_denied.value
    @throw_on_recurse_denied.setter
    def throw_on_recurse_denied(self, allow_recurse: bool):
        """Set whether denied recursion raises ``RecursionError``."""
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._throw_on_recurse_denied.value = allow_recurse

    @property
    def straight_call_on_recurse_denied(self):
        """Whether denied recursion calls the wrapped function directly."""
        return self._straight_call_on_recurse_denied.value
    @straight_call_on_recurse_denied.setter
    def straight_call_on_recurse_denied(self, straight_call_on_recurse_denied: bool):
        """Set whether denied recursion calls the wrapped function directly."""
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._straight_call_on_recurse_denied.value = straight_call_on_recurse_denied
    
    @property
    def in_use_on_instance(self):
        """Whether active-state tracking is separated by instance."""
        return self._in_use_on_instance.value
    @in_use_on_instance.setter
    def in_use_on_instance(self, in_use_on_instance: bool):
        """Set whether active-state tracking is separated by instance."""
        if self._is_default:
            raise RuntimeError("Cannot modify a default ListensFor.")
        self._in_use_on_instance.value = in_use_on_instance

    @property
    def active(self):
        """Whether this metadata is currently being used to trigger listeners."""
        return self._in_use
    @active.setter
    def active(self, active: bool):
        """Set whether this metadata is currently being used to trigger listeners."""
        self._in_use = active

    @property
    def instance_in_uses(self):
        """Per-callable active-state flags keyed by generated storage names."""
        return self._instance_in_uses

    def merge(self, listens_for: ListensFor):
        """
        Merge another ``ListensFor`` object into this one.

        Listener names are appended without duplicates. Recursion options are
        only copied from non-default metadata, which lets inherited decorators
        keep explicit settings while ignoring default placeholders.

        :param listens_for: Listener metadata to merge into this object.
        """
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
    """
    Add listener metadata to a callable without wrapping it a second time.

    :param func: The callable to annotate.
    :param listens_for: Listener metadata to attach or merge.
    :return: The original callable.
    """
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
    Decorate a callable so calling it can trigger named listeners.

    At least one listener name is required. When the first argument is a
    ``Listenable`` instance, the event is sent to that instance's listeners.
    Otherwise, the event is sent to ``GLOBAL_LISTENERS``. If a ``Listenable``
    instance does not have the named listener, a matching global listener is
    used when one exists.

    For instance methods on ``Listenable``, ``self`` is excluded from
    ``Event.args`` and ``Event.called_method`` is rebound so callbacks can call
    it as if it were the original bound method. For non-``Listenable`` calls,
    all positional arguments are preserved in ``Event.args``.

    When combined with descriptors such as ``property``,
    ``listens`` should be placed closest to the function
    so it wraps the raw function before ``property`` receives it.
    For example:
    ```
    @property
    @listens("get")
    ```

    Recursion protection prevents listener events from being triggered while
    those same events are already running. ``allow_recurse`` controls whether
    that recursive listener triggering is allowed. When recursion is denied,
    the wrapper either raises ``RecursionError``, returns ``None``, or calls the
    wrapped function directly depending on the recursion options.

    :param listens_for_names: The names of each listener that will be triggered on use of the decorated method.
    :param allow_recurse: Whether to allow for recursion.
    :param throw_on_recurse_denied: Whether to raise a ``RecursionError`` when ``allow_recurse`` is ``False`` and is in recursion.
    :param straight_call_on_recurse_denied: Whether to call the wrapped function instead of returning ``None`` on recurse denied.
    :param in_use_on_instance: Whether to store in use data on the instance. It is recommended that this is ``False`` for when on static methods. Defaults to ``True``.
    :param inherited_listens_for: The ``ListensFor`` instance to inherit information from.
    :return: A decorator that wraps the target callable.
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
        """
        Wrap a callable so it triggers its configured listeners.

        :param func: The callable to decorate.
        :return: The wrapped callable.
        """
        # Prevent double-wrapping.
        if getattr(func, "__listens_wrapped__", False):
            return _double_wrap_prevent(func, listens_for)

        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Call the decorated callable and trigger configured listeners.

            :param args: Positional arguments for the decorated callable.
            :param kwargs: Keyword arguments for the decorated callable.
            :return: The decorated callable's return value.
            """
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
    Decorate internal listener-system methods without recursive event dispatch.

    This is used for methods such as ``Listenable.get_listener`` that should
    still emit events but must not recursively trigger themselves while the
    listener system is already handling one of those events.

    :param names: The names of each listener that will be triggered on use of the decorated method.
    :param throw_on_recurse_denied: Whether to raise a ``RecursionError`` when ``allow_recurse`` is ``False`` and is in recursion.
    :param straight_call_on_recurse_denied: Whether to call the wrapped function instead of returning ``None`` on recurse denied.
    :return: A ``listens`` decorator configured for listener-system methods.
    """
    return listens(
        *names,
        allow_recurse=False,
        throw_on_recurse_denied=throw_on_recurse_denied,
        straight_call_on_recurse_denied=straight_call_on_recurse_denied
    )
