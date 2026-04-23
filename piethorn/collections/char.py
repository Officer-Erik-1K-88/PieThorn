from typing import Iterable, Iterator, TypeAlias, Callable, SupportsIndex

CharValid: TypeAlias = 'Char | str | int'

class Char:
    """Represent a single Unicode character or an empty sentinel value."""

    def __init__(self, char: CharValid):
        if isinstance(char, Char):
            self._char = char.char()
            self._ordinal = char.ord()
        elif isinstance(char, int):
            if 0 <= char <= 0x10FFFF:
                self._char = chr(char)
                self._ordinal = char
            else:
                self._char = ""
                self._ordinal = char
        else:
            if len(char) > 1:
                raise ValueError("Character must be a single character")
            self._char = char
            self._ordinal = ord(char) if char else -1

    def char(self) -> str:
        """
        Returns the character represented by this char.
        """
        return self._char

    def ord(self):
        """
        Returns the ordinal value of the character.

        The ordinal usually is the Unicode code point of that character.
        """
        return self._ordinal

    def is_empty(self) -> bool:
        """
        Check if char is empty.
        """
        return self.char() == ''

    def isascii(self) -> bool:
        """
        Return True if this char is ASCII, False otherwise.

        An ASCII char has a code point in the range U+0000-U+007F. An empty char is ASCII too.
        """
        return self.char().isascii()

    def isdecimal(self) -> bool:
        """
        Return True if the char is a decimal, False otherwise.
        """
        return self.char().isdecimal()

    def isdigit(self) -> bool:
        """
        Return True if the char is a digit, False otherwise.
        """
        return self.char().isdigit()

    def isnumeric(self) -> bool:
        """
        Return True if the char is numeric, False otherwise.
        """
        return self.char().isnumeric()

    def isalnum(self) -> bool:
        """
        Return True if the char is alphanumeric, False otherwise.
        """
        return self.char().isalnum()

    def isalpha(self) -> bool:
        """
        Return True if the char is alphabetic, False otherwise.
        """
        return self.char().isalpha()

    def islower(self) -> bool:
        """
        Return True if the char is lowercase, False otherwise.
        """
        return self.char().islower()

    def isupper(self) -> bool:
        """
        Return True if the char is uppercase, False otherwise.
        """
        return self.char().isupper()

    def isspace(self) -> bool:
        """
        Return True if the char is whitespace, False otherwise.
        """
        return self.char().isspace()

    def isprintable(self) -> bool:
        """
        Return True if this char is printable, False otherwise.

        A character is printable if repr() may use it in its output.
        :return:
        """
        return self.char().isprintable()

    def upper(self):
        """Return an uppercased copy of this character."""
        return Char(self._char.upper())
    def lower(self):
        """Return a lowercased copy of this character."""
        return Char(self._char.lower())

    def compare(self, other):
        """
        Compares this object to another object.

        Rules:
        - Char vs Char: compare ordinals.
        - Char vs str:
            * len==1: compare to ord(str)
            * len==0: empty string is deemed smaller than any non-empty Char
                      (but equal to an empty Char)
            * len>1: multi-char strings are deemed larger than any Char
        - Char vs int/float: compare to numeric ordinal.

        :param other: The object to compare to.
        :return: 0 if both objects are equal, 1 if this object is greater, and -1 if this object is less.
        """
        if self is other:
            return 0
        # Char
        if isinstance(other, Char):
            a = self.ord()
            b = other.ord()
            return -1 if a < b else (1 if a > b else 0)

        # str
        if isinstance(other, str):
            if len(other) == 0:
                # other is "smaller"
                return 0 if self.is_empty() else 1
            if len(other) == 1:
                a = self.ord()
                b = ord(other)
                return -1 if a < b else (1 if a > b else 0)
            # multi-char strings are "larger"
            return -1

        # numbers
        if isinstance(other, (int, float)):
            a = self.ord()
            b = other
            return -1 if a < b else (1 if a > b else 0)

        raise TypeError(f"cannot compare type {type(self)} to {type(other)}")

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __len__(self):
        return len(self.char())

    def __str__(self):
        return self.char()

    def __int__(self):
        return self.ord()

    def __float__(self):
        return float(self.ord())

    def __repr__(self):
        return f"Char({self._char!r})"


