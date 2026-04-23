from __future__ import annotations

from decimal import Decimal
from typing import Callable, Iterable, Mapping

from .errors import ParseError
from .tokens import EquationPiece


class Symbol[**P, R]:
    """Describe a symbolic operator and the callable bound to it."""

    def __init__(
            self,
            symbol: str,
            name: str,
            *,
            param_count: int=0,
            after_loop:bool=False,
            action: Callable[P, R] | None = None
    ):
        self._symbol = symbol
        self._name = name
        self._param_count = param_count
        self._after_loop = after_loop
        self._action = action

    @property
    def symbol(self) -> str:
        """Return the symbol text."""
        return self._symbol

    @property
    def name(self) -> str:
        """Return the descriptive name of the symbol."""
        return self._name

    @property
    def param_count(self) -> int:
        """Return how many operands this symbol expects."""
        return self._param_count

    @property
    def after_loop(self) -> bool:
        """Return whether this symbol applies after pairwise reductions."""
        return self._after_loop

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        if self._action is None:
            return None
        return self._action(*args, **kwargs)

    def as_operator(self):
        return Operator(self._symbol)

    def compare(self, other):
        """Compare this symbol with another symbol or comparable value."""
        if self is other:
            return 0
        other_symbol = None
        this_symbol = self._symbol
        if isinstance(other, Symbol):
            other_symbol = other._symbol
        else:
            other_symbol = other
            if isinstance(other, (int, float)):
                this_symbol =  ord(self._symbol)

        if this_symbol == other_symbol:
            return 0
        elif this_symbol < other_symbol:
            return -1
        elif this_symbol > other_symbol:
            return 1
        raise RuntimeError(f"Failed to compare `{this_symbol}` to `{other_symbol}`")

    def __eq__(self, other):
        return self.compare(other) == 0
    def __ne__(self, other):
        return self.compare(other) != 0
    def __lt__(self, other):
        return self.compare(other) < 0
    def __le__(self, other):
        return self.compare(other) <= 0
    def __gt__(self, other):
        return self.compare(other) > 0
    def __ge__(self, other):
        return self.compare(other) >= 0

    def __str__(self):
        return self.symbol


class Symbols(Mapping[str, Symbol]):
    """
    Map symbol text to ``Symbol`` objects with filtering helpers.

    Order
    -----
    It is good practice to Order the symbols like:
    ``<=``, ``>=``, ``<``, ``>``, ``=``.
    This is because of the way the parsing system parses
    ``Symbol`` objects. Refer to ``parser.parse_symbols`` for more details.
    """

    def __init__(self, symbols: Iterable[Symbol]):
        self._symbol_list: list[str] = []
        self._param_counts: dict[int, list[str]] = {}
        self._symbols: dict[str, Symbol] = {}
        for symbol in symbols:
            sym = symbol.symbol
            self._symbols[sym] = symbol
            self._symbol_list.append(sym)
            self._param_counts.setdefault(symbol.param_count, []).append(sym)

    def index(self, value: str | Symbol, start: int = 0, stop=None) -> int:
        """Return the ordered position of a symbol."""
        value = str(value)
        if stop is None:
            return self._symbol_list.index(value, start)
        return self._symbol_list.index(value, start, stop)

    def at(self, index: int) -> Symbol:
        """Return the symbol stored at ``index``."""
        return self._symbols[self._symbol_list[index]]

    def contains_any(self, values: Iterable[object]):
        """Return whether any provided value matches a registered symbol."""
        for value in values:
            if value in self._symbols:
                return True
        return False

    def __getitem__(self, key, /):
        return self._symbols[key]

    def __len__(self):
        return len(self._symbol_list)

    def iter(self, param_count: int | None = None, after_loop: bool = True, during_loop: bool = True):
        """Iterate symbols filtered by arity and loop timing."""
        loop_list = self._symbol_list if param_count is None else self._param_counts.get(param_count, [])
        for symbol in loop_list:
            sym = self[symbol]
            if sym.after_loop and not after_loop:
                continue
            elif not sym.after_loop and not during_loop:
                continue
            yield symbol

    def __iter__(self):
        for symbol in self._symbol_list:
            yield symbol

    def __contains__(self, key):
        return str(key) in self._symbols

# Predefined Symbols
# Order matters, refer to `parser.parse_symbols` on how symbols are parsed.

MATH_SYMBOLS = Symbols([
    Symbol("^", "exponentiation", param_count=2, action = lambda a, b: a ** b),
    Symbol("*", "times", param_count=2, action = lambda a, b: a * b),
    Symbol("/", "divide", param_count=2, action = lambda a, b: a / b),
    Symbol("%", "modulus", param_count=2, action = lambda a, b: a % b),
    Symbol("+", "plus", param_count=2, action = lambda a, b: a + b),
    Symbol("-", "minus", param_count=2, action = lambda a, b: a - b),
])

