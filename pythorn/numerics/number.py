import cmath
import math


class Precision:
    def __init__(self, exp=32):
        self._base = 10
        self._exp = exp
        self._pow = self._base ** self._exp
        self._one = 1
        self._small = self._one / self._pow
        self._loop = int(self._exp / 2)
        self.f_lead = "0"
        self.f_last = "d"

    def update(self):
        self._pow = self._base ** self._exp
        self._small = self._one / self._pow
        self._loop = int(self._exp / 2)

    @property
    def base(self):
        return self._base

    @base.setter
    def base(self, value):
        self._base = value
        self.update()

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, value):
        self._exp = value
        self.update()

    @property
    def pow(self):
        return self._pow

    @property
    def one(self):
        return self._one

    @one.setter
    def one(self, value):
        self._one = value
        self.update()

    @property
    def small(self):
        return self._small

    @property
    def loop(self):
        return self._loop

    def format(self, value):
        return format(value, f"{self.f_lead}{self.exp}{self.f_last}")

    def __str__(self):
        return f"{self.base} ** {self.exp}"

    def __repr__(self):
        return f"<{self.__class__.__name__} \"{self}\">"

_precise_default = Precision()


class RealNum:
    # conversion below

    @classmethod
    def from_number(cls, whole, decimal, precision=_precise_default):
        """Create a Number from a whole number and a decimal part"""
        num_high, num_low = divmod(whole, precision.one << precision.exp)
        den_high, den_low = divmod(decimal, precision.one << precision.exp)
        return cls(num_high, num_low, den_high, den_low, precision)

    @classmethod
    def from_float(cls, value, precision=_precise_default):
        """
        Convert a float into a Number.
        Since floats are imprecise, this will not guarantee exact conversion.
        """
        whole_part = int(value)
        decimal_part = str(value).split(".")[1] if "." in str(value) else "0"
        decimal_part = int(decimal_part.ljust(precision.exp, "0"))  # Pad to 32 digits
        return cls.from_number(whole_part, decimal_part, precision)

    @classmethod
    def from_int(cls, value, precision=_precise_default):
        """Convert an integer to Number (decimal part = 0)"""
        return cls.from_number(value, 0, precision)

    @classmethod
    def from_string(cls, value: str, precision=_precise_default):
        """
        Convert a string representation of a number into a Number.
        Example: "1234.56789" → Number(1234, 56789000000000000000000000000000)
        """
        split = value.split(".")
        if len(split) > 2 or len(split) <= 0 or not all((s.isnumeric() or s.isdigit() or s.isdecimal() for s in split)):
            raise ValueError("The provided string is not a recognized number string.")
        if len(split) == 1:
            split.append("0")
        whole_part, decimal_part = split

        whole_part = int(whole_part)
        decimal_part = int(decimal_part.ljust(precision.exp, "0"))  # Ensure 32-digit precision
        return cls.from_number(whole_part, decimal_part, precision)

    @classmethod
    def from_any(cls, value, precision=_precise_default):
        if isinstance(value, int):
            return cls.from_int(value, precision)
        elif isinstance(value, float):
            return cls.from_float(value, precision)
        elif isinstance(value, (list, tuple)):
            return cls.from_number(value[0] | 0, value[1] | 0, precision)
        return cls.from_string(str(value), precision)

    # internal process
    def __init__(self, num_high, num_low, den_high, den_low, precision: Precision):
        """
        Represents a high-precision number using:
        - num_high: High 32 bits of the whole number part
        - num_low:  Low 32 bits of the whole number part
        - den_high: High 32 bits of the decimal part
        - den_low:  Low 32 bits of the decimal part
        """
        self.num_high = num_high
        self.num_low = num_low
        self.den_high = den_high
        self.den_low = den_low
        self._precision = precision
        self._calc = Compute(self._precision)

    @property
    def precision(self):
        return self._precision

    def get_whole_number(self):
        """Retrieve the full whole number part as a single integer"""
        return (self.num_high << self._precision.exp) + self.num_low

    def get_decimal_part(self):
        """Retrieve the full decimal part as a string with leading zeros"""
        decimal_value = (self.den_high << self._precision.exp) + self.den_low
        return self._precision.format(decimal_value).rstrip("0")  # Removes trailing zeros

    # declarations

    def __str__(self):
        """Return the precise string representation without losing precision"""
        decimal_part = self.get_decimal_part()
        if decimal_part:
            return f"{self.get_whole_number()}.{decimal_part}"
        return f"{self.get_whole_number()}"

    def __repr__(self):
        return f"Number({self.num_high}, {self.num_low}, {self.den_high}, {self.den_low}, {self._precision})"

    def __int__(self):
        return int(str(self))

    def __float__(self):
        return float(str(self))

    def __complex__(self):
        return complex(float(self))

    # math below

    def __add__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        whole1 = self.get_whole_number()
        whole2 = other.get_whole_number()
        dec1 = int(self.get_decimal_part())
        dec2 = int(other.get_decimal_part())

        # Perform addition
        new_whole = whole1 + whole2
        new_dec = dec1 + dec2

        # Handle decimal overflow (if decimal part exceeds precision)
        if new_dec >= self._precision.pow:
            new_whole += 1
            new_dec -= self._precision.pow

        return RealNum.from_number(new_whole, new_dec, self._precision)

    def __radd__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__add__(self)

    def __sub__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        whole1 = self.get_whole_number()
        whole2 = other.get_whole_number()
        dec1 = int(self.get_decimal_part())
        dec2 = int(other.get_decimal_part())

        # Perform subtraction
        new_whole = whole1 - whole2
        new_dec = dec1 - dec2

        # Handle decimal underflow (if decimal part goes negative)
        if new_dec < 0:
            new_whole -= 1
            new_dec += self._precision.pow

        return RealNum.from_number(new_whole, new_dec, self._precision)

    def __rsub__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__sub__(self)

    def __mul__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        whole1 = self.get_whole_number()
        whole2 = other.get_whole_number()
        dec1 = int(self.get_decimal_part())
        dec2 = int(other.get_decimal_part())

        # Multiply the parts
        new_whole = whole1 * whole2
        new_dec = dec1 * dec2

        # Adjust decimal part if it exceeds precision
        if new_dec >= self._precision.pow:
            carry = new_dec // self._precision.pow
            new_whole += carry
            new_dec = new_dec % self._precision.pow

        return RealNum.from_number(new_whole, new_dec, self._precision)

    def __rmul__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__mul__(self)

    def __truediv__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        whole1 = self.get_whole_number()
        whole2 = other.get_whole_number()
        dec1 = int(self.get_decimal_part())
        dec2 = int(other.get_decimal_part())

        if whole2 == 0 and dec2 == 0:
            raise ZeroDivisionError("Division by zero")

        # Convert to very large numbers for division
        num = whole1 * self._precision.pow + dec1
        den = whole2 * self._precision.pow + dec2

        # Perform division with high precision
        result = num // den
        remainder = num % den

        # Convert remainder to a decimal part
        new_dec = (remainder * self._precision.pow) // den

        return RealNum.from_number(result, new_dec, self._precision)

    def __rtruediv__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__truediv__(self)

    def __floordiv__(self, other):
        """Perform floor division (//) with another Number"""
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)

        num1 = self.get_whole_number() * self._precision.pow + int(self.get_decimal_part())
        num2 = other.get_whole_number() * self._precision.pow + int(other.get_decimal_part())

        if num2 == 0:
            raise ZeroDivisionError("Floor division by zero is not allowed.")

        quotient = num1 // num2
        return RealNum.from_number(quotient, 0, self._precision)

    def __rfloordiv__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__floordiv__(self)

    def __divmod__(self, other):
        """Perform divmod() operation: returns (quotient, remainder)."""
        quotient = self // other  # Floor division
        remainder = self % other  # Modulo
        return quotient, remainder

    def __rdivmod__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__divmod__(self)

    def __pow__(self, exponent):
        """Raise the number to an integer power."""
        whole = self.get_whole_number()
        decimal = int(self.get_decimal_part())

        # Convert the number to a high-precision integer
        base = whole * self._precision.pow + decimal
        result = base ** exponent

        # Extract whole and decimal parts
        new_whole = result // self._precision.pow
        new_decimal = result % self._precision.pow

        return RealNum.from_number(new_whole, new_decimal, self._precision)

    def __rpow__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__pow__(self)

    def __mod__(self, other):
        """Compute the remainder of division (modulus) with another Number."""
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)

        num1 = self.get_whole_number() * self._precision.pow + int(self.get_decimal_part())
        num2 = other.get_whole_number() * self._precision.pow + int(other.get_decimal_part())

        if num2 == 0:
            raise ZeroDivisionError("Modulo by zero is not allowed.")

        remainder = num1 % num2

        # Extract whole and decimal parts of the remainder
        new_whole = remainder // self._precision.pow
        new_decimal = remainder % self._precision.pow

        return RealNum.from_number(new_whole, new_decimal, self._precision)

    def __rmod__(self, other):
        if not isinstance(other, RealNum):
            other = RealNum.from_any(other, self._precision)
        return other.__mod__(self)

    def __neg__(self):
        """Return the negation of the number (-x)."""
        return RealNum.from_number(-self.get_whole_number(), int(self.get_decimal_part()), self._precision)

    def __pos__(self):
        """Return the number itself (+x)."""
        return self  # No change needed

    def __abs__(self):
        """Return the absolute value of the number"""
        whole = abs(self.get_whole_number())
        decimal = int(self.get_decimal_part())
        return RealNum.from_number(whole, decimal, self._precision)

    def __ceil__(self):
        """Round up to the nearest integer"""
        whole = self.get_whole_number()
        decimal = int(self.get_decimal_part())

        if decimal > 0:
            whole += 1  # Round up if decimal part exists

        return RealNum.from_number(whole, 0, self._precision)

    def __floor__(self):
        """Round down to the nearest integer"""
        whole = self.get_whole_number()
        return RealNum.from_number(whole, 0, self._precision)

    # comparison

    def __eq__(self, other):
        if isinstance(other, RealNum):
            return self.get_whole_number() == other.get_whole_number() and self.get_decimal_part() == other.get_decimal_part()
        return float(self) == other

    def __ne__(self, other):
        if isinstance(other, RealNum):
            return self.get_whole_number() != other.get_whole_number() and self.get_decimal_part() != other.get_decimal_part()
        return float(self) != other

    def __lt__(self, other):
        if isinstance(other, RealNum):
            return (self.get_whole_number(), self.get_decimal_part()) < (
            other.get_whole_number(), other.get_decimal_part())
        return float(self) < other

    def __le__(self, other):
        if isinstance(other, RealNum):
            return (self.get_whole_number(), self.get_decimal_part()) <= (
            other.get_whole_number(), other.get_decimal_part())
        return float(self) <= other

    def __gt__(self, other):
        if isinstance(other, RealNum):
            return (self.get_whole_number(), self.get_decimal_part()) > (
            other.get_whole_number(), other.get_decimal_part())
        return float(self) > other

    def __ge__(self, other):
        if isinstance(other, RealNum):
            return (self.get_whole_number(), self.get_decimal_part()) >= (
            other.get_whole_number(), other.get_decimal_part())
        return float(self) >= other