class CharSequence(tuple[Char]):
    """Store a normalized immutable sequence of ``Char`` instances."""

    def __new__(cls, chars: Iterable[CharValid]):
        out: list[Char] = []
        append = out.append
        extend = out.extend
        Char_ = Char  # local binding = faster in tight loops

        for c in chars:
            if isinstance(c, Char_):
                append(c)
            elif isinstance(c, str) and len(c) > 1:
                # Only special-case multi-character strings (need flattening)
                extend(map(Char_, c))
            else:
                append(Char_(c))
        return tuple.__new__(cls, out)

    def is_empty(self) -> bool:
        """
        Check if char is empty.
        """
        if len(self) != 0:
            for c in self:
                if not c.is_empty():
                    return False
        return True

    def isascii(self) -> bool:
        """
        Return True if this char is ASCII, False otherwise.

        An ASCII char has a code point in the range U+0000-U+007F. An empty char is ASCII too.
        """
        for c in self:
            if not c.isascii():
                return False
        return True

    def isdecimal(self) -> bool:
        """
        Return True if the char is a decimal, False otherwise.
        """
        for c in self:
            if not c.isdecimal():
                return False
        return True

    def isdigit(self) -> bool:
        """
        Return True if the char is a digit, False otherwise.
        """
        for c in self:
            if not c.isdigit():
                return False
        return True

    def isnumeric(self) -> bool:
        """
        Return True if the char is numeric, False otherwise.
        """
        for c in self:
            if not c.isnumeric():
                return False
        return True

    def isalnum(self) -> bool:
        """
        Return True if the char is alphanumeric, False otherwise.
        """
        for c in self:
            if not c.isalnum():
                return False
        return True

    def isalpha(self) -> bool:
        """
        Return True if the char is alphabetic, False otherwise.
        """
        for c in self:
            if not c.isalpha():
                return False
        return True

    def islower(self) -> bool:
        """
        Return True if the char is lowercase, False otherwise.
        """
        for c in self:
            if not c.islower():
                return False
        return True

    def isupper(self) -> bool:
        """
        Return True if the char is uppercase, False otherwise.
        """
        for c in self:
            if not c.isupper():
                return False
        return True

    def isspace(self) -> bool:
        """
        Return True if the char is whitespace, False otherwise.
        """
        for c in self:
            if not c.isspace():
                return False
        return True

    def isprintable(self) -> bool:
        """
        Return True if this char is printable, False otherwise.

        A character is printable if repr() may use it in its output.
        :return:
        """
        for c in self:
            if not c.isprintable():
                return False
        return True

    def __getitem__(self, key) -> CharSequence | Char:
        value = super().__getitem__(key)
        if isinstance(value, tuple):
            return CharSequence(value)
        return value

    def __add__(self, other) -> CharSequence:
        return CharSequence(super().__add__(other))

    def __mul__(self, value: SupportsIndex) -> CharSequence:
        return CharSequence(super().__mul__(value))

    def __rmul__(self, value: SupportsIndex) -> CharSequence:
        return CharSequence(super().__rmul__(value))

    def __str__(self) -> str:
        string = ""
        for c in self:
            string += str(c)
        return string


class CharIterator(Iterator[Char]):
    """
        Iterates a CharSequence with optional whitespace skipping.

        Semantics:
        - `current` is the last returned character.
        - the iterator starts "before" `start_index`, so the first `next()` returns
            the first character at/after `start_index` (respecting `skip_space`).
        - `eat(ch)` consumes the next character if it equals `ch`.
            If consumed, `ate_next` becomes True and the next call to `next()`
            skips the consumed character and advances to the following one.
        """
    def __init__(
            self,
            chars: Iterable[CharValid],
            *,
            skip_space: bool = False,
            skip_empty: bool = False,
            start_index: int = 0,
    ):
        self._chars: CharSequence = chars if isinstance(chars, CharSequence) else CharSequence(chars)
        self._skip_space = skip_space
        self._skip_empty = skip_empty
        self._pos = start_index-1
        self._ate_next = False

    @property
    def current(self) -> Char:
        """Return the current character or an empty sentinel when out of range."""
        if 0 <= self._pos < self.char_count():
            return self._chars[self._pos]
        return Char(-1)

    @property
    def skip_space(self):
        """Return whether whitespace is skipped during iteration."""
        return self._skip_space

    @property
    def pos(self):
        """Return the current iterator position."""
        return self._pos

    @property
    def ate_next(self):
        """Return whether ``eat`` already consumed the next character."""
        return self._ate_next

    def char_count(self):
        """Return the total number of characters in the source sequence."""
        return len(self._chars)

    def has_current(self):
        """Return whether the iterator currently points at a valid character."""
        return -1 < self._pos < self.char_count()

    def _next_index(self) -> int:
        """Return the next index to consume, respecting skip_space."""
        i = self._pos + 1
        n = self.char_count()
        while i < n:
            if self._skip_empty and self._chars[i].is_empty():
                i += 1
                continue
            if self._skip_space and self._chars[i].isspace():
                i += 1
                continue
            break
        return i

    def has_next(self):
        """Return whether another character can be consumed."""
        return self._next_index() < self.char_count()

    def next_ended(self):
        """Return whether iteration is exhausted and clear any eaten-next flag."""
        if self.has_next():
            return False
        self._ate_next = False
        return True

    def _advance(self) -> Char:
        i = self._next_index()
        if i >= self.char_count():
            self._pos = self.char_count()
            raise StopIteration()
        self._pos = i
        return self.current

    def eat(self, char: CharValid):
        """
        If the next character equals `char`, consume it and return True.
        :param char: The char to check for.
        :return:
        """
        if self.next_ended():
            return False

        i = self._next_index()
        if i >= self.char_count():
            return False

        if self._chars[i] == char:
            self._pos = i
            self._ate_next = True
            return True

        return False

    def next(self):
        """Advance to and return the next available character."""
        if self.next_ended():
            raise StopIteration()

        # If `eat()` consumed a character, we do NOT return it here.
        # We simply clear the flag and advance again.
        if self._ate_next:
            self._ate_next = False

        return self._advance()

    def __next__(self):
        return self.next()

    def for_remaining(self, action: Callable[[Char], bool]):
        """
        Performs the given action for each remaining char until all chars
        have been processed or the action throws an exception.
        :param action: The action to perform.
        :return:
        """
        while self.has_next():
            try:
                action(self.next())
            except StopIteration:
                break

    def peek(self):
        """Return the next available character without consuming it."""
        if self.has_next():
            return self._chars[self._next_index()]
        return None

    def peek_check(self, action: Callable[[Char], bool]):
        """Apply ``action`` to ``peek()`` and return the result."""
        return action(self.peek())

