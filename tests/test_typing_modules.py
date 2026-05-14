import builtins
import inspect
import unittest
from collections import abc as collections_abc
from typing import Callable, Iterable, Literal, Mapping, Sequence

from piethorn.typing.argument import Argument as TypedArgument
from piethorn.typing.argument import ArgumentKind, Arguments as TypedArguments
from piethorn.typing.analyze import Argument, Arguments, analyze
from piethorn.typing.checker import TYPES, TypeChecker, get_type_checker, type_check
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


class TypeCheckerModuleTests(unittest.TestCase):
    def setUp(self):
        self.old_types = TYPES.copy()
        TYPES[:] = [
            TypeChecker(int, origin_only=True),
            TypeChecker(str, origin_only=True),
            TypeChecker(bytes, origin_only=True),
            TypeChecker(tuple, tuple_like=True),
            TypeChecker(Mapping, map_like=True),
            TypeChecker(Sequence, sequence_like=True),
            TypeChecker(Iterable, iterable_like=True),
            TypeChecker(int | str, union_like=True),
            TypeChecker(Literal[1, 2], literal_like=True, allow_non_type_args=True),
            TypeChecker(Callable, callable_like=True, allow_non_type_args=True),
        ]

    def tearDown(self):
        TYPES[:] = self.old_types

    def test_check_hint_matches_generic_arguments(self):
        checker = TypeChecker(list[int], sequence_like=True)

        self.assertTrue(checker.check_hint(list[int]))
        self.assertFalse(checker.check_hint(list[str]))

    def test_check_value_uses_value_checks_for_generic_arguments(self):
        checker = TypeChecker(list[int], sequence_like=True)

        self.assertTrue(checker.check_value([1]))
        self.assertFalse(checker.check_value(["bad"]))

    def test_default_registry_covers_builtin_types(self):
        TYPES[:] = self.old_types
        registered_hints = {type_checker.info.hint for type_checker in TYPES}
        builtin_types = {
            type_obj
            for name, type_obj in vars(builtins).items()
            if isinstance(type_obj, type) and name != "__loader__"
        }
        collection_builtins = {
            type_obj
            for type_obj in builtin_types
            if (
                    issubclass(type_obj, collections_abc.Mapping)
                    or (
                            issubclass(type_obj, collections_abc.Sequence)
                            and type_obj not in (str, bytes, bytearray, tuple)
                    )
                    or (
                            issubclass(type_obj, collections_abc.Iterable)
                            and type_obj not in (str, bytes, bytearray, tuple)
                    )
            )
        }

        self.assertTrue(all(get_type_checker(type_obj, None) for type_obj in builtin_types))
        self.assertTrue(collection_builtins.isdisjoint(registered_hints))
        self.assertTrue(type_check([1, 2], list[int]))
        self.assertFalse(type_check([1, "bad"], list[int]))
        self.assertTrue(type_check({"a": 1}, dict[str, int]))
        self.assertFalse(type_check({"a": "bad"}, dict[str, int]))
        self.assertTrue(type_check({1, 2}, set[int]))
        self.assertTrue(type_check(frozenset({1, 2}), frozenset[int]))
        self.assertTrue(type_check(range(3), range))

    def test_check_hint_compares_nested_hints(self):
        checker = TypeChecker(list[dict[str, int]], sequence_like=True)

        self.assertTrue(checker.check_hint(list[dict[str, int]]))
        self.assertFalse(checker.check_hint(list[dict[str, str]]))

    def test_check_hint_supports_collection_like_forms(self):
        self.assertTrue(TypeChecker(dict[str, int], map_like=True).check_hint(dict[str, int]))
        self.assertFalse(TypeChecker(dict[str, int], map_like=True).check_hint(dict[str, str]))
        self.assertTrue(TypeChecker(tuple[int, str], tuple_like=True).check_hint(tuple[int, str]))
        self.assertFalse(TypeChecker(tuple[int, str], tuple_like=True).check_hint(tuple[int, int]))

    def test_check_hint_supports_union_literal_and_callable_forms(self):
        self.assertTrue(TypeChecker(int | str, union_like=True).check_hint(str | int))
        self.assertFalse(TypeChecker(int | str, union_like=True).check_hint(int | bytes))
        self.assertTrue(
            TypeChecker(
                Literal[1, 2],
                literal_like=True,
                allow_non_type_args=True,
            ).check_hint(Literal[2, 1])
        )
        self.assertFalse(
            TypeChecker(
                Literal[1, 2],
                literal_like=True,
                allow_non_type_args=True,
            ).check_hint(Literal[1, 3])
        )
        self.assertTrue(
            TypeChecker(
                Callable[[int], str],
                callable_like=True,
                allow_non_type_args=True,
            )
            .check_hint(Callable[[int], str])
        )
        self.assertFalse(
            TypeChecker(
                Callable[[int], str],
                callable_like=True,
                allow_non_type_args=True,
            )
            .check_hint(Callable[[str], str])
        )


if __name__ == "__main__":
    unittest.main()
