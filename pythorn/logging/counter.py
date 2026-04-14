import math
from typing import Optional, Iterable, Sequence, Collection, Literal, Any

from pythorn.collections.views import SequenceView

from pythorn.logging.logger import Logger


class CounterBehavior:
    """Configure how counters react to resets and parent-child propagation."""

    def __init__(self, reset_on_reset: bool = True, remove_on_reset: bool = False, affect_child: bool = False):
        self._reset_on_reset = reset_on_reset
        self._remove_on_reset = remove_on_reset
        self._affect_child = affect_child
        self._parent_behavior: CounterBehavior | None = None

    @property
    def reset_on_reset(self):
        """Return whether reset should zero this counter."""
        # noinspection PyUnresolvedReferences
        return self._parent_behavior.reset_on_reset if self.affected_by_parent else self._reset_on_reset

    @property
    def remove_on_reset(self):
        """Return whether reset should remove this counter from its parent."""
        # noinspection PyUnresolvedReferences
        return self._parent_behavior.remove_on_reset if self.affected_by_parent else self._remove_on_reset

    @property
    def affect_child(self):
        """Return whether this behavior propagates to child counters."""
        return self._affect_child

    @property
    def parent(self):
        """Return the parent behavior when this behavior is inherited."""
        return self._parent_behavior

    @property
    def affected_by_parent(self):
        """Return whether a parent behavior currently overrides this one."""
        # noinspection PyUnresolvedReferences
        return self.parent is not None and self.parent.affect_child

    def reset_allowed(self):
        """Return whether reset has any effect under this behavior."""
        return self.reset_on_reset or self.remove_on_reset

    def child_behavior(self, *args, **kwargs) -> CounterBehavior:
        """Create a child behavior linked back to this behavior."""
        kwargs.setdefault("reset_on_reset", False)
        kwargs.setdefault("remove_on_reset", True)
        kwargs.setdefault("affect_child", False)
        child_behavior = CounterBehavior(*args, **kwargs)
        child_behavior._parent_behavior = self
        return child_behavior

_DEFAULT_COUNTER_BEHAVIOR: CounterBehavior = CounterBehavior(
    reset_on_reset=True,
    remove_on_reset=False,
    affect_child=False,
)


def _get_compare_num(value, other):
    num_to_check: int | float = 0
    if isinstance(value, Percent):
        num_to_check = value.larger_percent() if isinstance(other, int) else value.percent
    elif isinstance(value, Counter):
        num_to_check = value.current
    elif isinstance(value, (int, float)):
        num_to_check = value
    elif hasattr(value, '__float__'):
        num_to_check = float(value)
    elif hasattr(value, '__int__'):
        num_to_check = int(value)
    elif hasattr(value, '__bool__'):
        num_to_check = 1 if bool(value) else 0
    return num_to_check


