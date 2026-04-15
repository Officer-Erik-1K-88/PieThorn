import unittest
from decimal import Context, Decimal

from pythorn.collections.char import CharSequence
from pythorn.math import equation as equation_module
from pythorn.math.equation import (
    ChildError,
    COMPARISON_SYMBOLS,
    Equation,
    EquationFunc,
    FuncParam,
    Function,
    Functions,
    MATH_SYMBOLS,
    Number,
    Operator,
    Parameter,
    Parameters,
    ParsedEquation,
    ParseError,
    Symbol,
    Symbols,
    SyntaxParseError,
    UNION_SYMBOLS,
    Variable,
    _EvalParser,
)


class EquationModuleTestCase(unittest.TestCase):
    def setUp(self):
        self.context = Context()
        self._old_functions = equation_module.FUNCTIONS
        equation_module.FUNCTIONS = Functions(())

    def tearDown(self):
        equation_module.FUNCTIONS = self._old_functions

    def install_functions(self, *functions: Function):
        equation_module.FUNCTIONS = Functions(tuple(functions))

    def parse_expression(self, text: str) -> ParsedEquation:
        parser = _EvalParser(CharSequence(text), self.context)
        parser.parse()
        return parser.parsed

    def parse_statement(self, text: str) -> ParsedEquation:
        parser = _EvalParser(CharSequence(text), self.context)
        parser._parse_statement()
        if not parser.next_ended():
            raise ParseError("Ended too Early")
        return parser.parsed


class ParameterTests(EquationModuleTestCase):
    def test_parameter_get_prefers_explicit_value(self):
        parameter = Parameter("amount", default=Decimal("2"), value=Decimal("5"))
        self.assertEqual(parameter.get(), Decimal("5"))

    def test_parameter_get_uses_default_when_value_missing(self):
        parameter = Parameter("amount", default=Decimal("2"))
        self.assertEqual(parameter.get(), Decimal("2"))

    def test_parameter_position_dependent_when_name_empty(self):
        parameter = Parameter("", required=True)
        self.assertTrue(parameter.position_dependent)

    def test_parameter_is_empty_when_no_value_or_default(self):
        parameter = Parameter("missing")
        self.assertTrue(parameter.is_empty())

    def test_parameter_new_copies_definition_and_replaces_value(self):
        parameter = Parameter("flag", takes_boolean=True, default=False, required=True)
        cloned = parameter.new(True)

        self.assertIsInstance(cloned, Parameter)
        self.assertEqual(cloned.name, "flag")
        self.assertTrue(cloned.takes_boolean)
        self.assertEqual(cloned.default, False)
        self.assertEqual(cloned.value, True)
        self.assertTrue(cloned.required)


class ParametersTests(EquationModuleTestCase):
    def test_parameters_fill_merges_named_and_positional_values(self):
        declared = Parameters((
            Parameter("", required=True),
            Parameter("named", default=Decimal("1")),
        ))
        given = Parameters((
            Parameter("", value=Decimal("10")),
            Parameter("named", value=Decimal("20")),
            Parameter("ignored", value=Decimal("99")),
        ))

        filled = declared.fill(given)

        self.assertEqual(filled[0].value, Decimal("10"))
        self.assertEqual(filled[1].value, Decimal("20"))
        self.assertEqual(len(filled), 2)

    def test_parameters_required_filled_detects_missing_required_values(self):
        parameters = Parameters((
            Parameter("left", value=Decimal("1"), required=True),
            Parameter("right", required=True),
        ))
        self.assertFalse(parameters.required_filled())

    def test_parameters_check_requires_same_length_and_required_values(self):
        declared = Parameters((
            Parameter("", required=True),
            Parameter("named", required=True),
        ))
        valid = Parameters((
            Parameter("", value=Decimal("1")),
            Parameter("named", value=Decimal("2")),
        ))
        invalid = Parameters((Parameter("", value=Decimal("1")),))

        self.assertTrue(declared.check(valid))
        self.assertFalse(declared.check(invalid))

    def test_parameters_get_named_parameter_raises_for_missing_name(self):
        parameters = Parameters((Parameter("named"),))
        with self.assertRaisesRegex(KeyError, "Parameter `missing` not found"):
            parameters.get_named_parameter("missing")

    def test_parameters_contains_supports_names_and_parameter_objects(self):
        parameter = Parameter("named")
        parameters = Parameters((parameter,))

        self.assertIn("named", parameters)
        self.assertIn(parameter, parameters)
        self.assertNotIn("missing", parameters)

    def test_parameters_add_and_radd_preserve_order(self):
        left = Parameter("left")
        right = Parameter("right")
        extra = Parameter("extra")

        added = Parameters((left,)) + Parameters((right,))
        tuple_added = Parameters((left,)) + (right,)
        iterable_added = Parameters((left,)) + [right]
        radded = (extra,) + Parameters((left,))

        self.assertEqual([param.name for param in added], ["left", "right"])
        self.assertEqual([param.name for param in tuple_added], ["left", "right"])
        self.assertEqual([param.name for param in iterable_added], ["left", "right"])
        self.assertEqual([param.name for param in radded], ["extra", "left"])