class Numeric:
    # conversion below

    @classmethod
    def from_tuple(cls, real, imag, precision=_precise_default):
        """Create a HighPrecisionComplex from two numerical values."""
        return cls(RealNum.from_any(real, precision), RealNum.from_any(imag, precision), precision)

    @classmethod
    def from_complex(cls, value, precision=_precise_default):
        """Create a HighPrecisionComplex from a standard Python complex number."""
        return cls(RealNum.from_float(value.real, precision), RealNum.from_float(value.imag, precision), precision)

    @classmethod
    def from_string(cls, value, precision=_precise_default):
        """
        Convert a string representation like '3.5 + 4.2i' into HighPrecisionComplex.
        Assumes format is 'a + bi' or 'a - bi'.
        """
        if "i" in value or "j" in value:
            value = value.replace(" ", "").replace("i", "").replace("j", "")
            if "+" in value:
                real_part, imag_part = value.split("+")
            elif "-" in value[1:]:  # Ensure we don't mistake a leading negative sign
                real_part, imag_part = value.rsplit("-", 1)
                imag_part = "-" + imag_part  # Restore negative sign for imaginary part
            else:
                raise ValueError("Invalid complex number format.")
            return cls(RealNum.from_string(real_part, precision), RealNum.from_string(imag_part, precision), precision)
        else:
            cls(RealNum.from_string(value, precision), None, precision)

    @classmethod
    def from_any(cls, value, precision=_precise_default):
        if isinstance(value, str):
            return cls.from_string(value, precision)
        elif isinstance(value, complex):
            return cls.from_complex(value, precision)
        elif isinstance(value, (list, tuple)):
            return cls.from_tuple(value[0] | 0, value[1] | 0, precision)
        elif isinstance(value, Numeric):
            return cls.from_tuple(value.real, value.imag, precision)
        return cls.from_tuple(value, 0, precision)

    # internal processes
    def __init__(self, real:RealNum, imag: RealNum | None, precision: Precision):
        """
        Represents a high-precision number.

        :param real: Number representing the real part.
        :param imag: Number representing the imaginary part.
        :param precision: The level of precision this number will have.
        """
        if imag is None:
            imag = RealNum.from_any(0, precision)
        self._real = real
        self._imag = imag
        self._precision = precision
        self._calc = Compute(self._precision)

    @property
    def real(self):
        return self._real

    @property
    def imag(self):
        return self._imag

    @property
    def precision(self):
        return self._precision

    def is_complex(self):
        return self._imag != 0

    def conjugate(self):
        """Return the complex conjugate."""
        return Numeric(self.real, -self.imag, self._precision)

    # declarations
    def __str__(self):
        """Return the precise string representation without losing precision"""
        if self.is_complex():
            return f"({self.real} {'+' if self.imag.get_whole_number() >= 0 else '-'} {abs(self.imag)}i)"
        return f"{self._real}"

    def __repr__(self):
        return f"Numeric({self._real}, {self._imag}, {self._precision})"

    def __int__(self):
        return int(self._real)

    def __float__(self):
        return float(self._real)

    def __complex__(self):
        if self.is_complex():
            return complex(str(self).replace(" ", "").replace("i", "j"))
        return complex(self._real)

    # math

    def __add__(self, other):
        """Add two high-precision numbers."""
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return Numeric(self.real + other.real, self.imag + other.imag, self._precision)

    def __radd__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__add__(self)

    def __sub__(self, other):
        """Subtract two high-precision numbers."""
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return Numeric(self.real - other.real, self.imag - other.imag, self._precision)

    def __rsub__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__sub__(self)

    def __mul__(self, other):
        """Multiply two high-precision numbers."""
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        real_part = (self.real * other.real) - (self.imag * other.imag)
        imag_part = (self.real * other.imag) + (self.imag * other.real)
        return Numeric(real_part, imag_part, self._precision)

    def __rmul__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__mul__(self)

    def __truediv__(self, other):
        """Divide two high-precision numbers."""
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        denom = (other.real * other.real) + (other.imag * other.imag)
        real_part = ((self.real * other.real) + (self.imag * other.imag)) / denom
        imag_part = ((self.imag * other.real) - (self.real * other.imag)) / denom
        return Numeric(real_part, imag_part, self._precision)

    def __rtruediv__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__truediv__(self)

    def __floordiv__(self, other):
        """Perform floor division (//) with another Number"""
        pass

    def __rfloordiv__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__floordiv__(self)

    def __divmod__(self, other):
        """Perform divmod() operation: returns (quotient, remainder)."""
        pass

    def __rdivmod__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__divmod__(self)

    def __pow__(self, exponent):
        """Raise the number to an exponent."""
        if isinstance(exponent, int):
            # Fast exponentiation for integer exponents
            if exponent == 0:
                return Numeric.from_tuple(1, 0, self._precision)
            if exponent < 0:
                return Numeric.from_tuple(1, 0, self._precision) / (self ** -exponent)

            result = Numeric.from_tuple(1, 0, self._precision)
            base = self
            while exponent > 0:
                if exponent % 2 == 1:
                    result *= base
                base *= base
                exponent //= 2
            return result

        elif isinstance(exponent, float):
            # Convert to polar form and apply exponentiation
            # Use polar form: (r * e^(iθ))^n = r^n * e^(iθn)
            magnitude = abs(self)
            theta = math.atan2(float(self.imag), float(self.real))  # Get the angle
            new_magnitude = magnitude ** exponent
            new_angle = theta * float(exponent)

            real_part = new_magnitude * math.cos(new_angle)
            imag_part = new_magnitude * math.sin(new_angle)

            return Numeric.from_tuple(real_part, imag_part, self._precision)
        elif isinstance(exponent, (complex, Numeric)):
            if isinstance(exponent, complex):
                exponent = Numeric.from_complex(exponent, self._precision)
            # Complex exponentiation: z^w = exp(w * log(z))
            if self.real.get_whole_number() == 0 and self.imag.get_whole_number() == 0:
                raise ValueError("Cannot raise 0 to a complex exponent.")

            # Logarithm of complex number: log(z) = log(|z|) + i * arg(z)
            magnitude = abs(self)
            theta = self._calc.atan2(self.imag, self.real)
            log_real = self._calc.log(10, magnitude)  # log(|z|)
            log_imag = theta  # i * arg(z)

            # Multiply exponent (w) by log(z)
            exp_real = (exponent.real * log_real) - (exponent.imag * log_imag)
            exp_imag = (exponent.real * log_imag) + (exponent.imag * log_real)

            # Compute final result using Euler's formula: e^(a + bi) = e^a * e^(i * b)
            final_magnitude = exp_real.exp()
            real_part = final_magnitude * self._calc.cos(exp_imag)
            imag_part = final_magnitude * self._calc.sin(exp_imag)

            return Numeric.from_tuple(real_part, imag_part, self._precision)
        else:
            raise TypeError(f"Exponent is not of supported type: {type(exponent)}")

    def __rpow__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__pow__(self)

    def __mod__(self, other):
        """Compute the remainder of division (modulus) with another Number."""
        pass

    def __rmod__(self, other):
        if not isinstance(other, Numeric):
            other = Numeric.from_any(other, self._precision)
        return other.__mod__(self)

    def __neg__(self):
        """Return the negation of the number (-x)."""
        return Numeric(-self.real, -self.imag, self._precision)

    def __pos__(self):
        """Return the number itself (+x)."""
        return self  # No change needed

    def __abs__(self):
        """Return the absolute value of the number.
        Or if complex, then return the magnitude of the complex number."""
        if self.is_complex():
            return Numeric.from_any(
                (self.real ** 2 + self.imag ** 2) ** 0.5, self._precision
            )
        return Numeric(abs(self.real), abs(self.imag), self._precision)

    def __ceil__(self):
        """Round up to the nearest integer"""
        pass

    def __floor__(self):
        """Round down to the nearest integer"""
        pass

    # comparison

    def __eq__(self, other):
        """Check the equality of two numbers."""
        if isinstance(other, complex):
            other = Numeric.from_complex(other, self._precision)
        if isinstance(other, Numeric):
            return self.real == other.real and self.imag == other.imag
        if self.is_complex():
            return False
        return self.real == other

    def __ne__(self, other):
        """Check the equality of two numbers."""
        if isinstance(other, complex):
            other = Numeric.from_complex(other, self._precision)
        if isinstance(other, Numeric):
            return self.real != other.real and self.imag != other.imag
        if self.is_complex():
            return True
        return self.real != other

    def __lt__(self, other):
        """Check if the magnitude of self is less than other."""
        if isinstance(other, complex):
            other = Numeric.from_complex(other, self._precision)
        if isinstance(other, Numeric):
            if self.is_complex() and other.is_complex():
                return abs(self) < abs(other)
            elif self.is_complex():
                return abs(self) < other.real
            elif other.is_complex():
                return self.real < abs(other)
            else:
                return self.real < other.real
        return self.real < other

    def __le__(self, other):
        """Check if the magnitude of self is less than or equal to other."""
        if isinstance(other, complex):
            other = Numeric.from_complex(other, self._precision)
        if isinstance(other, Numeric):
            if self.is_complex() and other.is_complex():
                return abs(self) <= abs(other)
            elif self.is_complex():
                return abs(self) <= other.real
            elif other.is_complex():
                return self.real <= abs(other)
            else:
                return self.real <= other.real
        return self.real <= other

    def __gt__(self, other):
        """Check if the magnitude of self is greater than other."""
        if isinstance(other, complex):
            other = Numeric.from_complex(other, self._precision)
        if isinstance(other, Numeric):
            if self.is_complex() and other.is_complex():
                return abs(self) > abs(other)
            elif self.is_complex():
                return abs(self) > other.real
            elif other.is_complex():
                return self.real > abs(other)
            else:
                return self.real > other.real
        return self.real > other

    def __ge__(self, other):
        """Check if the magnitude of self is greater than or equal to other."""
        if isinstance(other, complex):
            other = Numeric.from_complex(other, self._precision)
        if isinstance(other, Numeric):
            if self.is_complex() and other.is_complex():
                return abs(self) >= abs(other)
            elif self.is_complex():
                return abs(self) >= other.real
            elif other.is_complex():
                return self.real >= abs(other)
            else:
                return self.real >= other.real
        return self.real >= other


