"""
NumberConvert.py

One-to-one Python port of the Java `NumberConvert` utility.

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
- NumberConvert.find_number_name(exponent: int) -> str
- NumberConvert.find_number_name_from_value(number: Decimal) -> Pair[str, Decimal]
- NumberConvert.convert_to_words(number: Any) -> str
- NumberConvert.convert_partial_word(number: Any, places_before_word: int = 0, round_to: int = 2**31-1) -> str
- NumberConvert.convert_to_number(number_words: str) -> Decimal
- NumberConvert.convert_to_big(number: Any) -> Decimal
"""
from dataclasses import dataclass
from decimal import Decimal, getcontext, localcontext, ROUND_HALF_UP, InvalidOperation
from typing import Any, Dict, Iterable, Iterator, List, Tuple, Mapping, AbstractSet, Hashable, Callable

# --- Java MathContext(2448) equivalent ---
JAVA_CONTEXT_PREC = 2448
getcontext().prec = JAVA_CONTEXT_PREC


@dataclass(frozen=True)
class Pair:
    """
    Lightweight (name, value) holder used to keep word->number pairs.
    
    This mirrors the tiny Java helper class used throughout the original
    implementation, primarily for the fixed English word tables (ones, tens,
    hundreds, etc.).
    """
    key: Any
    value: Any


class Consonant:
    def __init__(self, converts: str, trails: bool, to: str=None):
        """
        This is the suffix of a ``NumberPrefix``.
        It helps add depth and variety to number words.

        :param converts: The consonant that this class represents
        :param trails: Whether this consonant is appended to the end of a ``NumberPrefix`` or if it decides the consonant of the previous ``NumberPrefix``
        :param to: The consonant that is appended to the end of a ``NumberPrefix``. Defaults to ``converts``.
        """
        self._converts = converts
        self._trails = trails
        self._to = to

    @property
    def converts(self):
        """ The consonant that this class represents """
        return self._converts

    @property
    def trails(self):
        """
        If ``True``, then this defines that the ``NumberPrefix`` gains this consonant
        when placed before a ``NumberPrefix`` that defines the same consonant.
        While, if ``False``, then this defines that the ``NumberPrefix`` tells the previous
        ``NumberPrefix`` should gain this consonant if it defines the same consonant and
        has ``trails`` set to ``True``.
        """
        return self._trails

    @property
    def to(self):
        """ The actual consonant that is appended to the end of a ``NumberPrefix`` """
        if self._to is None:
            return self._converts
        return self._to

    def __eq__(self, other):
        if isinstance(other, Consonant):
            return self._converts == other._converts
        elif isinstance(other, str):
            return self._converts == other
        return False


class Consonants(AbstractSet[Consonant]):
    """
    A Set of ``Consonant`` classes.
    """
    def __init__(self, consonants: Iterable[Consonant]):
        self._consonants = {}
        self._length = 0
        for consonant in consonants:
            if consonant.converts not in self._consonants:
                self._consonants[consonant.converts] = consonant
                self._length += 1

    def __len__(self):
        return self._length

    def __iter__(self):
        for conv in self._consonants:
            yield self._consonants[conv]

    def __contains__(self, x):
        if isinstance(x, Consonant):
            check_for = x.converts
        else:
            check_for = x
        return check_for in self._consonants


class NumPrefix:
    def __init__(
            self,
            num: int,
            prefix: str,
            convert: str,
            consonants: Iterable[Consonant],
    ):
        """
        Defines a part of a number word.

        :param num: The number that the prefix represents
        :param prefix: The prefix being represented
        :param convert: The second prefix that can be used. Defaults to ``prefix``
        :param consonants: The optional suffixes to this prefix. This is also used to check if the previous ``NumberPrefix`` should use one of its consonants.
        """
        self._num = num
        self._prefix = prefix
        self._convert = convert
        self._consonants = Consonants(consonants)

    @property
    def place(self):
        """ The digits place that this prefix is in """
        if self._num < 10:
            return "units"
        elif self._num < 100:
            return "tens"
        elif self._num < 1000:
            return "hundreds"
        elif self._num < 10000:
            return "thousands"
        else:
            return "unknown"

    @property
    def prefix(self):
        """ The actual prefix that this prefix is """
        return self._prefix

    @property
    def convert(self):
        """ A second prefix that this prefix can be """
        if self._convert is None or self._convert == "":
            return self._prefix
        return self._convert

    @property
    def num(self):
        """ The number this prefix represents """
        return self._num

    @property
    def consonants(self):
        """
        The consonants that this prefix uses.

        Refer to ``Consonant`` class for details on how consonants work.
        """
        return self._consonants


