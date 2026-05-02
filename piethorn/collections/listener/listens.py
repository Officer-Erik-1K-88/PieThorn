from __future__ import annotations

from functools import wraps

from piethorn.collections.listener.listener import _listener_name


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

    Class methods and static methods trigger global listeners
    unless manually passed a Listenable instance as their first argument.

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
            from piethorn.collections.listener.listenable import Listenable, GLOBAL_LISTENERS
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