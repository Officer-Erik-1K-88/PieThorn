from decimal import Decimal
from typing import List, Tuple

from ._handle import _exponent10
from ._cache import FOUND_EXPONENTS, FOUND_NUMBERS, PREFIXES, VOWELS, NUMBER_VALUES
from ._prefix import NumPrefix
from ...collections.mapping import Pair


def _check_atnn_rem(value: str, ending: bool) -> bool:
    """
    Port of Java `checkATNNRem`.

    This is part of the large-number naming algorithm: it decides whether a given
    counter segment should append `nilli` vs `illi`, matching Java's internal
    rules for the -illion family name construction.
    """
    val = value.lower()
    for check in VOWELS:
        if ending:
            if val.endswith(check):
                return True
        else:
            if val.startswith(check):
                return True
    return False

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
        if _check_atnn_rem(current, True) and _check_atnn_rem(to_add, False):
            current = current[:-1]
            name.clear()
            name.append(current)
    name.append(to_add)

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

    if group in FOUND_NUMBERS:
        return FOUND_NUMBERS[group]

    # Split group into (unit, ten, hundred) digit triples, least-significant triple first.
    indexes: List[Tuple[int, ...]] = []
    build_top = group
    while build_top != 0:
        places: List[int] = []
        for i in range(PREFIXES.place_count):
            if build_top < 10:
                places.append(build_top)
                build_top = 0
                break
            else:
                places.append(build_top % 10)
                build_top = build_top // 10
        indexes.append(tuple(place_index * pow(10, i) for i, place_index in enumerate(places)))

    name_parts: List[str] = []
    counter = 0

    for tiers_i in reversed(indexes):
        tiers: List[NumPrefix] = []

        for i in tiers_i:
            # finds the prefixes
            if i > 0:
                tiers.append(PREFIXES[i])

        tier_count = len(tiers)
        if tier_count == 1:
            # Java special-case for a single "group" digit (Billion, Trillion, ...):
            # the unit prefixes become Milli/Billi/Trilli/... instead of Un/Duo/Tre/...
            _append_to_number_name(name_parts, tiers[0].convert)
        else:
            # Consonant insertion rules (Java parity): certain unit prefixes gain a
            # trailing consonant depending on the following tens/hundreds chunk.
            # This is why you see Tre->Tres/Tresx and Se->Ses/Sex in some names.
            # Java implements this via membership tests in the s/n/m/x lists.
            # Java consonant insertion rules for Tre/Se and Septe/Nove.
            for i, tier in enumerate(tiers):
                string = tier.prefix
                if i != tier_count - 1:
                    n_tier = tiers[i + 1]
                    if len(tier.consonants) != 0 and len(n_tier.consonants) != 0:
                        for consonant in tier.consonants:
                            if consonant.trails and consonant in n_tier.consonants:
                                string = string + consonant.to
                                break
                _append_to_number_name(name_parts, string)

        built = "".join(name_parts)
        if built and (counter > 0 or tier_count > 0):
            if len(indexes) == 1:
                if not built.endswith("illi"):
                    _append_to_number_name(name_parts, "illi")
            else:
                if _check_atnn_rem(built, True):
                    name_parts.append("nilli")
                else:
                    name_parts.append("illi")

            if "".join(name_parts):
                counter += 1

    name_parts.append("on")

    final_name = "".join(name_parts).lower()
    final_name = final_name[:1].upper() + final_name[1:]
    FOUND_NUMBERS[group] = final_name
    FOUND_EXPONENTS[final_name] = Decimal(f"1E{exponent}")
    return final_name

def find_number_name(exponent: int) -> str:
    """
    Return the scale name for a base-10 exponent.

    Java method: `findNumberName(int exponent)`.

    This is a thin wrapper that normalizes the exponent to a thousand-group
    boundary and then delegates to `_get_numbers_name`.
    """
    if exponent % 3 != 0:
        raise RuntimeError("The exponent provided isn't dividable by 3.")
    word = _get_numbers_name(exponent)
    if word == "" or word == "On":
        raise RuntimeError("Couldn't find number's name from exponent.")
    return word

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
    return Pair(find_number_name(exponent), val)

def _find_decimal_name(number: Decimal, placement: str | None) -> str:
    """
    Name the fractional denominator (tenths, hundredths, ...).

    Java private helper used by the word conversion when a Decimal has a
    fractional part. It selects the correct ordinal scale word based on the
    number of decimal places.
    """
    for nv in NUMBER_VALUES:
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

        val = find_number_name(exponent)
        return f"{placement}-{val}th" if placement is not None else f"{val}th"
    except RuntimeError:
        pass

    if placement is None:
        return _find_decimal_name(number / Decimal(10), "ten")
    if placement == "ten":
        return _find_decimal_name(number / Decimal(10), "hundred")
    return ""
