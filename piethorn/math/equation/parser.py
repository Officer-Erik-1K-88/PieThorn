from __future__ import annotations

from decimal import Context, Decimal
from typing import Callable

from piethorn.collections.char import CharIterator, CharSequence, Char

from .errors import ParseError, SyntaxParseError
from .functions import FUNCTIONS
from .parameters import Parameters
from .parsed import FuncParam, ParsedEquation
from .symbols import Operator, Symbols, Symbol, MATH_SYMBOLS, COMPARISON_SYMBOLS, UNION_SYMBOLS
from .tokens import Number, Variable


def parse_symbols(
        chars: CharIterator,
        symbols: Symbols,
        handler: Callable[[Symbol], None] | Callable[[Operator], None],
        mix_symbols: bool = False,
):
    """
    The order that is defined by ``symbols`` is the order of checking.
    Because of this, if you have the symbol ``<`` before ``<=``, then ``<=``
    will never get parsed. However, in ``EvalParser``, it will always throw an
    error since the parser didn't expect an ``=`` to precede ``<``.
    Therefore, ``<=`` must always be defined before ``<``.
    This works because if there is no ``=`` after ``<`` then the ``=`` sign
    is ignored and will continue the parse as the ``<`` symbol.

    Another note, if the symbol being checked is ``!<=``, then it
    is possible of it to find the following symbols:
    ``!<=``, ``!<``, ``!=``, ``!``, ``<``, or ``=``.
    Because of this, all multi-sign symbols should come before
    single sign symbols.

    :param chars: the characters to parse
    :param symbols: The symbols to parse
    :param handler: Handler for when a symbol is encountered
    :param mix_symbols: Whether symbols should be mixed together. If ``True``, then will mix all symbols found and send it to ``handler`` as an ``Operator``.
    :return:
    """
    mixed = ""
    while True:
        cont = False
        for symbol in symbols:
            followed_sym = ""
            for sym in symbol:
                # build symbol
                if chars.eat(sym):
                    followed_sym += sym
            if followed_sym in symbols:
                # parse symbol
                cont = True
                act_sym = symbols[followed_sym]
                if mix_symbols:
                    mixed += act_sym.symbol
                else:
                    handler(act_sym)
                    break
            elif followed_sym != "":
                raise SyntaxParseError(f"Unknown Symbol: '{followed_sym}', found during parse of '{symbol}' symbol")
        if not cont:
            break
    if mix_symbols:
        if mixed == "":
            raise SyntaxParseError(f"Cannot handle mixing of symbols when none found")
        handler(Operator(mixed))


