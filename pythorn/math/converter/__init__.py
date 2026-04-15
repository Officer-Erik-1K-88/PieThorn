"""
pythorn.math.converter

One-to-one Python port of the Java `cache` utility.

This module intentionally preserves Java behavior, including:
- Naming quirks
- Edge cases
- Large-number Latin prefix rules
- Fraction handling semantics

This module intentionally preserves the Java behavior so outputs and parsing
round-trip the same way.

Notable behaviors preserved from Java:
- Fractions are expressed using "and" + an ordinal place name
  (e.g., 0.25 -> "Zero and Twenty Five Hundredth").
- Large-number names are generated using the same Latin-prefix construction.
- `convert_partial_word()` returns a numeric string followed by a scale word,
  matching Java's formatting logic.

Public API (mirrors Java, with snake_case aliases):
- find_number_name(exponent: int) -> str
- find_number_name_from_value(number: Decimal) -> Pair[str, Decimal]
- convert_to_words(number: Any) -> str
- convert_partial_word(number: Any, places_before_word: int = 0, round_to: int = 2**31-1) -> str
- convert_to_number(number_words: str) -> Decimal
- convert_to_big(number: Any) -> Decimal
"""
import random

from ._num_name import find_number_name_from_value, find_number_name

from ._to_number import convert_to_number, convert_to_big

from ._to_words import convert_to_words, convert_partial_word

__all__ = [
    "find_number_name",
    "find_number_name_from_value",
    "convert_to_words",
    "convert_partial_word",
    "convert_to_number",
    "convert_to_big",
    "letter_to_number",
]

def letter_to_number(sentence: str, percent_to_convert: float=-1.0):
    """
    Randomly replace mapped letters in a sentence with lookalike digits.

    If ``percent_to_convert`` is less than zero or greater than 100,
    then will generate a randomly skewed percent using ``percent_to_convert``
    as a hint with an upper modifier of 91 and lower modifier of 5.

    :param sentence: Sentence to convert.
    :param percent_to_convert: The amount of ``sentence`` to convert.
    """

    char_lists = [
        ['o', 'u', 'D', '@', '(', ')', '.', ',',],
        ['i', 'l', 'j', '!', '|', '\\', '/', ':', ';',],
        ['z', 'r', 'n', '^', '=', '<', '>',],
        ['e', 'c', 'm', 'w',],
        ['a', 'd', 'f', '#', '+',],
        ['s', 'v', 'k', '$', '?',],
        ['b', 'g', '%', '[', ']',],
        ['t', 'y', 'x', '{', '}',],
        ['h', 'q', 'B', '&',],
        ['p', '*', '`', '\'', '"',],
    ]
    def get_number(c: str):
        index = 0
        for char_list in char_lists:
            if c in char_list or c.lower() in char_list:
                return str(index)
            index += 1
        return c

    pave_chars: list[str] = []
    letters: dict[str, list[int]] = {}
    total = 0
    i = 0

    for char in sentence:
        if get_number(char) != char:
            total += 1
            if char not in pave_chars[0]:
                pave_chars.append(char)
                letters[char] = [i]
            else:
                letters[char].append(i)
        i += 1

    if percent_to_convert < 0 or percent_to_convert > 100:
        # Generate a skewed random percentage if percent is out of range
        max_perc: float = min(max(abs(91 + percent_to_convert), 0), 100)
        min_perc: float = min(max(abs(percent_to_convert - 5), 0), 100)
        if min_perc >= max_perc:
            if max_perc == min_perc:
                min_perc = max_perc / 2
            else:
                min_perc = (max_perc + min_perc) / 2
        percent_to_convert = min(max(random.betavariate(2.5, 4) * max_perc, min_perc), max_perc)
    chars_to_convert = int((percent_to_convert / 100) * total)

    to_convert: list[int] = []
    while len(to_convert) != chars_to_convert:
        key = random.choice(pave_chars)
        if len(letters[key]) == 0:
            pave_chars.remove(key)
        else:
            value = random.choice(letters[key])
            letters[key].remove(value)
            to_convert.append(value)
            total -= 1

    sentence_list = list(sentence)
    for i in to_convert:
        s = sentence_list[i]
        sentence_list[i] = get_number(s)

    return "".join(sentence_list)