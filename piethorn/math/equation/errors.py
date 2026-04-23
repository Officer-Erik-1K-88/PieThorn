class ParseError(RuntimeError):
    """The generic exception raised when parsing fails."""


class SyntaxParseError(ParseError):
    """Exception raised when syntax is invalid when parsing."""

class ChildError(RuntimeError):
    """Exception raised when a child parse scope doesn't exist."""