class FunctionTests(EquationModuleTestCase):
    def test_function_requires_value_or_action(self):
        with self.assertRaisesRegex(TypeError, "One of `action` or `value` must be specified"):
            Function("broken")

    def test_function_with_action_requires_parameters(self):
        with self.assertRaisesRegex(TypeError, "`parameters` must be specified when `action` is specified"):
            Function("broken", action=lambda params: Decimal("1"))

    def test_value_function_apply_returns_constant(self):
        function = Function("pi", value=Decimal("3.14"))
        self.assertTrue(function.is_value())
        self.assertEqual(function.apply(), Decimal("3.14"))

    def test_callable_function_call_fills_declared_parameters(self):
        function = Function(
            "sum",
            parameters=Parameters((
                Parameter("left", required=True),
                Parameter("right", default=Decimal("2")),
            )),
            action=lambda params: params[0].get() + params[1].get(),
        )
        result = function(Parameters((Parameter("left", value=Decimal("5")),)))
        self.assertEqual(result, Decimal("7"))

    def test_callable_function_call_requires_parameters_argument(self):
        function = Function(
            "sum",
            parameters=Parameters((Parameter("left", required=True),)),
            action=lambda params: params[0].get(),
        )
        with self.assertRaisesRegex(TypeError, "`parameters` must be specified"):
            function(None)

    def test_callable_function_call_requires_required_parameters(self):
        function = Function(
            "sum",
            parameters=Parameters((Parameter("left", required=True),)),
            action=lambda params: params[0].get(),
        )
        with self.assertRaisesRegex(TypeError, "all required `parameters` must be filled"):
            function(Parameters(()))

    def test_callable_function_apply_uses_param_handler(self):
        function = Function(
            "sum",
            parameters=Parameters((
                Parameter("left", required=True),
                Parameter("right", required=True),
            )),
            action=lambda params: params[0].get() + params[1].get(),
        )
        result = function.apply(
            lambda parameters: Parameters((
                parameters[0].new(Decimal("3")),
                parameters[1].new(Decimal("4")),
            ))
        )
        self.assertEqual(result, Decimal("7"))

    def test_callable_function_apply_requires_param_handler(self):
        function = Function(
            "sum",
            parameters=Parameters((Parameter("left", required=True),)),
            action=lambda params: params[0].get(),
        )
        with self.assertRaisesRegex(TypeError, "`param_handler` must be specified when `action` is specified"):
            function.apply()


class FunctionsTests(EquationModuleTestCase):
    def test_functions_get_index_names_and_contains(self):
        one = Function("one", value=Decimal("1"))
        two = Function("two", value=Decimal("2"))
        functions = Functions((one, two))

        self.assertEqual(functions.get("two"), two)
        self.assertEqual(functions.index("one"), 0)
        self.assertEqual(list(functions.names()), ["one", "two"])
        self.assertIn("one", functions)
        self.assertEqual(len(functions), 2)
        self.assertEqual(list(functions), [one, two])

    def test_functions_get_raises_for_missing_name(self):
        functions = Functions((Function("one", value=Decimal("1")),))
        with self.assertRaisesRegex(KeyError, "Parameter `missing` not found"):
            functions.get("missing")


