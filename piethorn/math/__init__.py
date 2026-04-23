import random

__all__ = [
    # modules
    "converter",
    "equation",

    # logic
    "LogicGates",

    # random
    "skew",
]

# --- logistics ---
class LogicGates:
    """Evaluate basic boolean gates with configurable truthy polarity."""

    def __init__(self, reverse=False):
        self.truthy = True
        self.falsy = False
        if reverse:
            self.truthy = False
            self.falsy = True

    def and_gate(self, *boolean):
        """Return the logical AND of the provided boolean-like values."""
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.truthy
        for y in bools:
            x = y if isinstance(y,bool) else self.truthy if y==1 else self.falsy
            if not x:
                bool_val = self.falsy
                break
        return bool_val

    def or_gate(self, *boolean):
        """Return the logical OR of the provided boolean-like values."""
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.falsy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                bool_val = self.truthy
                break
        return bool_val

    def not_gate(self, *boolean):
        """Return the logical NOT of one value or each value in a collection."""
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_vals = []
        if isinstance(bools,list):
            for y in bools:
                x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
                if x:
                    bool_vals.append(self.falsy)
                else:
                    bool_vals.append(self.truthy)
            return bool_vals
        else:
            if bools:
                return self.falsy
            else:
                return self.truthy

    def nand_gate(self, *boolean):
        """Return the logical NAND of the provided boolean-like values."""
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.falsy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if not x:
                bool_val = self.truthy
                break
        return bool_val

    def nor_gate(self, *boolean):
        """Return the logical NOR of the provided boolean-like values."""
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.truthy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                bool_val = self.falsy
                break
        return bool_val

    def xor_gate(self, *boolean):
        """Return the logical XOR of the provided boolean-like values."""
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.falsy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                if self.and_gate(bools):
                    bool_val = self.falsy
                    break
                else:
                    bool_val = self.truthy
                    break
        return bool_val

    def xnor_gate(self, *boolean):
        """Return the logical XNOR of the provided boolean-like values."""
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.truthy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                if self.and_gate(bools):
                    bool_val = self.truthy
                    break
                else:
                    bool_val = self.falsy
                    break
        return bool_val

# --- random ---

def skew(skew_at=0.6, weight=0.9, minimum=0, maximum=100, is_int=False):
    """
    Generates a random percentage skewed towards `skew_at`.
    The generation has a skew of two points, the first is the declared `skew_at`,
    the second is `(skew_at/2) + (minimum/100)` this second skew is called the
    `mix_skew`.

    The default skew is a skew at 60% with a weight of 90% for a range of 0-100%
    with a return of a float.

    :param skew_at: The point around which values are skewed (0-1).
    :param weight: The probability that values fall below `skew_at` (0-1). If this value is zero, then no skew. If this value is one then it will be heavily skewed, but values beyond `skew_at` are still possible.
    :param minimum: The lowest percent that can be given. (0-100)
    :param maximum: The largest percent that can be given. (0-100)
    :param is_int: Whether to return the random percent as an integer.
    :return: A skewed random percentage within [minimum, maximum].
    """
    if not (0 <= skew_at <= 1):
        raise ValueError("skew_at must be between 0 and 1")
    if not (0 <= weight <= 1):
        raise ValueError("weight must be between 0 and 1")
    if not (0 <= minimum < maximum <= 100):
        raise ValueError("minimum and maximum must satisfy 0 <= minimum < maximum <= 100")

    base_value = random.uniform(0, 1)  # Generate a base random value between 0 and 1

    if skew_at == 0 or skew_at == 1 or weight == 0:
        ret = base_value
    else:
        # Apply a custom transformation to skew the values
        check = random.random()
        skew_weight = (skew_at / weight)
        if check < weight:
            if base_value < minimum / 100:
                base_value = base_value * skew_weight * maximum
            if base_value > skew_at:
                base_value = base_value * skew_weight
        else:
            base_value = 1 - (1 - skew_weight) * (1 - base_value)
        if base_value > 1:
            base_value = skew_at / base_value

        mix_skew = (skew_at / 2) + (minimum / 100)

        if mix_skew < base_value <= skew_at:
            # Spread values more evenly across the skewed range
            # Further reduce clustering with a combination of exponentiation and a secondary random factor
            base_value = mix_skew + ((random.uniform(0, 1) ** 1.1) * (skew_at - mix_skew) * random.uniform(1.3, 1.6))

        ret = base_value

    ret *= maximum
    if is_int:
        ret = int(round(ret))
        minimum = int(minimum)
        maximum = int(maximum)
    if ret < minimum:
        ret = ret / minimum
        ret *= 100
        ret = int(ret)
    return min(max(ret, minimum), maximum)
