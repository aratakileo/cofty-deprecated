from copy import deepcopy
from enum import Enum


class TokenTypes(Enum):
    MAIN            = -2  # temp token
    QUOTATION_MARK  = -1  # temp token
    SKIP            = 0
    COMMENT         = 1
    OP              = 2
    NEWLINE         = 3
    ENDMARKER       = 4
    MISMATCH        = 5
    STRING          = 6
    NAME            = 7
    NUMBER          = 8
    TUPLE           = 9   # <expression>, <expression>
    PARENTHESIS     = 10  # (<expression>)
    SQUARE_BRACKETS = 11  # [<expression>]
    CURLY_BRACES    = 12  # {<expression>}


class AnyToken:
    type: TokenTypes
    value: list | str

    def copy(self):
        return deepcopy(self)

    def __eq__(self, other):
        return self.type, self.value == other.type, other.value

    def __ne__(self, other):
        return not (self == other)


class DummyToken(AnyToken):
    def __init__(self, _type: TokenTypes, value: list | str):
        self.type, self.value = _type, value

    def __str__(self):
        return f'DummyToken(type={self.type.value} ({self.type.name}), value={repr(self.value)})'

    __repr__ = __str__


class TokenType(AnyToken):
    type: TokenTypes
    value: str | list
    start: tuple[int, int]  # (line index, char index)
    end: tuple[int, int]    # (line index, char index)

    def __eq__(self, other):
        return self.type, self.value, self.start, self.end == other.type, other.value, other.start, other.end


class Token(TokenType):
    def __init__(
            self,
            _type: TokenTypes,
            value: str | list,
            start: tuple[int, int],
            end: tuple[int, int]
    ):
        self.type = _type
        self.value = value
        self.start = start
        self.end = end

    def __str__(self):
        return f'Token(type={self.type.value} ({self.type.name}), value={repr(self.value)}, start={self.start}, end={self.end})'

    __repr__ = __str__


class LiteralToken(TokenType):
    def __init__(
            self,
            value: str,
            literal_value: str,
            start: tuple[int, int],
            end: tuple[int, int],
            is_char: bool
    ):
        self.literal_value = literal_value
        self.is_char = is_char
        self.value = value
        self.start = start
        self.end = end

    @property
    def type(self):
        return TokenTypes.STRING

    def __str__(self):
        return f'LiteralToken(type={self.type.value} ({self.type.name}), value={repr(self.value)}, literal_value={repr(self.literal_value)}, start={self.start}, end={self.end}, is_char={self.is_char})'

    __repr__ = __str__


class NumberToken(TokenType):
    def __init__(
            self,
            value: str,
            number_value: float,
            start: tuple[int, int],
            end: tuple[int, int],
            value_type: str
    ):
        self.number_value = number_value
        self.value_type = value_type
        self.value = value
        self.start = start
        self.end = end

    @property
    def type(self):
        return TokenTypes.NUMBER

    def __str__(self):
        return f'NumberToken(type={self.type.value} ({self.type.name}), value={repr(self.value)}, number_value={self.number_value}, start={self.start}, end={self.end}, value_type={repr(self.value_type)})'

    __repr__ = __str__


__all__ = (
    'TokenTypes',
    'AnyToken',
    'TokenType',
    'DummyToken',
    'Token',
    'LiteralToken',
    'NumberToken',
)
