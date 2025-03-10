import math


class Precision:
    def __init__(self, exp=32):
        self.base = 10
        self.exp = exp
        self.one = 1
        self.f_lead = "0"
        self.f_last = "d"

    @property
    def pow(self):
        return self.base ** self.exp

    def format(self, value):
        return format(value, f"{self.f_lead}{self.exp}{self.f_last}")

    def __str__(self):
        return f"{self.base} ** {self.exp}"

    def __repr__(self):
        return f"<{self.__class__.__name__} \"{self}\">"

_precise_default = Precision()


class RealNum:
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
        value = value.replace(" ", "").replace("i", "").replace("j", "")
        if "+" in value:
            real_part, imag_part = value.split("+")
        elif "-" in value[1:]:  # Ensure we don't mistake a leading negative sign
            real_part, imag_part = value.rsplit("-", 1)
            imag_part = "-" + imag_part  # Restore negative sign for imaginary part
        else:
            raise ValueError("Invalid complex number format.")

        return cls(RealNum.from_string(real_part, precision), RealNum.from_string(imag_part, precision), precision)

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

    def __init__(self, real:RealNum, imag: RealNum, precision: Precision):
        self._real = real
        self._imag = imag
        self._precision = precision

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
        return complex(str(self).replace(" ", "").replace("i", "j"))

    def __abs__(self):
        """Return the magnitude of the complex number. If not complex, then it's just the absolute value."""
        if self.is_complex():
            return RealNum.from_any(
                (self.real ** 2 + self.imag ** 2) ** 0.5, self._precision
            )
        else:
            return Numeric(abs(self.real), RealNum.from_any(0, self._precision), self._precision)

    def __neg__(self):
        """Return the negation of the number."""
        return Numeric(-self.real, -self.imag, self._precision)

    def __pos__(self):
        return self

    # comparison

    def __eq__(self, other):
        """Check the equality of two complex numbers."""
        if isinstance(other, complex):
            other = Numeric.from_complex(other, self._precision)
        if isinstance(other, Numeric):
            return self.real == other.real and self.imag == other.imag
        if self.is_complex():
            return False
        return self.real == other

    def __ne__(self, other):
        """Check the equality of two complex numbers."""
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


class Number:
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
            return Number.from_int(value, precision)
        elif isinstance(value, float):
            return Number.from_float(value, precision)
        elif isinstance(value, (list, tuple)):
            return Number.from_number(value[0] | 0, value[1] | 0, precision)
        elif isinstance(value, complex):
            return HighPrecisionComplex.from_complex(value, precision)
        elif isinstance(value, HighPrecisionComplex):
            return HighPrecisionComplex.from_any(value, precision)
        return Number.from_string(str(value), precision)

    # internal processes
    def __init__(self, num_high, num_low, den_high, den_low, precision=_precise_default):
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
        return f"Number({self.num_high}, {self.num_low}, {self.den_high}, {self.den_low})"

    def __int__(self):
        return int(str(self))

    def __float__(self):
        return float(str(self))

    def __complex__(self):
        return complex(float(self))

    # math below

    def __add__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
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

        return Number.from_number(new_whole, new_dec, self._precision)

    def __radd__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
        return other.__add__(self)

    def __sub__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
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

        return Number.from_number(new_whole, new_dec, self._precision)

    def __rsub__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
        return other.__sub__(self)

    def __mul__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
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

        return Number.from_number(new_whole, new_dec, self._precision)

    def __rmul__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
        return other.__mul__(self)

    def __truediv__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
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

        return Number.from_number(result, new_dec, self._precision)

    def __rtruediv__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
        return other.__truediv__(self)

    def __floordiv__(self, other):
        """Perform floor division (//) with another Number"""
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)

        num1 = self.get_whole_number() * self._precision.pow + int(self.get_decimal_part())
        num2 = other.get_whole_number() * self._precision.pow + int(other.get_decimal_part())

        if num2 == 0:
            raise ZeroDivisionError("Floor division by zero is not allowed.")

        quotient = num1 // num2
        return Number.from_number(quotient, 0, self._precision)

    def __rfloordiv__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
        return other.__floordiv__(self)

    def __divmod__(self, other):
        """Perform divmod() operation: returns (quotient, remainder)."""
        quotient = self // other  # Floor division
        remainder = self % other  # Modulo
        return quotient, remainder

    def __rdivmod__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
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

        return Number.from_number(new_whole, new_decimal, self._precision)

    def __rpow__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
        return other.__pow__(self)

    def __mod__(self, other):
        """Compute the remainder of division (modulus) with another Number."""
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)

        num1 = self.get_whole_number() * self._precision.pow + int(self.get_decimal_part())
        num2 = other.get_whole_number() * self._precision.pow + int(other.get_decimal_part())

        if num2 == 0:
            raise ZeroDivisionError("Modulo by zero is not allowed.")

        remainder = num1 % num2

        # Extract whole and decimal parts of the remainder
        new_whole = remainder // self._precision.pow
        new_decimal = remainder % self._precision.pow

        return Number.from_number(new_whole, new_decimal, self._precision)

    def __rmod__(self, other):
        if not isinstance(other, Number):
            other = Number.from_any(other, self._precision)
        return other.__mod__(self)

    def __neg__(self):
        """Return the negation of the number (-x)."""
        return Number.from_number(-self.get_whole_number(), int(self.get_decimal_part()))

    def __pos__(self):
        """Return the number itself (+x)."""
        return self  # No change needed

    def __abs__(self):
        """Return the absolute value of the number"""
        whole = abs(self.get_whole_number())
        decimal = int(self.get_decimal_part())
        return Number.from_number(whole, decimal, self._precision)

    def __ceil__(self):
        """Round up to the nearest integer"""
        whole = self.get_whole_number()
        decimal = int(self.get_decimal_part())

        if decimal > 0:
            whole += 1  # Round up if decimal part exists

        return Number.from_number(whole, 0, self._precision)

    def __floor__(self):
        """Round down to the nearest integer"""
        whole = self.get_whole_number()
        return Number.from_number(whole, 0, self._precision)

    # comparison

    def __eq__(self, other):
        if isinstance(other, Number):
            return self.get_whole_number() == other.get_whole_number() and self.get_decimal_part() == other.get_decimal_part()
        return float(self) == other

    def __ne__(self, other):
        if isinstance(other, Number):
            return self.get_whole_number() != other.get_whole_number() and self.get_decimal_part() != other.get_decimal_part()
        return float(self) != other

    def __lt__(self, other):
        if isinstance(other, Number):
            return (self.get_whole_number(), self.get_decimal_part()) < (other.get_whole_number(), other.get_decimal_part())
        return float(self) < other

    def __le__(self, other):
        if isinstance(other, Number):
            return (self.get_whole_number(), self.get_decimal_part()) <= (other.get_whole_number(), other.get_decimal_part())
        return float(self) <= other

    def __gt__(self, other):
        if isinstance(other, Number):
            return (self.get_whole_number(), self.get_decimal_part()) > (other.get_whole_number(), other.get_decimal_part())
        return float(self) > other

    def __ge__(self, other):
        if isinstance(other, Number):
            return (self.get_whole_number(), self.get_decimal_part()) >= (other.get_whole_number(), other.get_decimal_part())
        return float(self) >= other


