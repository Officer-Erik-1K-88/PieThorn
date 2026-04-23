import decimal
from decimal import Decimal

# --- Java MathContext(2448) equivalent ---
decimal.getcontext().prec = 2448

def localcontext():
    """Return ``decimal.localcontext`` using the module's configured precision."""

    return decimal.localcontext()

# --- Special handling ---
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