class EvalParser(CharIterator):
    def __init__(self, chars: CharSequence, context: Context):
        super().__init__(chars, skip_space=True, skip_empty=True)
        self._context = context
        self._parsed = ParsedEquation()

    @property
    def context(self):
        """Return the decimal context used during parsing."""
        return self._context

    @property
    def parsed(self):
        """Return the parsed equation tree built by this parser."""
        return self._parsed

    def parse(self):
        """Parse the full input sequence into ``parsed``."""
        # Arithmetic expressions are the top-level grammar entrypoint here.
        self._parse_expression()
        if not self.next_ended():
            raise ParseError("Ended too Early")

    def _peek_is(self, *chars: str, handler: Callable[[CharSequence | Char], bool] | None=None, space_conscious: bool=False) -> bool:
        if space_conscious:
            next_index = self.pos + 1
            if next_index < 0 or next_index >= self.char_count():
                return False
            future = self._chars[next_index]
        else:
            future = self.peek()
        if future is None:
            return False
        if space_conscious and (future.isspace() or future.is_empty()):
            return False
        if handler is not None:
            if handler(future):
                return True
        return any(future == char for char in chars)

    def _peek_starts_expression(self) -> bool:
        future = self.peek()
        if future is None:
            return False
        return (
            future.isdecimal()
            or future == "."
            or future == "$"
            or future == "("
            or future == "+"
            or future == "-"
            or future.isalpha()
            or future == "_"
        )

    def _peek_starts_implicit_expression(self) -> bool:
        future = self.peek()
        if future is None:
            return False
        return (
            future.isdecimal()
            or future == "."
            or future == "$"
            or future == "("
            or future.isalpha()
            or future == "_"
        )

    def _peek_starts_statement(self) -> bool:
        future = self.peek()
        if future is None:
            return False
        return future == "!" or self._peek_starts_expression()

    def _assert_no_implicit_expression(self, message: str):
        if self._peek_starts_implicit_expression():
            raise SyntaxParseError(message)

    def _parse_symbols(
            self,
            symbols: Symbols,
            handler: Callable[[], None],
    ):
        def parse_handler(sym: Symbol):
            if not self._peek_starts_expression():
                raise SyntaxParseError(f"Incomplete expression after '{sym.symbol}'")
            self._parsed.append(sym.as_operator())
            handler()

        parse_symbols(self, symbols, parse_handler)

    def _parse_expression(self):
        # expression := factor ((MATH_SYMBOL) factor)*
        self._parse_factor()
        self._parse_symbols(MATH_SYMBOLS, self._parse_factor)

    def _parse_factor(self):
        # factor handles unary operators, grouped expressions, literals,
        # variables, and function calls.
        if self.eat("+"):
            self._parsed.append(Operator("+"))
            self._parse_factor()
            return
        elif self.eat("-"):
            self._parsed.append(Operator("-"))
            self._parse_factor()
            return


        if self.eat("("): # parentheses
            # Parse a nested arithmetic expression into a child ParsedEquation.
            self._parsed.enter_sub()
            self._parse_expression()
            self._parsed.exit_sub()
            if not self.eat(")"):
                raise SyntaxParseError("Missing closing parenthesis: ')'")
        elif self.eat("$"):
            # Variables are delimited as $name$.
            # With optional default value: $name:default$
            var_name = ""
            in_options = False
            var_default = None
            while not self.eat("$"):
                if self.eat(":"):
                    # Checks to see if the variable has a default value
                    if in_options:
                        raise SyntaxParseError("Invalid Syntax: only one ':' is allowed in var")
                    in_options = True
                    continue
                if in_options:
                    # Get the variable's default value, if one exists
                    if var_default is None:
                        var_default = ""
                    if not self._peek_num_check(True):
                        raise SyntaxParseError("Invalid Syntax: Default variable value must be numeric")
                    var_default += str(self.next())
                else:
                    # Get the variable's name
                    if not self._peek_identifier_part_check(True):
                        raise SyntaxParseError("Invalid Syntax: Variable name must only contain alpha-numeric characters and '_'")
                    var_name += str(self.next())
                if self.next_ended():
                    raise SyntaxParseError("Missing variable closer: '$'")
            self._parsed.append(Variable(var_name, var_default))
        elif self._peek_num_check(False): # number
            # Consume a decimal literal as a single Number token.
            str_val = str(self.next())
            while self._peek_num_check(True):
                str_val += str(self.next())
            self._parsed.append(Number(Decimal(str_val, self.context)))
        elif self._peek_letter_check(False): # function
            # Consume an identifier, then bind and parse its argument list.
            func = str(self.next())
            while self._peek_letter_check(True):
                func += str(self.next())
            if func in FUNCTIONS:
                self._parsed.enter_function(func, FUNCTIONS.name_index(func))
                func_val = FUNCTIONS.get(func)
                if not func_val.is_value():
                    self._parse_parameters(func_val.parameters)
                self._parsed.exit_function()
            else:
                raise SyntaxParseError(f"Unknown symbol '{func}'")
        else:
            raise SyntaxParseError("Unexpected character: '%s'" % self.peek())
        self._assert_no_implicit_expression("Missing operator between expressions")


    def _peek_num_check(self, space_conscious: bool):
        return self._peek_is(".", handler=lambda c: c.isdecimal(), space_conscious=space_conscious)

    def _peek_letter_check(self, space_conscious: bool):
        return self._peek_is("_", handler=lambda c: c.isalpha(), space_conscious=space_conscious)

    def _peek_identifier_part_check(self, space_conscious: bool):
        return self._peek_is("_", handler=lambda c: c.isalnum(), space_conscious=space_conscious)

    def _parse_statement(self):
        # Boolean statements extend the arithmetic grammar with negation,
        # grouping, comparisons, and unions.
        if self.eat("!"):
            if not self._peek_starts_statement():
                raise SyntaxParseError("Incomplete statement after '!'")
            self._parsed.append(Operator("!"))
            self._parse_statement()
            return

        if self.eat("("):
            self._parsed.enter_sub()
            self._parse_union(True)
            self._parsed.exit_sub()
            if not self.eat(")"):
                raise SyntaxParseError("Missing closing parenthesis: `)`")
        else:
            self._parse_comparison()

        if self._needs_union(): # if statement has more union symbols
            self._parse_union(False)
        elif self._peek_starts_statement():
            raise SyntaxParseError("Missing boolean operator between statements")

    def _parse_union(self, inst_state: bool):
        if inst_state:
            self._parse_statement()
        # Union operators chain boolean statements left-to-right.

        def handler(operator: Operator):
            if not self._peek_starts_statement():
                raise SyntaxParseError(f"Incomplete union after '{operator.value}'")
            self._parsed.append(operator)
            self._parse_statement()

        while True:
            if not self._needs_union():
                break
            parse_symbols(self, UNION_SYMBOLS, handler, True)

    def _parse_comparison(self):
        # Comparisons are built from arithmetic expressions on both sides.
        self._parse_expression()
        if not self._needs_compare():
            raise SyntaxParseError("Missing comparison operator")

        def during():
            self._parse_expression()
            if self._peek_starts_expression():
                raise SyntaxParseError("Missing comparison operator between expressions")

        self._parse_symbols(COMPARISON_SYMBOLS, during)

    def _needs_union(self):
        return self.peek_check(lambda ch: ch in UNION_SYMBOLS)

    def _needs_compare(self):
        return self.peek_check(lambda ch: ch == ">" or ch == "<" or ch == "=" or ch == "!")

    def _parse_parameters(self, parameters: Parameters):
        if self.eat("("):
            parsed_count = 0
            declared = tuple(parameters)
            # Each declared parameter gets its own parse target so nested
            # expressions are captured independently.
            for index, parameter in enumerate(declared):
                if self._peek_is(")"):
                    break
                current = self._parsed.get_current(sub_tonf=True, sub_toz=True).get_function_parent()
                param = FuncParam(
                    parameter.name,
                    parameter.takes_boolean,
                    parameter.required,
                    parameter.default
                )
                param._parent = current
                current.get_function().add_param(param)
                if parameter.takes_boolean:
                    self._parse_statement()
                else:
                    self._parse_expression()
                parsed_count = index + 1
                if self.eat(")"):
                    break
                if index + 1 >= len(declared):
                    raise SyntaxParseError("Too many parameters")
                if not self.eat(","):
                    raise SyntaxParseError("Missing parameter separator: ','")
            else:
                if not self.eat(")"):
                    raise SyntaxParseError("Missing closing parenthesis: ')'")

            for parameter in declared[parsed_count:]:
                if parameter.required and parameter.is_empty():
                    raise ParseError(f"Parameter `{parameter.name}` is required")
        else:
            raise SyntaxParseError("Missing starting parenthesis: '('")