class HighPrecisionComplex:
    @classmethod
    def from_tuple(cls, real, imag, precision=_precise_default):
        """Create a HighPrecisionComplex from two numerical values."""
        return cls(Number.from_any(real, precision), Number.from_any(imag, precision), precision)

    @classmethod
    def from_complex(cls, value, precision=_precise_default):
        """Create a HighPrecisionComplex from a standard Python complex number."""
        return cls(Number.from_float(value.real, precision), Number.from_float(value.imag, precision), precision)

    @classmethod
    def from_string(cls, value, precision=_precise_default):
        """
        Convert a string representation like '3.5 + 4.2i' into HighPrecisionComplex.
        Assumes format is 'a + bi' or 'a - bi'.
        """
        value = value.replace(" ", "").replace("i", "").replace("j", "")
        if "+" in value:
            real_part, imag_part = value.split("+")
        elif "-" in value[1:]:  # Ensure we don't mistake a leading negative sign
            real_part, imag_part = value.rsplit("-", 1)
            imag_part = "-" + imag_part  # Restore negative sign for imaginary part
        else:
            raise ValueError("Invalid complex number format.")

        return cls(Number.from_string(real_part, precision), Number.from_string(imag_part, precision), precision)

    @classmethod
    def from_any(cls, value, precision=_precise_default):
        if isinstance(value, str):
            return HighPrecisionComplex.from_string(value, precision)
        elif isinstance(value, complex):
            return HighPrecisionComplex.from_complex(value, precision)
        elif isinstance(value, (list, tuple)):
            return HighPrecisionComplex.from_tuple(value[0] | 0, value[1] | 0, precision)
        elif isinstance(value, HighPrecisionComplex):
            return HighPrecisionComplex.from_tuple(value.real, value.imag, precision)
        return HighPrecisionComplex.from_tuple(value, 0, precision)

    def __init__(self, real, imag, precision=_precise_default):
        """
        Represents a high-precision complex number.
        - `real`: Number representing the real part.
        - `imag`: Number representing the imaginary part.
        """
        if not isinstance(real, Number) or not isinstance(imag, Number):
            raise TypeError("Both real and imaginary parts must be Number instances.")

        self.real = real
        self.imag = imag
        self._precision = precision

    def __str__(self):
        """Return the precise string representation of the complex number."""
        return f"({self.real} {'+' if self.imag.get_whole_number() >= 0 else '-'} {abs(self.imag)}i)"

    def __repr__(self):
        return f"HighPrecisionComplex({repr(self.real)}, {repr(self.imag)})"

    def __complex__(self):
        for_complex = f"({self.real}{'+' if self.imag.get_whole_number() >= 0 else '-'}{abs(self.imag)}j)"
        return complex(for_complex)

    def __add__(self, other):
        """Add two high-precision complex numbers."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return HighPrecisionComplex(self.real + other.real, self.imag + other.imag, self._precision)

    def __radd__(self, other):
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return other.__add__(self)

    def __sub__(self, other):
        """Subtract two high-precision complex numbers."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return HighPrecisionComplex(self.real - other.real, self.imag - other.imag, self._precision)

    def __rsub__(self, other):
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return other.__sub__(self)

    def __mul__(self, other):
        """Multiply two high-precision complex numbers."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        real_part = (self.real * other.real) - (self.imag * other.imag)
        imag_part = (self.real * other.imag) + (self.imag * other.real)
        return HighPrecisionComplex(real_part, imag_part, self._precision)

    def __rmul__(self, other):
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return other.__mul__(self)

    def __truediv__(self, other):
        """Divide two high-precision complex numbers."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        denom = (other.real * other.real) + (other.imag * other.imag)
        real_part = ((self.real * other.real) + (self.imag * other.imag)) / denom
        imag_part = ((self.imag * other.real) - (self.real * other.imag)) / denom
        return HighPrecisionComplex(real_part, imag_part, self._precision)

    def __rtruediv__(self, other):
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return other.__truediv__(self)

    def __pow__(self, exponent):
        """Raise the complex number to an exponent (supports int, float, HighPrecisionNumber, and complex)."""
        if isinstance(exponent, int):
            # Fast exponentiation for integer exponents
            if exponent == 0:
                return HighPrecisionComplex.from_tuple(1, 0, self._precision)
            if exponent < 0:
                return HighPrecisionComplex.from_tuple(1, 0, self._precision) / (self ** -exponent)

            result = HighPrecisionComplex.from_tuple(1, 0, self._precision)
            base = self
            while exponent > 0:
                if exponent % 2 == 1:
                    result *= base
                base *= base
                exponent //= 2
            return result

        elif isinstance(exponent, (float, Number)):
            # Convert to polar form and apply exponentiation
            # Use polar form: (r * e^(iθ))^n = r^n * e^(iθn)
            magnitude = abs(self)
            theta = math.atan2(float(self.imag), float(self.real))  # Get the angle
            new_magnitude = magnitude ** exponent
            new_angle = theta * float(exponent)

            real_part = new_magnitude * math.cos(new_angle)
            imag_part = new_magnitude * math.sin(new_angle)

            return HighPrecisionComplex.from_tuple(real_part, imag_part, self._precision)

        elif isinstance(exponent, (complex, HighPrecisionComplex)):
            if isinstance(exponent, complex):
                exponent = HighPrecisionComplex.from_complex(exponent, self._precision)
            # Complex exponentiation: z^w = exp(w * log(z))
            if self.real.get_whole_number() == 0 and self.imag.get_whole_number() == 0:
                raise ValueError("Cannot raise 0 to a complex exponent.")

            # Logarithm of complex number: log(z) = log(|z|) + i * arg(z)
            magnitude = abs(self)
            theta = math.atan2(float(self.imag), float(self.real))
            log_real = math.log(float(magnitude))  # log(|z|)
            log_imag = theta  # i * arg(z)

            # Multiply exponent (w) by log(z)
            exp_real = (float(exponent.real) * log_real) - (float(exponent.imag) * log_imag)
            exp_imag = (float(exponent.real) * log_imag) + (float(exponent.imag) * log_real)

            # Compute final result using Euler's formula: e^(a + bi) = e^a * e^(i * b)
            final_magnitude = math.exp(exp_real)
            real_part = final_magnitude * math.cos(exp_imag)
            imag_part = final_magnitude * math.sin(exp_imag)

            return HighPrecisionComplex.from_tuple(real_part, imag_part, self._precision)
        else:
            raise TypeError("Exponent must be an int, float, Number, complex, or HighPrecisionComplex.")

    def __rpow__(self, other):
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return other.__pow__(self)

    def __abs__(self):
        """Return the magnitude of the complex number."""
        return Number.from_any(
            (self.real ** 2 + self.imag ** 2) ** 0.5, self._precision
        )

    def conjugate(self):
        """Return the complex conjugate."""
        return HighPrecisionComplex(self.real, -self.imag, self._precision)

    def __eq__(self, other):
        """Check the equality of two complex numbers."""
        return self.real == other.real and self.imag == other.imag

    def __ne__(self, other):
        """Check the equality of two complex numbers."""
        return self.real != other.real and self.imag != other.imag

    def __lt__(self, other):
        """Check if the magnitude of self is less than other."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return abs(self) < abs(other)

    def __le__(self, other):
        """Check if the magnitude of self is less than or equal to other."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return abs(self) <= abs(other)

    def __gt__(self, other):
        """Check if the magnitude of self is greater than other."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return abs(self) > abs(other)

    def __ge__(self, other):
        """Check if the magnitude of self is greater than or equal to other."""
        if not isinstance(other, HighPrecisionComplex):
            other = HighPrecisionComplex.from_any(other, self._precision)
        return abs(self) >= abs(other)

    def __neg__(self):
        """Return the negation of the complex number."""
        return HighPrecisionComplex(-self.real, -self.imag, self._precision)

    def __pos__(self):
        return self