class Counter:
    """Track visible and hidden progress with optional logger integration."""

    def __init__(self, name: str, visible: int=0, hidden: int=0, only_visible=True, *, step: float=1.0, logger: Optional[Logger] = None, behavior: CounterBehavior = _DEFAULT_COUNTER_BEHAVIOR):
        if visible < 0:
            raise ValueError("The visible count must not be less than zero.")
        if hidden < 0:
            raise ValueError("The hidden count must not be less than zero.")
        if step < 0.0001:
            raise ValueError("The step must not be less than 0.0001.")
        self._name = name
        self._visible = visible
        self._hidden = hidden
        self._decimal: float = 0.0
        self.only_visible = only_visible
        self._step = step
        self._logger: Logger | None = logger
        self.allow_messages = True
        """ Defines if this Counter is allowed to print messages to it's given logger. """
        self._behavior: CounterBehavior = behavior

    @property
    def behavior(self):
        """
        Defines the behavior of this counter.

        Refer to ``CounterBehavior`` for more information
        on default behavior.
        :return:
        """
        return self._behavior

    @property
    def name(self):
        """Return the display name of this counter."""
        return self._name

    @property
    def long_name(self):
        """Return the expanded display name of this counter."""
        return self.name

    @property
    def visible(self):
        """Return the visible whole-number count."""
        return self._visible

    @property
    def hidden(self):
        """Return the hidden whole-number count."""
        return self._hidden

    @property
    def decimal(self):
        """Return the fractional portion of the counter value."""
        return self._decimal

    @property
    def total(self):
        """Return the combined visible and hidden counts."""
        return self._visible + self._hidden

    @property
    def current(self) -> float:
        """Return the current counter value exposed to callers."""
        return (self._visible if self.only_visible else self.total) + self._decimal

    @current.setter
    def current(self, amount: float):
        """Set the current counter value, splitting integer and decimal parts."""
        if amount <= 0:
            self._visible = 0
            self._decimal = 0.0
        else:
            self._visible = math.floor(amount)
            decimal = amount - self._visible
            self._decimal = decimal
        if not self.only_visible:
            self._hidden = 0

    @property
    def step(self) -> float:
        """
        How much to add per tick.
        """
        return self._step

    def _msg_format(
            self,
            titles: Iterable[str],
            messages: Iterable[str],
            compact: bool,
            allow_lr: bool,
    ) -> str:
        title = ""
        message = ""
        add_msg = ""

        for t in titles:
            if title != "":
                title += f" | {t}"
            else:
                title = t

        for m in messages:
            add_m = m
            if add_m.endswith("\r"):
                add_m = add_m.removesuffix("\r")
                allow_lr = True
            if message != "":
                message = add_msg
            else:
                add_msg += f" (INFO: {add_m})"

        msg = message + add_msg

        if title != "":
            msg = f"[{title}] {msg}"

        msg = f"'{self.name if compact else self.long_name}' : {msg}"

        if allow_lr:
            if not msg.endswith("\r"):
                msg += "\r"

        return msg

    def build_message(self, compact: bool=False, allow_lr: bool=False) -> tuple[list[str], list[str], bool]:
        """
        Builds the default message parts.

        :param compact: Whether to enforce a compact message.
        :param allow_lr: Whether the next item sent to the logger will replace this message.
        :return: A tuple where the first item is the list of titles, the second item is the list of message parts, and the third is ``allow_lr``.
        """
        title: list[str] = []
        message: list[str] = [f"Count at {self.current}"]

        if not compact:
            message[0] = f"{message[0]} with {self.visible} visible and {self.hidden} hidden"
            if self.only_visible:
                message.append("Count only includes visible")

        return title, message, allow_lr

    def message_send(
            self,
            title: Optional[str | Collection[str]] = None,
            message: Optional[str | Collection[str]] = None,
            compact: bool = False,
            allow_lr: bool=False,
            include_default_msg: bool=False,
            return_only: bool = False,
    ):
        """
        Sends a message to the logger that this Counter was instantiated with.

        This method does nothing when ``self.allow_messages`` is False or when no
        logger was defined at instantiation. If ``return_only`` is ``True``,
        then ``self.allow_messages`` is ignored.

        If both ``title`` and ``message`` are not provided, the message will be
        created from ``self.build_message(compact, allow_lr)``.

        :param title: The title(s) of the message.
        :param message: The message(s) to send.
        :param compact: Whether to enforce a compact message.
        :param allow_lr: Whether the next item sent to the logger will replace this message.
        :param include_default_msg: Whether to include the message created by ``self.build_message`` regardless of title or message.
        :param return_only: Doesn't send the message, useful when needing just the message text.
        :return: The full message sent.
        """
        if return_only or (self.allow_messages and self._logger is not None):
            no_title = title is None or len(title) == 0
            no_message = message is None or len(message) == 0
            include_default_msg = include_default_msg or (no_title and no_message)
            if include_default_msg:
                built_msg = self.build_message(compact, allow_lr)
                if not no_title:
                    if isinstance(title, str):
                        built_msg[0].append(title)
                    else:
                        # noinspection PyTypeChecker
                        built_msg[0].extend(title)
                if not no_message:
                    if isinstance(message, str):
                        built_msg[1].append(message)
                    else:
                        # noinspection PyTypeChecker
                        built_msg[1].extend(message)
                title, message, allow_lr = built_msg
            # noinspection PyTypeChecker
            msg = self._msg_format(title, message, compact, allow_lr)
            p_msg = msg
            if not return_only:
                if msg.endswith("\r"):
                    msg = msg.removesuffix("\r")
                    allow_lr = True
                # noinspection PyUnresolvedReferences
                self._logger.log(self.__class__.__name__.upper(), msg, end="\r" if allow_lr else "\n")
            return p_msg
        return None

    def add(self, amount: int, hidden=False):
        """
        Adds `amount` to the counter.

        :param amount: The amount to add.
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if amount != 0:
            amount = abs(amount)
            if hidden:
                self._hidden += amount
            else:
                self._visible += amount
            self.message_send()
            self.check()

    def float_add(self, amount: float, hidden=False):
        """
        Adds `amount` to the counter.

        This is the same as ``self.add``, except that the value added to
        ``self.visible`` or ``self.hidden`` is the floor of ``amount``.
        The rest of ``amount`` is added to ``self.decimal``, given that
        ``self.only_visible`` or ``hidden`` is ``False``.

        :param amount: The amount to add.
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if amount != 0:
            amount = abs(amount)
            amt = math.floor(amount)
            decimal = amount - amt
            if hidden:
                self._hidden += amt
            else:
                self._visible += amt
            if (not self.only_visible) or (not hidden):
                self._decimal += decimal
            self.message_send()
            self.check()

    def tick_worth(self, tick_count: int, worth: float, linear: bool) -> float:
        """
        Gets the tick worth of a tick given a tick count and a worth.

        A tick worth defines how much to multiply ``self.step`` by
        to get the amount to add to the counter.

        When a tick is linear, then the worth of that tick is
        defined as ``worth * tick_count``.
        While when it is a non-linear tick, then the
        worth of that tick is defined as ``worth / tick_count``.

        :param tick_count: The number of ticks.
        :param worth: The worth of the tick count.
        :param linear: Whether the tick is linear (True) or not (False).
        :return: the worth of the tick.
        """
        return worth * tick_count if linear else worth / tick_count

    def tick(self, tick_count: int=1, worth: float=1.0, linear=True, hidden=False):
        """
        Moves the counter by the specified number of ticks.

        The amount a tick will add to the counter is defined as
        ``self.step * self.tick_worth(tick_count,worth,linear)``.

        When ``linear`` is False, the tick generated will only be the
        smallest portion of a non-linear tick.
        Use ``non_linear_tick`` when needing the full non-linear tick.

        :param tick_count: The number of ticks.
        :param worth: The worth of the tick count.
        :param linear: Weather or not the tick is linear (Default: False)
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if tick_count < 1:
            tick_count = 1
        tick_worth = self.tick_worth(tick_count, worth, linear)
        to_add = self.step * tick_worth
        self.float_add(to_add, hidden)

    def non_linear_tick(self, tick_count: int=1, worth: float=1.0, hidden=False):
        """
        Moves the counter by the specified number of ticks.

        Unlike ``tick``, ``non_linear_tick`` handles non-linear ticks in a
        trustworthy way.

        The logic of a non-linear tick is defined as ``self.step * tick_worth``
        where each number in a loop that starts at `1` and ends at ``tick_count``
        adds ``self.tick_worth(number_item,worth,False)`` to ``tick_worth``.

        :param tick_count: The number of ticks.
        :param worth: The worth of the tick count.
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if tick_count < 1:
            tick_count = 1
        tick_worth = 0.0
        for count in range(1, tick_count+1):
            tick_worth += self.tick_worth(count, worth, False)
        to_add = self.step * tick_worth
        self.float_add(to_add, hidden)

    def reset(self):
        """Reset the counter back to zero when its behavior allows it."""
        if self.behavior.reset_on_reset:
            self._visible = 0
            self._hidden = 0
            self._decimal = 0.0

    def check(self):
        """Hook for subclasses to react after the counter changes."""
        pass

    def __str__(self):
        return str(self.__int__())

    def __int__(self):
        return self.current

    def __float__(self):
        return float(self.__int__())

    def __bool__(self):
        """ True if ``self.current`` is greater than zero else False """
        return self.current > 0

    def compare(self, other):
        """Compare this counter numerically with another value."""
        current = _get_compare_num(self, other)
        num_to_check = _get_compare_num(other, self)

        if current < num_to_check:
            return -1
        elif current > num_to_check:
            return 1
        return 0

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __gt__(self, other):
        return self.compare(other) == 1

    def __le__(self, other):
        return self.compare(other) <= 0

    def __lt__(self, other):
        return self.compare(other) < 0