class NumPrefixDict(Mapping[int, NumPrefix]):
    """
    Maps out a set of ``NumPrefix`` classes.
    """
    def __init__(self, *args: NumPrefix):
        self._prefixes: Dict[int, NumPrefix] = {}
        self._places: set[str] = set()
        if len(args) != 0:
            self._add_all(args)

    def __len__(self):
        return len(self._prefixes)

    def __iter__(self):
        return iter(self._prefixes)

    def __getitem__(self, item):
        return self._prefixes[item]

    @property
    def place_count(self):
        return len(self._places)

    def has_place(self, place: str):
        return place in self._places

    def _add(self, prefix: NumPrefix):
        index = prefix.num
        self._places.add(prefix.place)
        self._prefixes[index] = prefix

    def _add_all(self, prefixes: Iterable[NumPrefix]):
        for prefix in prefixes:
            self._add(prefix)


def _to_plain_string(d: Decimal) -> str:
    """
    Return a non-scientific string for a Decimal.
    
    Java's BigDecimal uses `toPlainString()` in several spots. Python's `Decimal`
    can render using exponent notation depending on context; this helper forces
    a plain, non-exponent representation to keep output identical.
    """
    # format(..., 'f') forces fixed-point without exponent.
    # It will include trailing zeros if they are part of the Decimal's exponent.
    return format(d, "f")


def _exponent10(x: Decimal) -> int:
    """
    Return base-10 exponent information for a Decimal-like value.
    
    Used to emulate Java BigDecimal scale/precision logic when deciding how to
    name very large/small magnitudes.
    """
    if x.is_zero():
        return 0
    return x.copy_abs().adjusted()


def _integral_part(x: Decimal) -> Decimal:
    """
    Equivalent to BigDecimalMath.integralPart(x) in the Java version.
    """
    return x.to_integral_value(rounding="ROUND_DOWN")


def _fractional_part(x: Decimal) -> Decimal:
    """
    Equivalent to BigDecimalMath.fractionalPart(x) in the Java version.
    """
    return x - _integral_part(x)


