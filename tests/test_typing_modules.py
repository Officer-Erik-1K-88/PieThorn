import inspect
import unittest

from piethorn.typing.argument import Argument as TypedArgument
from piethorn.typing.argument import ArgumentKind, Arguments as TypedArguments
from piethorn.typing.analyze import Argument, Arguments, analyze
from piethorn.typing.flag import SetBool


def sample_signature(a, /, b: int, *args, c=3, **kwargs) -> str:
    return "ok"


class ArgumentModuleTests(unittest.TestCase):
    def test_argument_kind_and_argument_validation(self):
        positional = TypedArgument("count", int, default=1)
        variadic_kwargs = TypedArgument("options", int, kind=ArgumentKind.VAR_KEYWORD)

        self.assertEqual(
            ArgumentKind.from_param_kind(inspect.Parameter.KEYWORD_ONLY),
            ArgumentKind.KEYWORD_ONLY,
        )
        self.assertTrue(positional.has_default)
        self.assertEqual(positional.value, 1)
        self.assertEqual(positional.set(5), 1)
        self.assertEqual(positional.value, 5)
        variadic_kwargs.set(7, key="alpha")
        self.assertEqual(variadic_kwargs.value["alpha"], 7)
        self.assertEqual(positional.copy().key, "count")

        with self.assertRaisesRegex(TypeError, "Type mismatch"):
            positional.set("bad")

    def test_arguments_container_handles_dynamic_keys_defaults_and_removal(self):
        arguments = TypedArguments(
            TypedArgument("count", int, default=1),
            strict_keys=False,
        )

        self.assertTrue(arguments.validate("count", 2))
        self.assertEqual(arguments.set("name", "erik"), inspect.Parameter.empty)
        arguments.ensure_defaults(extra=2)
        self.assertEqual(arguments["count"], 1)
        self.assertEqual(arguments["name"], "erik")
        self.assertEqual(arguments["extra"], 2)
        self.assertEqual(list(arguments.iter_positionals()), ["count", "name", "extra"])
        removed = arguments.remove("name")
        self.assertEqual(removed.key, "name")
        self.assertNotIn("name", arguments)


class AnalyzeModuleTests(unittest.TestCase):
    def test_analyze_argument_and_arguments_reflect_signature(self):
        info = analyze(sample_signature)
        first_param = next(iter(inspect.signature(sample_signature).parameters.values()))
        wrapped = Argument(first_param)
        sliced = info.arguments[1:]

        self.assertTrue(info.callable())
        self.assertTrue(info.isfunction())
        self.assertEqual(info.return_annotation, str)
        self.assertEqual(info.arguments.positional, ("a",))
        self.assertEqual(info.arguments.positional_or_keyword, ("b",))
        self.assertEqual(info.arguments.keyword, ("c",))
        self.assertTrue(info.arguments.has_args)
        self.assertTrue(info.arguments.has_kwargs)
        self.assertEqual(info.arguments.arg_count, 2)
        self.assertEqual(str(wrapped), "a")
        self.assertEqual(repr(wrapped), '<Argument "a">')
        self.assertEqual(wrapped, first_param)
        self.assertIsInstance(sliced, Arguments)
        self.assertEqual(len(sliced), 4)

    def test_analyze_arguments_reject_invalid_iterable_members(self):
        with self.assertRaisesRegex(TypeError, "inspect.Parameter or Argument"):
            Arguments([object()])

class FlagModuleTests(unittest.TestCase):
    def test_set_bool_change_honors_and_or_modes(self):
        and_mode = SetBool(False, default=True, start_set=True)
        and_mode.change(SetBool(True, default=True, start_set=True))

        or_mode = SetBool(False, default=False, and_change=False, start_set=True)
        or_mode.change(SetBool(True, default=False, start_set=True))

        self.assertFalse(and_mode)
        self.assertTrue(or_mode)


if __name__ == "__main__":
    unittest.main()