class Percent(Counter):
    """Model percentage-style progress, optionally linked to child counters."""

    def __init__(
            self,
            name: str,
            current: float = 0,
            cap: int = 100,
            step: float = 1,
            *,
            logger: Optional[Logger] = None,
            behavior: CounterBehavior = _DEFAULT_COUNTER_BEHAVIOR
    ):
        super().__init__(name, step=step, logger=logger, behavior=behavior)
        if current < 0:
            raise ValueError("The current must not be less than zero.")
        if cap < current:
            raise ValueError("The cap must not be less than current.")
        if step > cap:
            raise ValueError("The step must not be greater than cap.")
        self._cap = cap
        self._parent: Percent | None = None
        self._children: list[Percent] = []
        self._child_view: SequenceView[Percent] | None = None
        self._worth = 0
        super().current = current

    def __call__(self, name: str, current: float=0, cap: int=100, step: float=1, worth: float=0, child_behavior=None):
        if child_behavior is None:
            child_behavior = dict()
        child = Percent(name, current, cap, step, logger=self._logger, behavior=self.behavior.child_behavior(**child_behavior))
        child._parent = self
        child._worth = worth
        self._children.append(child)
        return child

    @property
    def parent(self):
        """Return the parent percent counter when this counter is nested."""
        return self._parent

    @property
    def children(self) -> Sequence[Percent]:
        """Return an immutable view of this counter's child percentages."""
        if self._child_view is None:
            self._child_view = SequenceView(self._children)
        # noinspection PyTypeChecker
        return self._child_view

    # noinspection PyUnresolvedReferences
    @property
    def long_name(self):
        """Return the full hierarchical name for this percent counter."""
        name = self.name
        if self.is_child():
            parent = self
            while parent.is_child():
                parent = parent._parent
                name = f"{parent.name} ; {name}"
        return name

    @property
    def percent(self):
        """Return completion as a value between ``0`` and ``1``."""
        return self.current / self.cap

    @percent.setter
    def percent(self, value):
        """Set completion as a normalized value between ``0`` and ``1``."""
        if value < 0:
            raise ValueError("percent cannot be less than zero.")
        elif value > 1:
            raise ValueError("percent cannot be greater than one.")
        self.current = self.cap * value

    def larger_percent(self):
        """Return completion as a percentage between ``0`` and ``100``."""
        return self.percent * 100

    @property
    def current(self):
        """Return the current completed amount."""
        return super().current

    @current.setter
    def current(self, amount):
        """Set the completed amount, clamping it to ``cap``."""
        if amount >= self.cap:
            amount = self.cap
        super().current = amount

    @property
    def cap(self):
        """Return the total amount required for completion."""
        return self._cap

    @cap.setter
    def cap(self, amount):
        """Set the completion cap without dropping below ``current``."""
        if amount <= self.current:
            self._cap = self.current
        else:
            self._cap = amount

    @property
    def step(self):
        """Return the default amount added per tick or child completion."""
        return self._step

    @step.setter
    def step(self, count):
        """Set the default increment while clamping it to a valid range."""
        if count <= 0.0001:
            self._step = 0.0001
        elif count >= self.cap:
            self._step = self.cap
            # if self.current == 0:
            #    self._step = self.cap / 2
            # else:
            #    self._step = self.cap / self.current
        else:
            self._step = count

    @property
    def worth(self):
        """Return how much this child contributes to its parent on completion."""
        return self._worth

    def is_child(self):
        """Return whether this percent counter has a parent."""
        return self._parent is not None

    def is_parent(self):
        """Return whether this percent counter has child counters."""
        return len(self._children) != 0

    def is_complete(self):
        """Return whether this percent counter has reached its cap."""
        return self.percent >= 1

    def build_message(self, compact: bool = False, allow_lr: bool = False) -> tuple[list[str], list[str], bool]:
        """Build the default progress message for this percentage counter."""
        title: list[str] = []
        message: list[str] = []

        msg = ""
        if self.is_complete():
            msg = "COMPLETE"
        else:
            msg = f"{'' if compact else 'At '}{self} complete"

        if self.is_child():
            title.append("CHILD")
            if not compact:
                # noinspection PyUnresolvedReferences
                msg = f"({self._parent.message_send(compact=True, return_only=True)}) {msg}"

        if self.is_parent():
            title.append("PARENT")
            if not compact:
                msg = f"{msg} with {len(self._children)} children left"

        message.append(msg)

        return title, message, allow_lr

    def _pass_child(self, worth):
        self.float_add(worth if worth != 0 else self.step)

    def check(self):
        """
        Checks to see for completion of child requirements
        and detection of completion own self's percent bar.
        :return:
        """
        i = 0
        for child in self._children:
            if self.is_complete():
                break
            if child.is_complete():
                self._pass_child(child._worth)
            i += 1
            self.message_send(allow_lr=i != len(self._children))
        if self.is_complete():
            self.message_send()
            if self.is_child():
                # noinspection PyUnresolvedReferences
                self._parent._pass_child(self._worth)
                # if self.is_parent():
                #    self.message_send("CHILD TRANSFER", "This child is complete, moving it's children to the parent.")
                #    self._parent._child_transfer(self._children)
                self.message_send("CHECK", "Launching check of parent.")
                # noinspection PyUnresolvedReferences
                self._parent.check()

    def reset(self):
        """
        Resets this Percent back to zero.
        :return:
        """
        super().reset()
        i = 0
        to_remove = []
        for child in self._children:
            child_behavior = child.behavior
            if child_behavior.remove_on_reset:
                child._parent = None
                to_remove.append(i)
            elif child_behavior.reset_on_reset:
                child.reset()
            i+=1
        for index in to_remove:
            self._children.pop(index)

    def __str__(self):
        return f"{self.percent:.4%}"

    def __int__(self):
        return int(self.larger_percent())

    def __float__(self):
        return self.percent

    def __bool__(self):
        """ True if this Percent is 100% else False """
        return self.is_complete()
