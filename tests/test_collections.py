import unittest
from decimal import Decimal

from piethorn.collections.char import Char, CharIterator, CharSequence
from piethorn.collections.mapping import Map
from piethorn.collections.range import (
    SliceComposeResult,
    SliceMode,
    adhoc_combine_slices,
    combine_slices,
    is_full_slice,
    slice_len,
)
from piethorn.collections.views import MapView, SequenceView


class CharTests(unittest.TestCase):
    def test_char_normalizes_inputs_and_supports_comparisons(self):
        self.assertEqual(Char(Char("A")).ord(), 65)
        self.assertEqual(Char(65).char(), "A")
        self.assertTrue(Char("").is_empty())
        self.assertTrue(Char("A") == "A")
        self.assertTrue(Char("A") < "B")
        self.assertTrue(Char("A") > 32)
        self.assertEqual(Char("A").lower(), Char("a"))
        self.assertEqual(Char("a").upper(), Char("A"))

    def test_char_rejects_multi_character_string(self):
        with self.assertRaisesRegex(ValueError, "single character"):
            Char("ab")

    def test_char_sequence_normalizes_flattening_and_sequence_operations(self):
        sequence = CharSequence(["ab", " ", "C"])

        self.assertEqual(str(sequence), "ab C")
        self.assertEqual(sequence[0], Char("a"))
        self.assertEqual(str(sequence[1:]), "b C")
        self.assertEqual(str(sequence + CharSequence("!")), "ab C!")
        self.assertEqual(str(sequence * 2), "ab Cab C")
        self.assertFalse(sequence.isalpha())
        self.assertTrue(CharSequence("123").isdigit())

    def test_char_iterator_supports_peek_eat_and_remaining_iteration(self):
        iterator = CharIterator(["", " ", "a", "b"], skip_space=True, skip_empty=True)

        self.assertEqual(iterator.peek(), Char("a"))
        self.assertTrue(iterator.eat("a"))
        self.assertEqual(next(iterator), Char("b"))
        self.assertTrue(iterator.next_ended())

        seen = []
        second = CharIterator("xyz")
        second.for_remaining(lambda char: seen.append(str(char)) or False)
        self.assertEqual(seen, ["x", "y", "z"])


class MappingAndRangeTests(unittest.TestCase):
    def test_map_behaves_like_an_ordered_mutable_mapping(self):
        mapping = Map(["a", "b"], [1, 2])
        mapping["a"] = 3
        mapping["c"] = 4

        self.assertEqual(mapping["a"], 3)
        self.assertEqual(mapping.key_index("c"), 2)
        self.assertEqual(mapping.value_index(2), 1)
        self.assertEqual(mapping.key_at_index(0), "a")
        self.assertEqual(mapping.value_at_index(2), 4)
        self.assertTrue(mapping.has_key("b"))
        self.assertTrue(mapping.has_value(4))
        self.assertEqual(list(mapping), ["a", "b", "c"])
        self.assertEqual(list(reversed(mapping)), ["c", "b", "a"])
        self.assertEqual(mapping, {"a": 3, "b": 2, "c": 4})

        del mapping["b"]
        self.assertNotIn("b", mapping)

    def test_map_validates_parallel_sequences(self):
        with self.assertRaisesRegex(ValueError, "Both keys and values must be None or a sequence"):
            Map(["a"], None)
        with self.assertRaisesRegex(ValueError, "same length"):
            Map(["a"], [1, 2])

    def test_slice_helpers_cover_exact_and_heuristic_composition(self):
        self.assertEqual(combine_slices(slice(2, 10, 2), slice(1, 3), 20), slice(4, 8, 2))
        self.assertTrue(is_full_slice(slice(None, None)))
        self.assertEqual(slice_len(slice(1, 8, 2), 10), 4)
        self.assertEqual(SliceMode.classify(slice(1, 3)), SliceMode.POSITIVE)

        exact = adhoc_combine_slices(slice(None, None, 2), slice(1, 4))
        heuristic = adhoc_combine_slices(slice(5, None, 2), slice(1, None))

        self.assertIsInstance(exact, SliceComposeResult)
        self.assertEqual(exact.slice, slice(2, 8, 2))
        self.assertTrue(exact.exact)
        self.assertEqual(heuristic.slice, slice(7, None, 2))
        self.assertFalse(heuristic.exact)


class ViewTests(unittest.TestCase):
    def test_sequence_view_supports_reverse_cut_and_nested_slices(self):
        view = SequenceView([1, 2, 3, 4], reverse=True, cut=slice(1, 4))
        nested = view[1:]

        self.assertEqual(list(view), [4, 3, 2])
        self.assertEqual(view[1], 3)
        self.assertEqual(list(nested), [3, 2])
        self.assertIs(nested.parent, view)
        self.assertTrue(view.has_parent is False)
        self.assertEqual(list(reversed(view)), [2, 3, 4])
        self.assertEqual(len(view), 3)
        self.assertIn(3, view)
        self.assertEqual(view.count(2), 1)
        self.assertEqual(view.index(3), 1)

    def test_map_view_exposes_read_only_mapping_interface(self):
        view = MapView({"left": Decimal("1"), "right": Decimal("2")})

        self.assertEqual(view["left"], Decimal("1"))
        self.assertEqual(view.get("missing", 5), 5)
        self.assertEqual(list(view), ["left", "right"])
        self.assertIn("right", view)
        self.assertEqual(view, {"left": Decimal("1"), "right": Decimal("2")})


if __name__ == "__main__":
    unittest.main()
