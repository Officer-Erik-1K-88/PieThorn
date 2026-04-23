import random
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from piethorn.math import LogicGates, skew
from piethorn.math.converter import (
    convert_partial_word,
    convert_to_big,
    convert_to_number,
    convert_to_words,
    letter_to_number,
)
from piethorn.math.converter.timing import convert_seconds, convert_to_utc, format_time


class LogicAndRandomTests(unittest.TestCase):
    def test_logic_gates_support_scalar_and_iterable_inputs(self):
        gates = LogicGates()
        reverse = LogicGates(reverse=True)

        self.assertTrue(gates.and_gate([True, 1, True]))
        self.assertTrue(gates.or_gate(False, 1))
        self.assertEqual(gates.not_gate([True, False, 1]), [False, True, False])
        self.assertTrue(gates.nand_gate(True, False))
        self.assertFalse(gates.nor_gate(False, 1))
        self.assertTrue(gates.xor_gate(False, 1))
        self.assertFalse(gates.xnor_gate(False, 1))
        self.assertFalse(reverse.truthy)
        self.assertTrue(reverse.falsy)

    def test_skew_respects_range_and_validation(self):
        random.seed(0)
        value = skew(skew_at=0.4, weight=0.2, minimum=10, maximum=20, is_int=True)

        self.assertGreaterEqual(value, 10)
        self.assertLessEqual(value, 20)

        with self.assertRaisesRegex(ValueError, "skew_at"):
            skew(skew_at=2)


class ConverterTests(unittest.TestCase):
    def test_converter_round_trips_common_values_and_partial_words(self):
        self.assertEqual(convert_to_words(0), "Zero")
        self.assertEqual(convert_to_words(Decimal("12.5")), "Twelve and Five Tenth")
        self.assertEqual(convert_to_number("12.5"), Decimal("12.5"))
        self.assertEqual(convert_to_number("Twelve"), Decimal("12"))
        self.assertEqual(convert_to_number("Two Thousand Three"), Decimal("2003"))
        self.assertEqual(convert_partial_word(1234567, 2, 4), "1234.567 Thousand")

    def test_convert_to_big_handles_multiple_input_shapes(self):
        self.assertEqual(convert_to_big(True), Decimal("1"))
        self.assertEqual(convert_to_big([1, 2, 3]), Decimal("2"))
        self.assertEqual(convert_to_big({"a": 2, "b": 4}), Decimal("2.0"))
        self.assertEqual(convert_to_big("abc"), Decimal("1"))
        self.assertEqual(convert_to_big("1+2i"), Decimal(hash(complex("1+2j"))))

    def test_letter_to_number_is_deterministic_with_seed(self):
        random.seed(0)
        self.assertEqual(letter_to_number("Hello", 100), "83110")


class TimingTests(unittest.TestCase):
    def test_format_time_and_convert_seconds_cover_structured_output(self):
        self.assertEqual(
            format_time(2024, 1, 2, 3, 4, 5, 6, 7, 8, "UTC"),
            "2024-01-02  03:04:05 . 6;7;8  UTC",
        )
        self.assertEqual(
            convert_seconds(3661.25, formatted=False),
            {
                "years": 0,
                "months": 0,
                "days": 0,
                "hours": 1,
                "minutes": 1,
                "seconds": 1,
                "milliseconds": 250,
                "microseconds": 0,
                "nanoseconds": 0.0,
            },
        )
        self.assertEqual(convert_seconds(3661.25, formatted=True, f_nano=False), "0000-00-00  01:01:01 ; 250")

    def test_convert_to_utc_handles_numeric_datetime_and_string_inputs(self):
        epoch = "1970-01-01  00:00:00  UTC"

        self.assertEqual(convert_to_utc(0, "sec"), epoch)
        self.assertEqual(convert_to_utc(datetime(1970, 1, 1, tzinfo=timezone.utc)), epoch)
        self.assertEqual(convert_to_utc("1970-01-01T00:00:00+00:00"), epoch)

        with self.assertRaisesRegex(TypeError, "Unsupported time format"):
            convert_to_utc(object())


if __name__ == "__main__":
    unittest.main()
