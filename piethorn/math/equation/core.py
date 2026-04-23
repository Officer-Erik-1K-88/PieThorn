from __future__ import annotations

from decimal import Context, Decimal, localcontext
from typing import Mapping

from piethorn.collections.char import CharSequence

from .functions import FUNCTIONS, _DecimalValid
from .parameters import Parameter, Parameters
from .parsed import EquationFunc, FuncParam, ParsedEquation
from .parser import EvalParser
from .symbols import COMPARISON_SYMBOLS, MATH_SYMBOLS, Operator, UNION_SYMBOLS
from .tokens import Number, Variable


class Equation:
    """Parse an equation string into a reusable tokenized representation."""

    def __init__(self, equation: str, context: Context):
        self._equation = equation
        self._context = context
        parser = EvalParser(CharSequence(equation), context)
        parser.parse()
        self._parsed_equation = parser.parsed
        self._value = None

    @property
    def equation(self):
        """Return the original equation string."""
        return self._equation

    @property
    def context(self):
        """Return the decimal context associated with this equation."""
        return self._context

    def has_variables(self):
        """Return whether the equation references variables."""
        return self._parsed_equation.var_count != 0

    def calculate(self, variables: Mapping[str, _DecimalValid] | None = None) -> Decimal:
        if self._value is not None and not self.has_variables():
            return self._value
        if variables is None and self.has_variables():
            if self._parsed_equation.var_count > self._parsed_equation.var_count_default:
                raise ValueError("No variables specified when equation has variables.")
        with localcontext(self._context):
            value = self._evaluate_numeric(self._parsed_equation, variables or {})
        if not self.has_variables():
            self._value = value
        return value

    def _resolve_variable(self, variable: Variable, variables: Mapping[str, _DecimalValid]) -> Decimal:
        if variable.value in variables:
            return Decimal(variables[variable.value])
        if variable.has_default():
            return Decimal(variable.default)
        raise ValueError(f"Variable `{variable.value}` not specified.")

    def _evaluate_value(self, piece, variables: Mapping[str, _DecimalValid]) -> Decimal:
        if isinstance(piece, Number):
            return piece.value
        if isinstance(piece, Variable):
            return self._resolve_variable(piece, variables)
        if isinstance(piece, EquationFunc):
            return self._evaluate_function(piece, variables)
        if isinstance(piece, ParsedEquation):
            return self._evaluate_numeric(piece, variables)
        raise TypeError(f"Unsupported equation piece: {type(piece).__name__}")

    def _evaluate_numeric(self, parsed: ParsedEquation, variables: Mapping[str, _DecimalValid]) -> Decimal:
        pending: list[Operator] = []
        current: Decimal | None = None
        operator: Operator | None = None

        for piece in parsed:
            if isinstance(piece, Operator):
                if piece.value in MATH_SYMBOLS:
                    if current is None:
                        pending.append(piece)
                    else:
                        operator = piece
                    continue
                raise ValueError(f"Unexpected non-math operator `{piece.value}` in numeric expression.")

            value = self._evaluate_value(piece, variables)
            for unary in reversed(pending):
                if unary.value == "+":
                    continue
                if unary.value == "-":
                    value = -value
                    continue
                raise ValueError(f"Unsupported unary operator `{unary.value}`.")
            pending.clear()

            if current is None:
                current = value
                continue
            if operator is None:
                raise ValueError("Missing operator between values.")
            current = operator.calculate(current, value)
            operator = None

        if current is None:
            raise ValueError("Parsed equation is empty.")
        if operator is not None:
            raise ValueError(f"Incomplete expression after `{operator.value}`.")
        if pending:
            raise ValueError(f"Incomplete expression after `{pending[-1].value}`.")
        return current

    def _evaluate_comparison(self, parsed: ParsedEquation, variables: Mapping[str, _DecimalValid]) -> bool:
        current_value: Decimal | None = None
        current_operator: Operator | None = None
        result = True

        for piece in parsed:
            if isinstance(piece, Operator) and piece.value in COMPARISON_SYMBOLS:
                current_operator = piece
                continue

            value = self._evaluate_value(piece, variables)
            if current_value is None:
                current_value = value
                continue
            if current_operator is None:
                raise ValueError("Missing comparison operator between expressions.")
            result = result and current_operator.compare(current_value, value)
            current_value = value
            current_operator = None

        if current_value is None:
            raise ValueError("Parsed comparison is empty.")
        if current_operator is not None:
            raise ValueError(f"Incomplete comparison after `{current_operator.value}`.")
        return result

    def _evaluate_boolean(self, parsed: ParsedEquation, variables: Mapping[str, _DecimalValid]) -> bool:
        pending_not = False
        operands: list[bool] = []
        operators: list[Operator] = []
        buffer: list = []

        def flush_buffer():
            if not buffer:
                raise ValueError("Boolean statement is missing an operand.")
            value = self._evaluate_comparison(ParsedEquation(buffer), variables)
            buffer.clear()
            return value

        for piece in parsed:
            if isinstance(piece, Operator):
                if piece.value == "!":
                    pending_not = not pending_not
                    continue
                if UNION_SYMBOLS.contains_any(piece.value):
                    value = flush_buffer()
                    if pending_not:
                        value = not value
                        pending_not = False
                    operands.append(value)
                    operators.append(piece)
                    continue
            buffer.append(piece)

        value = flush_buffer()
        if pending_not:
            value = not value
        operands.append(value)

        result = operands[0]
        for index, operator in enumerate(operators):
            result = operator.union(result, operands[index + 1])
        return result

    def _evaluate_function(self, function: EquationFunc, variables: Mapping[str, _DecimalValid]) -> Decimal:
        target = FUNCTIONS.get(function.name)
        if target.is_value():
            return target.apply()

        evaluated = []
        for param in function.parameters:
            assert isinstance(param, FuncParam)
            value = self._evaluate_boolean(param, variables) if param.takes_boolean else self._evaluate_numeric(param, variables)
            evaluated.append(
                Parameter(
                    param.name,
                    takes_boolean=param.takes_boolean,
                    default=param.default,
                    value=value,
                    required=param.required,
                )
            )
        return target(Parameters(tuple(evaluated)))
