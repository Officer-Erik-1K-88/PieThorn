from decimal import Decimal, InvalidOperation
from typing import Callable, Iterable, Mapping, Any, List, Tuple

from piethorn.math.converter._cache import FOUND_EXPONENTS, NUMBER_VALUES
from piethorn.math.converter._handle import _exponent10, _to_plain_string


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
            if words[1] in FOUND_EXPONENTS:
                return numeric * FOUND_EXPONENTS[words[1]]
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
    for pair in NUMBER_VALUES:
        for i in range(start_i, len(words)):
            word = words[i]
            if word == "and":
                if not has_decimal:
                    has_decimal = True
                    # Java: decimalWords = Arrays.copyOfRange(words, i+1, words.length-1);
                    decimal_words = words[i + 1: len(words) - 1]
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
        if i not in added and word in FOUND_EXPONENTS:
            place.append((i, _to_plain_string(FOUND_EXPONENTS[word])))
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
        decimal = convert_to_number(" ".join(decimal_words))
        placement = words[len(words) - 1]
        zero = ""
        placement = placement[: len(placement) - 2]  # remove "th"
        sepered = placement.split("-")
        if len(sepered) == 2:
            zero = sepered[0]
            placement = sepered[1]

        if (placement in FOUND_EXPONENTS) or (placement == "Ten"):
            if placement == "Ten":
                bd = Decimal("10")
            else:
                bd = FOUND_EXPONENTS[placement]

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
                elif len(number) <= 1:
                    return Decimal(len(number))
            except ValueError:
                if len(number) <= 1:
                    return Decimal(len(number))

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
                n1 = convert_to_big(k)
                n2 = convert_to_big(v)
                total += (n1 + n2) / Decimal(2)
            return total / Decimal(length)

    # Java: if (number instanceof Object[] objects) -> average
    # Java: Iterable average
    if isinstance(number, Iterable):
        total = Decimal("0")
        length = 0
        for o in number:
            total += convert_to_big(o)
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
    return convert_to_big(str(number))