class SymbolTests(EquationModuleTestCase):
    def test_symbol_call_compare_and_string(self):
        symbol = Symbol("+", "plus", param_count=2, action=lambda a, b: a + b)
        other = Symbol("-", "minus", param_count=2, action=lambda a, b: a - b)

        self.assertEqual(symbol(Decimal("2"), Decimal("3")), Decimal("5"))
        self.assertEqual(str(symbol), "+")
        self.assertEqual(symbol.compare("+"), 0)
        self.assertLess(symbol.compare(other), 0)

    def test_symbol_call_returns_none_without_action(self):
        symbol = Symbol("?", "unknown")
        self.assertIsNone(symbol())

    def test_symbols_helpers_filter_and_lookup(self):
        unary = Symbol("!", "not", param_count=1, after_loop=True, action=lambda value: not value)
        binary = Symbol("&", "and", param_count=2, action=lambda a, b: a and b)
        symbols = Symbols((unary, binary))

        self.assertEqual(symbols.index("&"), 1)
        self.assertEqual(symbols.at(0), unary)
        self.assertTrue(symbols.contains_any("abc&"))
        self.assertFalse(symbols.contains_any("abc"))
        self.assertEqual(list(symbols.iter(param_count=2)), ["&"])
        self.assertEqual(list(symbols.iter(param_count=1, during_loop=False)), ["!"])
        self.assertIn("&", symbols)
        self.assertEqual(list(symbols), ["!", "&"])


class OperatorTests(EquationModuleTestCase):
    def test_operator_calculate_uses_math_symbols(self):
        self.assertEqual(Operator("+").calculate(Decimal("2"), Decimal("3")), Decimal("5"))
        self.assertEqual(Operator("^").calculate(Decimal("2"), Decimal("3")), Decimal("8"))

    def test_operator_compare_uses_comparison_symbols(self):
        self.assertTrue(Operator(">=").compare(Decimal("3"), Decimal("3")))
        self.assertFalse(Operator("<").compare(Decimal("3"), Decimal("2")))

    def test_operator_union_supports_binary_and_post_negation(self):
        self.assertFalse(Operator("&").union(True, False))
        self.assertTrue(Operator("|").union(True, False))
        self.assertTrue(Operator("!|").union(False, False))
        self.assertTrue(Operator("^").union(True, False))

    def test_operator_raises_for_invalid_modes(self):
        with self.assertRaisesRegex(ParseError, "`operator` isn't a mathematical operator"):
            Operator("&").calculate(Decimal("1"), Decimal("2"))
        with self.assertRaisesRegex(ParseError, "`operator` isn't a comparison operator"):
            Operator("+").compare(Decimal("1"), Decimal("2"))
        with self.assertRaisesRegex(ParseError, "`args` can't be empty"):
            Operator("&").union()
        with self.assertRaisesRegex(ParseError, "`operator` isn't an union operator"):
            Operator("+").union(True, False)

    def test_builtin_symbol_sets_expose_expected_symbols(self):
        self.assertIn("+", MATH_SYMBOLS)
        self.assertIn(">=", COMPARISON_SYMBOLS)
        self.assertIn("!", UNION_SYMBOLS)


