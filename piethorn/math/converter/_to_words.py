from decimal import Decimal, ROUND_HALF_UP
from typing import List, Any

from ._to_number import convert_to_big
from ._handle import _fractional_part, _integral_part, _to_plain_string, localcontext, _exponent10
from ._cache import NUMBER_VALUES
from ._num_name import _find_decimal_name, find_number_name_from_value
from ...collections.mapping import Pair


def _convert_to_words_rec(n: Decimal, values: List[Pair]) -> str:
    """
    Recursive integer-to-words conversion for whole numbers.

    Java method: `convertToWordsRec(BigDecimal n, ArrayList<Pair> values)`.

    This decomposes a non-negative integer using the `values` table which
    contains magnitudes like Octillion, Million, Thousand, Hundred, etc.
    The recursion order is critical for matching Java spacing/capitalization.
    """
    res = ""

    if n < values[0].value:
        for pair in values:
            value = pair.value
            word = pair.key
            if n >= value:
                # Java only appends quotient part when n >= 100
                if n >= Decimal(100):
                    res += _convert_to_words_rec(n / value, values) + " "
                res += word
                rem = n % value
                if rem > 0:
                    res += " " + _convert_to_words_rec(rem, values)
                return res
    else:
        val = find_number_name_from_value(n)
        word = val.key
        value = val.value
        if n >= value:
            if n >= Decimal(100):
                res += _convert_to_words_rec(n / value, values) + " "
            res += word
            rem = n % value
            if rem > 0:
                res += " " + _convert_to_words_rec(rem, values)
            return res

    return res

def _convert_to_words_decimal(n: Decimal) -> str:
    """
    Convert a Decimal into words (Java private `convertToWords(BigDecimal)`).

    Produces title-cased English words and uses Java's "and <fraction> <ordinal>"
    format for decimals (e.g., "One and Two Tenths"). Negative values are
    prefixed with "Negative".
    """
    if n == 0:
        return "Zero"

    is_negative = (n.copy_abs() != n)
    n = n.copy_abs()

    top = _integral_part(n)
    bottom = _fractional_part(n)

    if bottom == 0:
        ret = _convert_to_words_rec(n, NUMBER_VALUES)
    else:
        size = Decimal(1)
        while _fractional_part(bottom) != 0:
            bottom *= Decimal(10)
            size *= Decimal(10)

        end = _find_decimal_name(size, None)
        first_part = _convert_to_words_rec(top, NUMBER_VALUES)
        second_part = _convert_to_words_rec(bottom, NUMBER_VALUES)

        if first_part == "":
            first_part = "Zero"

        ret = f"{first_part} and {second_part} {end}"

    if is_negative:
        ret = "Negative " + ret
    return ret

def convert_to_words(number: Any) -> str:
    """
    Public entry point: convert a number into English words.

    Java method: `convertToWords(Object n)`.

    Accepts multiple input types (Decimal, int/float, strings, collections, etc.)
    and applies the same coercion rules as Java, then delegates to the internal
    Decimal implementation.
    """
    ret = _convert_to_words_decimal(convert_to_big(number))
    return " ".join(ret.split())  # Java: replaceAll(" +", " ")

def convert_partial_word(number: Any, places_before_word: int = 0, round_to: int = 2 ** 31 - 1) -> str:
    """
    Convert a number into words but optionally truncate/round its magnitude.

    Java method: `convertPartialWord(BigDecimal n, int placesBeforeWord, int roundTo)`.

    This is used to express a number using a shorter word scale (e.g., "12.3 Million")
    by shifting the decimal point before converting. The output formatting and
    rounding behavior matches Java (including 'plain string' rendering).
    """
    if places_before_word <= 1:
        places_before_word = 0
    else:
        places_before_word *= 2
        places_before_word -= 1

    n = convert_to_big(number)
    exponent = _exponent10(n)
    end = ""

    if places_before_word < exponent:
        pair = find_number_name_from_value(Decimal(f"1E{exponent - places_before_word}"))
        if pair.value > Decimal("100"):
            n = n / pair.value
            end = " " + pair.key

        string = _to_plain_string(n)

        if "." in string:
            index = string.find(".")
            end_index = index + places_before_word
            if end_index >= len(string):
                return string + end
            if string[end_index] == ".":
                end_index += 1
            else:
                end_index += 1

            if _fractional_part(n) == 0:
                count = len(string) - end_index
                string = string[: end_index - 1]
                return string + ("0" * count)

            return string[:end_index] + end

        return string + end

    if round_to != 2 ** 31 - 1:
        round_to += len(_to_plain_string(_integral_part(n)).replace("-", ""))

    with localcontext() as ctx:
        ctx.prec = round_to
        ctx.rounding = ROUND_HALF_UP
        rounded = +n
    return _to_plain_string(rounded) + end