class NumberConvert:
    """
    Namespace-style class implementing Java `NumberConvert`.
    
    The goal of this port is fidelity: method names, outputs, and edge cases are
    kept aligned with the Java source. Prefer changing the Java and re-porting
    over "cleaning up" the Python implementation.
    """

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

    # Java static caches
    FOUND_NUMBERS: Dict[int, str] = {0: "Thousand", -1: "Hundred"}
    FOUND_EXPONENTS: Dict[str, Decimal] = {"Thousand": Decimal("1E3"), "Hundred": Decimal("1E2")}

    prefixes: NumPrefixDict = NumPrefixDict(
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

    @staticmethod
    def _check_atnn_rem(value: str, ending: bool) -> bool:
        """
        Port of Java `checkATNNRem`.
        
        This is part of the large-number naming algorithm: it decides whether a given
        counter segment should append `nilli` vs `illi`, matching Java's internal
        rules for the -illion family name construction.
        """
        val = value.lower()
        for check in NumberConvert.VOWELS:
            if ending:
                if val.endswith(check):
                    return True
            else:
                if val.startswith(check):
                    return True
        return False

    @staticmethod
    def _append_to_number_name(name: List[str], to_add: str) -> None:
        """
        Append a prefix chunk to the mutable name buffer (Java parity).
        
        Java builds names by pushing fragments into an ArrayList and then joining.
        This helper reproduces the same "replace last element if empty/compatible"
        behavior to preserve subtle output differences.
        """
        if not to_add:
            return
        if name:
            current = "".join(name)
            if NumberConvert._check_atnn_rem(current, True) and NumberConvert._check_atnn_rem(to_add, False):
                current = current[:-1]
                name.clear()
                name.append(current)
        name.append(to_add)

    @staticmethod
    def _get_numbers_name(exponent: int) -> str:
        """
        Build or fetch the English name for a power of ten (divisible by 3).
        
        Java method: `getNumbersName(int exponent)`
        
        Parameters
        ----------
        exponent:
            The exponent in 10^exponent. The Java code expects this to be a multiple
            of 3 (thousand-group boundary).
        
        Returns
        -------
        str
            Title-cased scale name such as "Thousand", "Million", "Billion", ...
            including algorithmically generated names beyond the built-in cache.
        
        Notes
        -----
        This function is intentionally complex: it implements the Java Latin-prefix
        algorithm (units/tens/hundreds segments) plus several special-case rules:
        - group 1..9 remap (Milli/Billi/Trilli/Quadri/Quinti/Sexti/Septi/Octi/Noni)
        - consonant insertion rules for Tre/Se and Septe/Nove
        - the `nilli`/`illi` selection logic via `_check_atnn_rem`
        """
        group = (exponent // 3) - 1

        if group in NumberConvert.FOUND_NUMBERS:
            return NumberConvert.FOUND_NUMBERS[group]


        # Split group into (unit, ten, hundred) digit triples, least-significant triple first.
        indexes: List[Tuple[int, ...]] = []
        build_top = group
        while build_top != 0:
            places: List[int] = []
            for i in range(NumberConvert.prefixes.place_count):
                if build_top < 10:
                    places.append(build_top)
                    build_top = 0
                    break
                else:
                    places.append(build_top % 10)
                    build_top = build_top // 10
            indexes.append(tuple(place_index*pow(10, i) for i, place_index in enumerate(places)))

        name_parts: List[str] = []
        counter = 0

        for tiers_i in reversed(indexes):
            tiers: List[NumPrefix] = []

            for i in tiers_i:
                # finds the prefixes
                if i > 0:
                    tiers.append(NumberConvert.prefixes[i])

            tier_count = len(tiers)
            if tier_count == 1:
                # Java special-case for a single "group" digit (Billion, Trillion, ...):
                # the unit prefixes become Milli/Billi/Trilli/... instead of Un/Duo/Tre/...
                NumberConvert._append_to_number_name(name_parts, tiers[0].convert)
            else:
                # Consonant insertion rules (Java parity): certain unit prefixes gain a
                # trailing consonant depending on the following tens/hundreds chunk.
                # This is why you see Tre->Tres/Tresx and Se->Ses/Sex in some names.
                # Java implements this via membership tests in the s/n/m/x lists.
                # Java consonant insertion rules for Tre/Se and Septe/Nove.
                for i, tier in enumerate(tiers):
                    string = tier.prefix
                    if i != tier_count - 1:
                        n_tier = tiers[i+1]
                        if len(tier.consonants) != 0 and len(n_tier.consonants) != 0:
                            for consonant in tier.consonants:
                                if consonant.trails and consonant in n_tier.consonants:
                                    string = string + consonant.to
                                    break
                    NumberConvert._append_to_number_name(name_parts, string)


            built = "".join(name_parts)
            if built and (counter > 0 or tier_count > 0):
                if len(indexes) == 1:
                    if not built.endswith("illi"):
                        NumberConvert._append_to_number_name(name_parts, "illi")
                else:
                    if NumberConvert._check_atnn_rem(built, True):
                        name_parts.append("nilli")
                    else:
                        name_parts.append("illi")

                if "".join(name_parts):
                    counter += 1

        name_parts.append("on")

        final_name = "".join(name_parts).lower()
        final_name = final_name[:1].upper() + final_name[1:]
        NumberConvert.FOUND_NUMBERS[group] = final_name
        NumberConvert.FOUND_EXPONENTS[final_name] = Decimal(f"1E{exponent}")
        return final_name

    @staticmethod
    def find_number_name(exponent: int) -> str:
        """
        Return the scale name for a base-10 exponent.
        
        Java method: `findNumberName(int exponent)`.
        
        This is a thin wrapper that normalizes the exponent to a thousand-group
        boundary and then delegates to `_get_numbers_name`.
        """
        if exponent % 3 != 0:
            raise RuntimeError("The exponent provided isn't dividable by 3.")
        word = NumberConvert._get_numbers_name(exponent)
        if word == "" or word == "On":
            raise RuntimeError("Couldn't find number's name from exponent.")
        return word

    @staticmethod
    def find_number_name_from_value(number: Decimal) -> Pair:
        """
        Return the scale name for a numeric value.
        
        Java method: `findNumberName(BigDecimal value)`.
        
        The value is converted to an exponent (base 10), rounded down to a multiple
        of 3, and mapped to a name (e.g., 1E6 -> "Million").
        """
        exponent = _exponent10(number)
        if exponent % 3 != 0:
            if (exponent - 1) % 3 != 0:
                if (exponent - 2) % 3 != 0:
                    raise RuntimeError(
                        "Unexpected outcome, couldn't find instance of 3 (going down) from " + str(exponent)
                    )
                exponent -= 2
            else:
                exponent -= 1
        val = Decimal(f"1E{exponent}")
        return Pair(NumberConvert.find_number_name(exponent), val)

    @staticmethod
    def _find_decimal_name(number: Decimal, placement: str | None) -> str:
        """
        Name the fractional denominator (tenths, hundredths, ...).
        
        Java private helper used by the word conversion when a Decimal has a
        fractional part. It selects the correct ordinal scale word based on the
        number of decimal places.
        """
        for nv in NumberConvert.NUMBER_VALUES:
            if number == nv.value:
                return f"{placement}-{nv.key}th" if placement is not None else f"{nv.key}th"

        try:
            exponent = _exponent10(number)
            if exponent % 3 != 0:
                if (exponent - 1) % 3 != 0:
                    if (exponent - 2) % 3 != 0:
                        raise RuntimeError(
                            "Unexpected outcome, couldn't find instance of 3 (going down) from " + str(exponent)
                        )
                    exponent -= 2
                else:
                    exponent -= 1

            val = NumberConvert.find_number_name(exponent)
            return f"{placement}-{val}th" if placement is not None else f"{val}th"
        except RuntimeError:
            pass

        if placement is None:
            return NumberConvert._find_decimal_name(number / Decimal(10), "ten")
        if placement == "ten":
            return NumberConvert._find_decimal_name(number / Decimal(10), "hundred")
        return ""

    @staticmethod
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
                        res += NumberConvert._convert_to_words_rec(n / value, values) + " "
                    res += word
                    rem = n % value
                    if rem > 0:
                        res += " " + NumberConvert._convert_to_words_rec(rem, values)
                    return res
        else:
            val = NumberConvert.find_number_name_from_value(n)
            word = val.key
            value = val.value
            if n >= value:
                if n >= Decimal(100):
                    res += NumberConvert._convert_to_words_rec(n / value, values) + " "
                res += word
                rem = n % value
                if rem > 0:
                    res += " " + NumberConvert._convert_to_words_rec(rem, values)
                return res

        return res

    @staticmethod
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
            ret = NumberConvert._convert_to_words_rec(n, NumberConvert.NUMBER_VALUES)
        else:
            size = Decimal(1)
            while _fractional_part(bottom) != 0:
                bottom *= Decimal(10)
                size *= Decimal(10)

            end = NumberConvert._find_decimal_name(size, None)
            first_part = NumberConvert._convert_to_words_rec(top, NumberConvert.NUMBER_VALUES)
            second_part = NumberConvert._convert_to_words_rec(bottom, NumberConvert.NUMBER_VALUES)

            if first_part == "":
                first_part = "Zero"

            ret = f"{first_part} and {second_part} {end}"

        if is_negative:
            ret = "Negative " + ret
        return ret

    @staticmethod
    def convert_to_words(number: Any) -> str:
        """
        Public entry point: convert a number into English words.
        
        Java method: `convertToWords(Object n)`.
        
        Accepts multiple input types (Decimal, int/float, strings, collections, etc.)
        and applies the same coercion rules as Java, then delegates to the internal
        Decimal implementation.
        """
        ret = NumberConvert._convert_to_words_decimal(NumberConvert.convert_to_big(number))
        return " ".join(ret.split())  # Java: replaceAll(" +", " ")

    @staticmethod
    def convert_partial_word(number: Any, places_before_word: int = 0, round_to: int = 2**31 - 1) -> str:
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

        n = NumberConvert.convert_to_big(number)
        exponent = _exponent10(n)
        end = ""

        if places_before_word < exponent:
            pair = NumberConvert.find_number_name_from_value(Decimal(f"1E{exponent - places_before_word}"))
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

        if round_to != 2**31 - 1:
            round_to += len(_to_plain_string(_integral_part(n)).replace("-", ""))

        with localcontext() as ctx:
            ctx.prec = round_to
            ctx.rounding = ROUND_HALF_UP
            rounded = +n
        return _to_plain_string(rounded) + end

    @staticmethod
    def convert_to_number(number_words: str) -> Decimal:
        """
        Parse English words back into a Decimal (Java `convertToNumber(String)`).
        
        This attempts direct numeric parsing first (Decimal(number_words)). If that
        fails, it tokenizes the English words and accumulates the numeric value using
        the same scale tables/caches that `convert_to_words` uses.
        """
        try:
            return Decimal(number_words)
        except InvalidOperation:
            pass

        # TODO: Make this method work even when word not found in FOUND_EXPONENTS.

        # Accumulation strategy (Java parity): we keep a rolling `current` group that
        # collects values below the next scale word (e.g., Hundred/Thousand/Million).
        # When a scale token is hit, `current` is multiplied and added to `out`, then reset.
        words = number_words.split(" ")
        is_negative = (words[0] == "Negative")

        # Java: special-case 2 tokens without "Negative"
        # If parsing fails, Java *silently* falls through to the word-parser.
        if (not is_negative) and len(words) == 2:
            try:
                numeric = Decimal(words[0])
                if words[1] in NumberConvert.FOUND_EXPONENTS:
                    return numeric * NumberConvert.FOUND_EXPONENTS[words[1]]
                else:
                    raise RuntimeError("Cannot process the provided String to a number.")
            except InvalidOperation:
                pass

        place: List[Tuple[int, str]] = []
        added: List[int] = []

        start_i = 0
        if is_negative:
            place.append((0, "-"))
            added.append(0)
            start_i = 1

        has_decimal = False
        decimal_words: List[str] = []

        # This mirrors Java's nested loop over NUMBER_VALUES then indices.
        for pair in NumberConvert.NUMBER_VALUES:
            for i in range(start_i, len(words)):
                word = words[i]
                if word == "and":
                    if not has_decimal:
                        has_decimal = True
                        # Java: decimalWords = Arrays.copyOfRange(words, i+1, words.length-1);
                        decimal_words = words[i + 1 : len(words) - 1]
                    continue

                if not has_decimal:
                    if word == pair.key and i not in added:
                        place.append((i, _to_plain_string(pair.value)))
                        added.append(i)
                else:
                    break

        integral_part_length = len(words)
        if has_decimal:
            integral_part_length -= len(decimal_words) + 2  # +2 for "and" and last ordinal word

        for i in range(0, integral_part_length):
            word = words[i]
            if i not in added and word in NumberConvert.FOUND_EXPONENTS:
                place.append((i, _to_plain_string(NumberConvert.FOUND_EXPONENTS[word])))
                added.append(i)

        if len(place) != integral_part_length:
            raise RuntimeError("Cannot process the provided String to a number.")

        ret = Decimal("0")
        place.sort(key=lambda kv: kv[0])
        if place and place[0][1] == "-":
            place = place[1:]

        prev = Decimal("0")
        is_start = True

        for _, val_str in place:
            value = Decimal(val_str)
            exponent = _exponent10(value)
            if (not is_start) and exponent >= 2:
                prev = prev * value
                if exponent >= 3:
                    ret = ret + prev
                    prev = Decimal("0")
                    is_start = True
            else:
                prev = prev + value
                is_start = False

        ret = ret + prev

        # Decimal part (matches Java exactly)
        if has_decimal and len(decimal_words) != 0:
            decimal = NumberConvert.convert_to_number(" ".join(decimal_words))
            placement = words[len(words) - 1]
            zero = ""
            placement = placement[: len(placement) - 2]  # remove "th"
            sepered = placement.split("-")
            if len(sepered) == 2:
                zero = sepered[0]
                placement = sepered[1]

            if (placement in NumberConvert.FOUND_EXPONENTS) or (placement == "Ten"):
                if placement == "Ten":
                    bd = Decimal("10")
                else:
                    bd = NumberConvert.FOUND_EXPONENTS[placement]

                if zero != "":
                    if zero == "ten":
                        bd = bd * Decimal(10)
                    elif zero == "hundred":
                        bd = bd * Decimal(100)
            else:
                raise RuntimeError("Cannot find placement of decimal places.")

            decimal = decimal / bd
            ret = ret + decimal

        if is_negative:
            ret = -ret
        return ret

    @staticmethod
    def convert_to_big(number: Any) -> Decimal:
        """
        Coerce an arbitrary input into a Decimal ("BigDecimal") equivalent.
        
        Java method: `convertToBig(Object n)`.
        
        Supports:
        - numbers / numeric strings
        - iterables / arrays (average of elements)
        - mappings (average of values)
        - non-numeric fallback: hash-based deterministic conversion (Java parity)
        """
        if number is None:
            return Decimal(0)

        if isinstance(number, Decimal):
            return number

        if isinstance(number, str):
            try:
                return Decimal(number)
            except InvalidOperation:
                # Attempt to convert to complex if number has a j or i
                cvert = number.replace("i", "j")
                try:
                    if "j" in cvert:
                        number = complex(cvert)
                except ValueError:
                    # fall through to "massive conversions" then hash
                    pass

        if isinstance(number, bool):
            return Decimal(1) if number else Decimal(0)

        if isinstance(number, (int, float)):
            return Decimal(str(number))

        if isinstance(number, complex):
            # just hashes, for now, may be changed later
            return Decimal(hash(number))

        if hasattr(number, "__float__"):
            return Decimal(float(number))

        if hasattr(number, "__int__"):
            return Decimal(int(number))

        if isinstance(number, Mapping):
            # Java: Map.Entry handled separately, Map averages pair-averages then averages again
            length = len(number)
            if length != 0:
                total = Decimal("0")
                for k, v in number.items():
                    n1 = NumberConvert.convert_to_big(k)
                    n2 = NumberConvert.convert_to_big(v)
                    total += (n1 + n2) / Decimal(2)
                return total / Decimal(length)

        # Java: if (number instanceof Object[] objects) -> average
        # Java: Iterable average
        if isinstance(number, Iterable):
            total = Decimal("0")
            length = 0
            for o in number:
                total += NumberConvert.convert_to_big(o)
                length += 1
            if length != 0:
                return total / Decimal(length)

        try:
            hash_int = getattr(number, "__hash__", None)
            if isinstance(hash_int, Callable):
                hash_int = hash_int()
            if isinstance(hash_int, (int, float, str)):
                return Decimal(hash_int)
        except (TypeError, InvalidOperation):
            pass

        if isinstance(number, str):
            # Fallback when number is a string that cannot be correctly converted.
            return Decimal(len(number))

        # Fallback when number is of some type that cannot be converted in a normal sense.
        return NumberConvert.convert_to_big(str(number))

# Convenience aliases
find_number_name = NumberConvert.find_number_name
convert_to_words = NumberConvert.convert_to_words
convert_partial_word = NumberConvert.convert_partial_word
convert_to_number = NumberConvert.convert_to_number
convert_to_big = NumberConvert.convert_to_big