class ParsedEquationTests(EquationModuleTestCase):
    def test_parsed_equation_behaves_like_mutable_sequence(self):
        parsed = ParsedEquation()
        one = Number(Decimal("1"))
        two = Number(Decimal("2"))
        three = Number(Decimal("3"))

        parsed.append(one)
        parsed.extend((two,))
        parsed.insert(1, three)

        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0].value, Decimal("1"))
        self.assertEqual(parsed[1].value, Decimal("3"))
        self.assertEqual(parsed.count(two), 1)
        self.assertEqual(parsed.index(two), 2)
        self.assertIn(three, parsed)
        self.assertEqual(list(reversed(parsed))[0].value, Decimal("2"))

        parsed[1] = two
        del parsed[0]
        popped = parsed.pop()
        self.assertEqual(popped.value, Decimal("2"))
        parsed.clear()
        self.assertEqual(len(parsed), 0)

    def test_parsed_equation_extend_rejects_self(self):
        parsed = ParsedEquation()
        with self.assertRaisesRegex(ValueError, "Cannot extend because `values` is `current` ParsedEquation"):
            parsed.extend(parsed)

    def test_parsed_equation_reverse_is_not_supported(self):
        with self.assertRaisesRegex(NotImplementedError, "`reverse` not implemented"):
            ParsedEquation().reverse()

    def test_parsed_equation_subexpression_management(self):
        parsed = ParsedEquation()
        parsed.enter_sub()
        current = parsed.get_current()
        current.append(Number(Decimal("1")))

        self.assertTrue(parsed.in_sub)
        self.assertIsInstance(parsed.get_sub(), ParsedEquation)
        self.assertEqual(parsed.get_sub()[0].value, Decimal("1"))

        parsed.exit_sub()
        self.assertFalse(parsed.in_sub)

    def test_parsed_equation_function_management(self):
        parsed = ParsedEquation()
        parsed.enter_function("adder", 0)
        func = parsed.get_function()
        func.add_param(FuncParam("value", False, True))

        self.assertTrue(parsed.in_function)
        self.assertEqual(func.name, "adder")
        self.assertEqual(parsed.get_function_parent(), parsed)

        parsed.exit_function()
        self.assertFalse(parsed.in_function)

    def test_parsed_equation_raises_for_missing_child_context(self):
        parsed = ParsedEquation()
        with self.assertRaises(ChildError):
            parsed.get_sub()
        with self.assertRaises(ChildError):
            parsed.get_function()
        with self.assertRaises(ChildError):
            parsed.get_function_parent()


class FuncParamAndEquationFuncTests(EquationModuleTestCase):
    def test_func_param_exposes_param_metadata_and_sequence_value(self):
        param = FuncParam("condition", True, True, default=False)
        param.append(Variable("flag"))

        self.assertEqual(param.name, "condition")
        self.assertTrue(param.takes_boolean)
        self.assertTrue(param.required)
        self.assertEqual(param.default, False)
        self.assertEqual(param[0].value, "flag")

    def test_equation_func_get_and_get_param(self):
        function = Function("const", value=Decimal("7"))
        self.install_functions(function)

        equation_func = EquationFunc(0, "const")
        param = FuncParam("value", False, True)
        equation_func.add_param(param)

        self.assertEqual(equation_func.name, "const")
        self.assertEqual(equation_func.get(), function)
        self.assertIs(equation_func.get_param(), param)
        self.assertEqual(len(equation_func.parameters), 1)