class Compute:
    def __init__(self, precision: Precision = _precise_default):
        self.precision = precision  # Number of terms in Taylor series

    @property
    def e(self):
        return math.e

    @property
    def pi(self):
        return math.pi

    @property
    def inf(self):
        return math.inf

    def _sin_cos(self, x):
        sin_term = x
        sin = x
        cos_term = 1
        cos = 1
        n = 1
        leave = [False, False]
        while n < self.precision.loop:
            if abs(sin_term) >= self.precision.small or n == 1:
                sin_term *= -x * x / ((2 * n) * (2 * n + 1))
                sin += sin_term
            else:
                leave[0] = True
            if abs(cos_term) >= self.precision.small or n == 1:
                cos_term *= -x * x / ((2 * n - 1) * (2 * n))
                cos += cos_term
            else:
                leave[1] = True
            if all(leave):
                break
            n += 1
        return sin, cos

    def sin(self, x):
        """Fast sin(x) using Taylor series"""
        return self._sin_cos(x)[0]

    def cos(self, x):
        """Fast cos(x) using Taylor series"""
        return self._sin_cos(x)[1]

    def tan(self, x):
        """tan(x) = sin(x) / cos(x)"""
        sin, cos = self._sin_cos(x)
        return sin / cos

    def _sinh_cosh(self, x):
        sinh_term = x
        sinh = x
        cosh_term = 1
        cosh = 1
        n = 1
        leave = [False, False]
        while n < self.precision.loop:
            if abs(sinh_term) >= self.precision.small or n == 1:
                sinh_term *= x * x / ((2 * n) * (2 * n + 1))
                sinh += sinh_term
            else:
                leave[0] = True
            if abs(cosh_term) >= self.precision.small or n == 1:
                cosh_term *= x * x / ((2 * n - 1) * (2 * n))
                cosh += cosh_term
            else:
                leave[1] = True
            if all(leave):
                break
            n += 1
        return sinh, cosh

    def sinh(self, x):
        """Hyperbolic sin(x) using Taylor series"""
        return self._sinh_cosh(x)[0]

    def cosh(self, x):
        """Hyperbolic cosh(x) using Taylor series"""
        return self._sinh_cosh(x)[1]

    def tanh(self, x):
        """Hyperbolic tanh(x)"""
        sinh, cosh = self._sinh_cosh(x)
        return sinh / cosh

    def asin(self, x):
        """Inverse sin(x) using Taylor series"""
        if abs(x) > 1:
            raise ValueError("asin(x) is only defined for -1 <= x <= 1")
        term = x
        result = x
        num = x
        den = 1
        n = 1
        while n < self.precision.loop:
            num *= (2 * n - 1) ** 2 * x * x
            den *= (2 * n) * (2 * n + 1)
            term = num / den
            result += term
            if abs(term) < self.precision.small:
                break
            n += 1
        return result

    def acos(self, x):
        """Inverse cos(x)"""
        return (self.pi/2) - self.asin(x)  # pi/2 - asin(x)

    def atan(self, x):
        """Inverse tan(x) using Taylor series"""
        if abs(x) > 1:
            return (self.pi / 2) - self.atan(1 / x)  # Adjust for large x
        term = x
        result = x
        n = 1
        while n < self.precision.loop:
            term *= -x * x * (2 * n - 1) / (2 * n + 1)
            result += term
            if abs(term) < self.precision.small:
                break
            n += 1
        return result

    def atan2(self, y, x):
        """atan2(y, x) with quadrant correction"""
        if x > 0:
            return self.atan(y / x)
        elif x < 0 <= y:
            return self.atan(y / x) + self.pi
        elif x < 0 and y < 0:
            return self.atan(y / x) - self.pi
        elif x == 0 and y > 0:
            return self.pi / 2  # pi/2
        elif x == 0 and y < 0:
            return -(self.pi / 2)  # -pi/2
        else:
            return 0  # atan2(0, 0) is undefined but usually returns 0

    def asinh(self, x):
        """Inverse hyperbolic sinh(x)"""
        return self.ln(x + self.sqrt(x * x + 1))

    def acosh(self, x):
        """Inverse hyperbolic cosh(x)"""
        if x < 1:
            raise ValueError("acosh(x) is only defined for x >= 1")
        return self.ln(x + self.sqrt(x * x - 1))

    def atanh(self, x):
        """Inverse hyperbolic tanh(x)"""
        if abs(x) >= 1:
            raise ValueError("atanh(x) is only defined for -1 < x < 1")
        return 0.5 * self.ln((1 + x) / (1 - x))

    def rect(self, r, theta):
        """
        Converts from polar coordinates (r, theta) to rectangular coordinates.
        """
        sin, cos = self._sin_cos(theta)
        return complex(r * cos, r * sin)

    def gamma(self, x):
        """Rebuilds Python's math.gamma() function using the Lanczos approximation."""
        # TODO: Improve accuracy of this method.
        if x < 0.5:
            # Reflection formula for gamma(x) when x < 0.5:
            return self.pi / (self.sin(self.pi * x) * self.gamma(1 - x))

        # Lanczos Approximation with optimized coefficients
        g = 7
        p = [
            0.99999999999980993, 676.5203681218851, -1259.1392167224028,
            771.32342877765313, -176.61502916214059, 12.507343278686905,
            -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
        ]

        x -= 1  # Adjust for Gamma function definition

        a = p[0]
        for i in range(1, len(p)):
            a += p[i] / (x + i)

        t = x + g + 0.5
        sqrt_2pi = self.sqrt(2 * self.pi)  # sqrt(2π)

        return sqrt_2pi * (t ** (x + 0.5)) * self.exp(-t) * a

    def factorial(self, x):
        """Computes factorial(x) for real numbers using gamma(x + 1)."""
        if x < 0:
            raise ValueError("Factorial is not defined for negative numbers.")
        return self.gamma(x + 1)

    def sqrt(self, x):
        """Square root"""
        return self.nth_root(2, x)

    def nth_root(self, n, x):
        """Computes the nth root of x, handling negative n and negative x correctly."""
        if n == 0:
            raise ValueError("Root degree cannot be zero.")

        # Handle negative n: compute the positive nth root and take its reciprocal
        if n < 0:
            return 1 / self.nth_root(-n, x)

        # Handle negative x: odd roots are valid, even roots are not
        if x < 0:
            real_root = self.nth_root(n, -x)  # Compute real nth root of |x|
            if n % 2 == 0:
                angle = self.pi / n  # Phase shift for imaginary component
                return self.rect(real_root, angle)  # Convert to polar form
            #    raise ValueError("Cannot compute even root of a negative number")
            return -real_root  # Compute positive root and negate it


        # Initial guess using exponentiation: y = e^(ln(x)/n)
        y = self.exp(self.ln(x) / n)

        # Newton’s method loop
        for _ in range(self.precision.loop):
            y_next = y - (y ** n - x) / (n * y ** (n - 1))
            if abs(y_next - y) < self.precision.small:
                break
            y = y_next

        return y

    def power(self, base, exp):
        """Computes base^exp for both integer and float exponents without external libraries."""
        if base == 0:
            if exp > 0:
                return 0
            elif exp == 0:
                return 1  # 0^0 is conventionally 1
            else:
                raise ValueError("0 cannot be raised to a negative power")

        if exp == 0:
            return 1  # Any number to the power of 0 is 1

        if isinstance(exp, int):
            # Integer exponentiation using fast exponentiation (Exponentiation by Squaring)
            result = 1
            b = base
            e = abs(exp)
            while e > 0:
                if e % 2 == 1:
                    result *= b
                b *= b
                e //= 2
            return result if exp > 0 else 1 / result

        if base < 0 and exp % 1 != 0:
            # Negative base with non-integer exponent results in a complex number
            magnitude = self.power(-base, exp)
            angle = exp * 3.141592653589793  # pi * y
            sin, cos = self._sin_cos(angle)
            return complex(magnitude * cos, magnitude * sin)

        # Floating-point exponentiation using exp(y * ln(x))
        return self.exp(exp * self.ln(base))

    def exp(self, x):
        """Computes e^x with high precision using exponent splitting and Padé approximation."""
        if x == 0:
            return 1
        if x < 0:
            return 1 / self.exp(-x)

        # Exponent splitting: Separate integer and fractional parts
        int_x = int(x)  # Integer part
        frac_x = x - int_x  # Fractional part

        # Compute e^integer part using fast exponentiation
        def fast_pow(base, exp):
            """Computes base^exp using exponentiation by squaring."""
            result = 1
            while exp > 0:
                if exp % 2 == 1:
                    result *= base
                base *= base
                exp //= 2
            return result

        exp_int = fast_pow(2.718281828459045, int_x)

        # Taylor series for the fractional part
        def taylor_exp(y):
            term = 1
            result = 1
            for n in range(1, self.precision.loop):
                term *= y / n
                result += term
                if abs(term) < self.precision.small:
                    break
            return result

        result = taylor_exp(frac_x)

        return exp_int * result

    def frexp(self, x):
        """Extracts the exponent and mantissa similar to math.frexp(x)"""
        exponent = 0
        while x >= 2:
            x /= 2
            exponent += 1
        while x < 1:
            x *= 2
            exponent -= 1
        return x, exponent

    def _ln_frexp(self, x):
        # Extract exponent and mantissa
        m, e = self.frexp(x)
        m = (m - 1) / (m + 1)  # Transform for better convergence
        return m, e

    def _ln_taylor_guts(self, m2, term, i, result):
        # Use Taylor series expansion (Mercator series)
        term *= m2
        result += term / (2 * i + 1)
        return term, result

    def _ln_final(self, result, e):
        return (2 * result) + (e * 0.6931471805599453)  # ln(2) ≈ 0.693

    def ln(self, x):
        """Computes ln(x) using IEEE 754 floating-point tricks and a Taylor series."""
        if x <= 0:
            raise ValueError("ln(x) is only defined for x > 0")
        if x == 1:
            return 0  # ln(1) = 0

        # Extract exponent and mantissa
        m, e = self._ln_frexp(x)

        # Use Taylor series expansion (Mercator series)
        term = m
        m2 = m * m
        result = term
        for i in range(1, self.precision.loop):
            term, result = self._ln_taylor_guts(m2, term, i, result)
            if abs(term) < self.precision.small:
                break

        return self._ln_final(result, e)

    def log(self, base, x):
        """Computes log_base(x) using ln(x) / ln(base) as Python's math.log does."""
        if x <= 0:
            raise ArithmeticError("Logarithm any base of zero is undefined")
        elif x == 1:
            return 0
        elif x == base:
            return 1
        if base == 0:
            return 0
        elif base == 1:
            raise ArithmeticError("The base of a logarithm must not be 1.")

        m1, e1 = self._ln_frexp(x)
        m2, e2 = self._ln_frexp(base)

        # Use Taylor series expansion (Mercator series)
        term1 = m1
        m3 = m1 * m1
        result1 = term1
        term2 = m2
        m4 = m2 * m2
        result2 = term2
        leave = [False, False]
        for i in range(1, self.precision.loop):
            if abs(term1) < self.precision.small or i == 1:
                term1, result1 = self._ln_taylor_guts(m3, term1, i, result1)
            else:
                leave[0] = True
            if abs(term2) < self.precision.small or i == 1:
                term2, result2 = self._ln_taylor_guts(m4, term2, i, result2)
            else:
                leave[0] = True
            if all(leave):
                break

        return self._ln_final(result1, e1) / self._ln_final(result2, e2)

    def gcd(self, *args):
        """Computes the Greatest Common Divisor (GCD) of multiple numbers."""
        if not args:
            raise ValueError("At least one number must be provided for GCD")

        def gcd_two(a, b):
            """Computes GCD of two numbers using the Euclidean algorithm."""
            a, b = abs(a), abs(b)
            while b:
                a, b = b, a % b
            return a

        result = args[0]
        for num in args[1:]:
            result = gcd_two(result, num)
            if result == 1:  # GCD of 1 means all further calculations are unnecessary
                return 1
        return result

    def lcm(self, *args):
        """Computes the Least Common Multiple (LCM) of multiple numbers."""
        if not args:
            raise ValueError("At least one number must be provided for LCM")

        def lcm_two(a, b):
            """Computes LCM of two numbers using GCD."""
            if a == 0 or b == 0:
                return 0
            return abs(a * b) // self.gcd(a, b)

        result = args[0]
        for num in args[1:]:
            result = lcm_two(result, num)
        return result