COMPARISON_SYMBOLS = Symbols([
    Symbol("!=", "notEqual", param_count=2, action = lambda a, b: a != b),
    Symbol("<=", "lessOrEqual", param_count=2, action = lambda a, b: a <= b),
    Symbol(">=", "greaterOrEqual", param_count=2, action = lambda a, b: a >= b),
    Symbol("<", "less", param_count=2, action = lambda a, b: a < b),
    Symbol(">", "greater", param_count=2, action = lambda a, b: a > b),
    Symbol("=", "equal", param_count=2, action = lambda a, b: a == b),
])

UNION_SYMBOLS = Symbols([
    Symbol("&", "and", param_count=2, action = lambda a, b: a and b),
    Symbol("|", "or", param_count=2, action = lambda a, b: a or b),
    Symbol("~", "imp", param_count=2, action = lambda a, b: (not a) or b),
    Symbol("^", "ex", param_count=2, action = lambda a, b: a != b),
    Symbol("!", "not", param_count=1, after_loop=True, action = lambda a: not a),
])


class Operator(EquationPiece[str]):
    """Represent an equation operator that can calculate or compare values."""

    def __init__(self, operator: str):
        super().__init__(operator)

    def calculate(self, num1: Decimal, num2: Decimal) -> Decimal:
        """Apply this operator as a mathematical operator."""
        if self.value in MATH_SYMBOLS:
            return MATH_SYMBOLS[self.value](num1, num2)
        raise ParseError("`operator` isn't a mathematical operator")

    def compare(self, num1: Decimal, num2: Decimal) -> bool:
        """Apply this operator as a comparison operator."""
        if self.value in COMPARISON_SYMBOLS:
            return COMPARISON_SYMBOLS[self.value](num1, num2)
        raise ParseError("`operator` isn't a comparison operator")

    def union(self, *args: bool) -> bool:
        """
        Reduce one or more boolean operands using a flag-driven composite logic operator.

        This method performs a left-to-right fold over the given boolean arguments.
        The behavior is determined by which operator flags are present in ``self.value``.
        Multiple flags may be active at the same time; when they are, they are applied
        in a fixed sequence of logical stages for every reduction step.

        Enabled operator flags
        ----------------------
        The presence of the following characters in ``self.value`` enables the
        corresponding stage:

        ``"&"``  AND stage
            Combines the accumulator and the current value using logical AND.

        ``"|"``  OR stage
            If ``"|"`` is present, this stage performs logical OR.

        ``"~"``  IMPLICATION stage
            Applies material implication using the rule:
                ``A → B == (not A) or B``
            where ``A`` is the intermediate result from previous stages.

        ``"^"`` EXCLUSIVE stage
            Exclusive modifier.
            Preforms XOR.

        ``"!"``  NOT stage
            Negates the final result after all operands have been reduced.

        Evaluation order
        ----------------
        For each pairwise reduction step, the enabled stages are applied in
        the fixed order defined by ``UNION_SYMBOLS``.

        Common gate interpretations
        ---------------------------
        With this staged model, several standard logic gates emerge naturally:

        - ``"&"``     → AND
        - ``"|"``     → OR
        - ``"^"``    → XOR
        - ``"!&"``    → NAND
        - ``"!|"``    → NOR
        - ``"!^"``   → XNOR
        - ``"!"``     → NOT (final inversion)

        Other combinations form composite or non-standard gates whose behavior
        is fully defined by the staged evaluation rules above.

        Parameters
        ----------
        *args : bool
            One or more boolean values to be reduced.

        Returns
        -------
        bool
            The result of reducing all operands using the enabled operator flags.

        Raises
        ------
        ParseError
            - If no operands are provided.
            - If ``self.value`` contains none of the supported operator flags.
        """
        if len(args) == 0:
            raise ParseError("`args` can't be empty")
        last: bool | None = None

        if not UNION_SYMBOLS.contains_any(self.value):
            raise ParseError("`operator` isn't an union operator")
        for current in args:
            if last is None:
                last = current
                if len(args) > 1:
                    continue
            future = last
            for symbol in UNION_SYMBOLS.iter(2, after_loop=False):
                if symbol in self.value:
                    future = UNION_SYMBOLS[symbol](future, current)
            last = future
        for symbol in UNION_SYMBOLS.iter(1, during_loop=False):
            if symbol in self.value:
                last = UNION_SYMBOLS[symbol](last)
        return False if last is None else last