class ParserTests(EquationModuleTestCase):
    def test_parser_parses_numbers_variables_parentheses_and_unary_operators(self):
        self.install_functions(Function("pi", value=Decimal("3.14")))
        parsed = self.parse_expression("-($name$ + .5) + pi")

        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0].value, "-")
        self.assertIsInstance(parsed[1], ParsedEquation)
        self.assertEqual(parsed[1][0].value, "name")
        self.assertEqual(parsed[1][1].value, "+")
        self.assertEqual(parsed[1][2].value, Decimal(".5"))
        self.assertEqual(parsed[2].value, "+")
        self.assertEqual(parsed[3].name, "pi")

    def test_parser_parses_callable_function_parameters(self):
        self.install_functions(
            Function(
                "add",
                parameters=Parameters((
                    Parameter("left", required=True),
                    Parameter("right", required=True),
                )),
                action=lambda params: params[0].get() + params[1].get(),
            )
        )

        parsed = self.parse_expression("add(1, 2)")
        func = parsed[0]

        self.assertEqual(func.name, "add")
        self.assertEqual(len(func.parameters), 2)
        self.assertEqual(func.parameters[0][0].value, Decimal("1"))
        self.assertEqual(func.parameters[1][0].value, Decimal("2"))

    def test_parser_parses_boolean_statements_and_unions(self):
        parsed = self.parse_statement("!(1 < 2) | 3 = 3")
        self.assertEqual(parsed[0].value, "!")
        self.assertIsInstance(parsed[1], ParsedEquation)
        self.assertEqual([piece.value for piece in parsed[1]], [Decimal("1"), "<", Decimal("2")])
        self.assertEqual(parsed[2].value, "|")
        self.assertEqual([piece.value for piece in parsed[3:]], [Decimal("3"), "=", Decimal("3")])

    def test_equation_has_variables_flag(self):
        equation = Equation("$name$ + 1", self.context)
        self.assertTrue(equation.has_variables())

    def test_equation_exposes_original_equation_and_context(self):
        equation = Equation("1 + 2", self.context)
        self.assertEqual(equation.equation, "1 + 2")
        self.assertIs(equation.context, self.context)

    def test_parser_rejects_unknown_symbol(self):
        with self.assertRaisesRegex(SyntaxParseError, "Unknown symbol 'unknown'"):
            self.parse_expression("unknown")

    def test_parser_rejects_missing_variable_closer(self):
        with self.assertRaisesRegex(SyntaxParseError, "Missing variable closer: '\\$'"):
            self.parse_expression("$name")

    def test_parser_rejects_missing_closing_parenthesis(self):
        with self.assertRaisesRegex(SyntaxParseError, "Missing closing parenthesis: '\\)'"):
            self.parse_expression("(1 + 2")

    def test_parser_rejects_implicit_expression_adjacency(self):
        with self.assertRaisesRegex(SyntaxParseError, "Missing operator between expressions"):
            self.parse_expression("1 2")

    def test_parser_rejects_unknown_character(self):
        with self.assertRaisesRegex(SyntaxParseError, "Unexpected character: '@'"):
            self.parse_expression("@")

    def test_parser_rejects_incomplete_expression_after_operator(self):
        with self.assertRaisesRegex(SyntaxParseError, "Incomplete expression after '\\+'"):
            self.parse_expression("1 +")

    def test_parser_rejects_missing_comparison_operator_in_boolean_param(self):
        self.install_functions(
            Function(
                "flag",
                parameters=Parameters((Parameter("condition", takes_boolean=True, required=True),)),
                action=lambda params: Decimal("1"),
            )
        )
        with self.assertRaisesRegex(SyntaxParseError, "Missing comparison operator"):
            self.parse_expression("flag(1)")

    def test_parser_rejects_incomplete_comparison(self):
        with self.assertRaisesRegex(SyntaxParseError, "Incomplete comparison after '<'"):
            self.parse_statement("1 <")

    def test_parser_rejects_missing_equal_after_bang_comparison(self):
        with self.assertRaisesRegex(SyntaxParseError, "Missing '='"):
            self.parse_statement("1 ! 2")

    def test_parser_rejects_incomplete_union(self):
        with self.assertRaisesRegex(SyntaxParseError, "Incomplete union after '&'"):
            self.parse_statement("1 < 2 &")

    def test_parser_rejects_missing_boolean_operator_between_statements(self):
        with self.assertRaisesRegex(SyntaxParseError, "Missing boolean operator between statements"):
            self.parse_statement("(1 < 2) (3 < 4)")

    def test_parser_rejects_missing_parameter_separator(self):
        self.install_functions(
            Function(
                "pair",
                parameters=Parameters((
                    Parameter("left", required=True),
                    Parameter("right", required=True),
                )),
                action=lambda params: Decimal("0"),
            )
        )
        with self.assertRaisesRegex(SyntaxParseError, "Missing parameter separator: ','"):
            self.parse_expression("pair(1 @)")

    def test_parser_rejects_too_many_parameters(self):
        self.install_functions(
            Function(
                "single",
                parameters=Parameters((Parameter("value", required=True),)),
                action=lambda params: Decimal("0"),
            )
        )
        with self.assertRaisesRegex(SyntaxParseError, "Too many parameters"):
            self.parse_expression("single(1, 2)")

    def test_parser_rejects_missing_required_function_parameter(self):
        self.install_functions(
            Function(
                "pair",
                parameters=Parameters((
                    Parameter("left", required=True),
                    Parameter("right", required=True),
                )),
                action=lambda params: Decimal("0"),
            )
        )
        with self.assertRaisesRegex(ParseError, "Parameter `right` is required"):
            self.parse_expression("pair(1)")


if __name__ == "__main__":
    unittest.main()
