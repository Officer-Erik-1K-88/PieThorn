from decimal import Decimal
from typing import Dict, List

from pythorn.collections.mapping import Pair
from pythorn.math.converter._consonant import Consonant
from pythorn.math.converter._prefix import NumPrefix, NumPrefixDict

VOWELS = ("a", "i", "o", "u", "e")

# Key numeric values and their corresponding English words (same order/casing as Java)
NUMBER_VALUES: List[Pair] = [
    Pair("Million", Decimal("1E6")),
    Pair("Thousand", Decimal("1E3")),
    Pair("Hundred", Decimal("100")),
    Pair("Ninety", Decimal("90")),
    Pair("Eighty", Decimal("80")),
    Pair("Seventy", Decimal("70")),
    Pair("Sixty", Decimal("60")),
    Pair("Fifty", Decimal("50")),
    Pair("Forty", Decimal("40")),
    Pair("Thirty", Decimal("30")),
    Pair("Twenty", Decimal("20")),
    Pair("Nineteen", Decimal("19")),
    Pair("Eighteen", Decimal("18")),
    Pair("Seventeen", Decimal("17")),
    Pair("Sixteen", Decimal("16")),
    Pair("Fifteen", Decimal("15")),
    Pair("Fourteen", Decimal("14")),
    Pair("Thirteen", Decimal("13")),
    Pair("Twelve", Decimal("12")),
    Pair("Eleven", Decimal("11")),
    Pair("Ten", Decimal("10")),
    Pair("Nine", Decimal("9")),
    Pair("Eight", Decimal("8")),
    Pair("Seven", Decimal("7")),
    Pair("Six", Decimal("6")),
    Pair("Five", Decimal("5")),
    Pair("Four", Decimal("4")),
    Pair("Three", Decimal("3")),
    Pair("Two", Decimal("2")),
    Pair("One", Decimal("1")),
]

# static caches
FOUND_NUMBERS: Dict[int, str] = {0: "Thousand", -1: "Hundred"}
FOUND_EXPONENTS: Dict[str, Decimal] = {"Thousand": Decimal("1E3"), "Hundred": Decimal("1E2")}

PREFIXES: NumPrefixDict = NumPrefixDict(
    NumPrefix(
        1, "Un", "Milli", []
    ),
    NumPrefix(
        2, "Duo", "Billi", []
    ),
    NumPrefix(
        3,
        "Tre",
        "Trilli",
        [
            Consonant('s', True),
            Consonant('x', True, 's')
        ]
    ),
    NumPrefix(
        4, "Quattuor", "Quadri", []
    ),
    NumPrefix(
        5, "Quin", "Quinti", []
    ),
    NumPrefix(
        6,
        "Se",
        "Sexti",
        [
            Consonant('s', True),
            Consonant('x', True)
        ]
    ),
    NumPrefix(
        7,
        "Septe",
        "Septi",
        [
            Consonant('m', True),
            Consonant('n', True)
        ]
    ),
    NumPrefix(
        8, "Octo", "Octi", []
    ),
    NumPrefix(
        9,
        "Nove",
        "Noni",
        [
            Consonant('m', True),
            Consonant('n', True)
        ]
    ),
     NumPrefix(
        10,
        "Deci",
        "",
        [
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        20,
        "Viginti",
        "",
        [
            Consonant('s', False),
            Consonant('m', False)
        ]
    ),
    NumPrefix(
        30,
        "Triginta",
        "",
        [
            Consonant('s', False),
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        40,
        "Quadraginta",
        "",
        [
            Consonant('s', False),
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        50,
        "Quinquaginta",
        "",
        [
            Consonant('s', False),
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        60,
        "Sexaginta",
        "",
        [
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        70,
        "Septuaginta",
        "",
        [
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        80,
        "Octoginta",
        "",
        [
            Consonant('x', False),
            Consonant('m', False)
        ]
    ),
    NumPrefix(
        90, "Nonaginta", "", []
    ),
    NumPrefix(
        100,
        "Centi",
        "",
            [
            Consonant('x', False),
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        200,
        "Ducenti",
        "",
        [
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        300,
        "Trecenti",
        "",
        [
            Consonant('s', False),
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        400,
        "Quadringenti",
        "",
        [
            Consonant('s', False),
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        500,
        "Quingenti",
        "",
        [
            Consonant('s', False),
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        600,
        "Sescenti",
        "",
        [
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        700,
        "Septingenti",
        "",
        [
            Consonant('n', False)
        ]
    ),
    NumPrefix(
        800,
        "Octingenti",
        "",
        [
            Consonant('x', False),
            Consonant('m', False)
        ]
    ),
    NumPrefix(
        900, "Nongenti", "", []
    ),
)
