from re import compile, finditer, DOTALL
from errors_handler import ErrorsHandler
from typing import Tuple, List
from copy import deepcopy
from enum import Enum


class TokenTypes(Enum):
    MAIN = -2
    QUOTATION_MARK = -1
    SKIP = 0
    OP = 1
    NEWLINE = 2
    ENDMARKER = 3
    MISMATCH = 4
    STRING = 5
    NAME = 6
    DOT = 7
    NUMBER = 8
    COMMENT = 9
    TUPLE = 10  # <expression>, <expression>
    PARENTHESIS = 11  # (<expression>)
    SQUARE_BRACKETS = 12  # [<expression>]
    CURLY_BRACES = 13  # {<expression>}


class TokenType:
    type: TokenTypes

    def __init__(self, t: TokenTypes):
        self.type = t

    def __eq__(self, other):
        if isinstance(other, TokenTypes):
            return self.type == other

        return self.type == other.type

    def __ne__(self, other):
        if isinstance(other, TokenTypes):
            return self.type != other

        return self.type != other.type

    def __str__(self):
        return f'TokenType(type={self.type.value} ({self.type.name}))'

    __repr__ = __str__


class DummyToken:
    type: TokenTypes
    value: str | List['Token'] | List[List['Token']]

    def __init__(self, t: TokenTypes | None, value: str | List['Token'] | List[List['Token']]):
        self.type = t
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, TokenType | DummyToken | Token):
            return self.value == other

        if isinstance(other, TokenType):
            return self.type == other.type

        if self.type is None:
            return self.value == other.value

        return self.type == other.type and self.value == other.value

    def __ne__(self, other):
        if not isinstance(other, TokenType | DummyToken | Token):
            return self.value != other

        if isinstance(other, TokenType):
            return self.type != other.type

        if self.type is None:
            return self.value != other.value

        return self.type != other.type or self.value != other.value

    def __str__(self):
        return f'DummyToken(type={self.type.value} ({self.type.name}), value={repr(self.value)})'

    __repr__ = __str__

    def copy(self):
        return deepcopy(self)


class Token:
    type: TokenTypes
    value: str | List['Token'] | List[List['Token']]
    start: Tuple[int, int, int]
    end: Tuple[int, int]
    line: str

    def __init__(
            self,
            t: TokenTypes,
            value: str | List['Token'] | List[List['Token']],
            start: Tuple[int, int, int],
            end: Tuple[int, int],
            line: str
    ):
        self.type = t
        self.value = value
        self.start = start
        self.end = end
        self.line = line

    def __eq__(self, other):
        if isinstance(other, tuple | list):
            for o in other:
                if self != o:
                    return False

            return True

        if not isinstance(other, TokenType | DummyToken | Token):
            return self.value == other

        if isinstance(other, TokenType):
            return self.type == other.type

        return self.type == other.type and self.value == other.value

    def __ne__(self, other):
        if isinstance(other, tuple | list):
            for o in other:
                if self == o:
                    return False

            return True

        if not isinstance(other, TokenType | DummyToken | Token):
            return self.value != other

        if isinstance(other, TokenType):
            return self.type == other.type

        return self.type != other.type or self.value != other.value

    def __str__(self):
        return f'Token(type={self.type.value} ({self.type.name}), value={repr(self.value)}, start={self.start}, end={self.end}, line={repr(self.line)})'

    __repr__ = __str__

    def copy(self):
        return deepcopy(self)


regex_specifications = [
    (TokenTypes.COMMENT, r'--.*'),
    (TokenTypes.QUOTATION_MARK, r'[rRcC]?[\'"]'),
    (TokenTypes.NAME, r'(?![\d_]+)[A-Za-z\d_]+'),
    (TokenTypes.NUMBER, r'(?:0(?:[xX][\dA-Fa-f_]+|[bB][01_]+|[oO][0-7_]+)|(?:'
                        r'\d+\.\d+|\d+)[eE][+-]?\d+'
                        r'|[\d_]*\.[\d_]+'
                        r'|[\d_]+\.[\d_]*'
                        r'|[\d_]+'
                        r')(?:@(?:f(?:32|64)|(?:i|u)(?:8|16|32|64|128)))?'),
    (TokenTypes.DOT, r'\.'),
    (TokenTypes.OP, r'!|\?|@|\$|~|%|\^|&|\-|\+|\*\*|\*|//|/|\||<=>|>=|<=|=>|>|<|==|=|,|:|\(|\)|\[|\]|\{|\}'),
    (TokenTypes.NEWLINE, r'\n'),
    (TokenTypes.SKIP, r'\s+'),
    (TokenTypes.MISMATCH, r'.'),
]
regex = compile('|'.join(['(?P<%s>%s)' % (pair[0].name, pair[1]) for pair in regex_specifications]))


def generate_tokens(s: str, path: str, errors_handler: ErrorsHandler):
    iline = 1
    lines = s.split('\n')

    for i in range(len(lines)):
        lines[i] += '\n'

    tokens = []
    limit = -1

    for mo in finditer(regex, s):
        before_start = len(''.join(lines[:iline - 1]))

        if limit != -1:
            if mo.start() >= limit:
                limit = -1
            else:
                if TokenTypes.__getitem__(mo.lastgroup) == TokenTypes.NEWLINE:
                    iline += 1

                continue

        token = Token(
            TokenTypes.__getitem__(mo.lastgroup),
            mo.group(),
            (iline, mo.start() - before_start, mo.start()),
            (iline, mo.end() - before_start),
            lines[iline - 1]
        )

        if token.type == TokenTypes.QUOTATION_MARK:
            limit = tokenize_str_next(s, path, token, errors_handler)

            if errors_handler.has_errors():
                return []
        elif token.type == TokenTypes.NUMBER:
            value = token.value.split('@')
            value[0] = value[0].replace('_', '').lower()

            if value[0] in ('', '.'):
                errors_handler.final_push_segment(
                    path,
                    'SyntaxError: invalid syntax',
                    token,
                    fill=True,
                    backspace=len('@'.join(value)) - len(value[0])
                )

                if '.' in value[0]:
                    value[0] = '0.0'
                    errors_handler.final_push_segment(
                        path,
                        'if you meant to write a `float` literal, try changing it like this',
                        token,
                        type=ErrorsHandler.HELP,
                        correct='@'.join(value),
                        fill=True,
                        backspace=len('@'.join(value)) - len(value[0])
                    )
                else:
                    value[0] = '0'
                    errors_handler.final_push_segment(
                        path,
                        'if you meant to write a `float` literal, try changing it like this',
                        token,
                        type=ErrorsHandler.HELP,
                        correct='@'.join(value),
                        fill=True,
                        backspace=len('@'.join(value)) - len(value[0])
                    )

                return []

            if len(value[0]) > 1 and value[0][1] in 'bxo':
                value[0] = value[0][:2] + value[0][2:].lstrip('0')
            elif 'e' not in value[0]:
                if value[0].startswith('0') and '.' not in value[0] and value[0].strip('0') != '':
                    errors_handler.final_push_segment(
                        path,
                        'SyntaxError: leading zeros in decimal integer literals are not permitted',
                        token,
                        fill=True,
                        errcode=1
                    )
                    _correct = token.value.split('@')[0]
                    value[0] = _correct[_correct.index(value[0].lstrip('0')[0]):]
                    errors_handler.final_push_segment(
                        path,
                        'try changing it like this',
                        token,
                        type=ErrorsHandler.HELP,
                        correct='@'.join(value),
                        fill=True
                    )
                    return []
                elif value[0].startswith('.'):
                    value[0] = '0' + value[0]
                elif value[0].endswith('.'):
                    value[0] += '0'

            token.value = '@'.join(value)
        elif token.type == TokenTypes.SKIP:
            continue
        elif token.type == TokenTypes.NEWLINE:
            iline += 1

        tokens.append(token)

    tokens.append(Token(TokenTypes.ENDMARKER, '', (iline, 0, len(path)), (iline, 0), ''))

    return tokens


def tokenize_str_next(s: str, path: str, token: Token, errors_handler: ErrorsHandler) -> int:
    quotation_type = token.value[-1]
    _s = s[token.start[2] + len(token.value):]
    prefix = token.value[:-1]
    value = token.value
    value_len = 0

    if len(_s) == 0:
        errors_handler.final_push_segment(path, f'SyntaxError: `{quotation_type}` is never closed here', token)
        errors_handler.final_push_segment(
            path,
            f'just insert `{quotation_type}` to the end',
            token,
            type=ErrorsHandler.HELP,
            correct=token.value + quotation_type,
            offset=1
        )
        return 0

    line_i = 0
    neg_i = 0
    i = 0
    while i < len(_s):
        next = None if i == len(_s) - 1 else _s[i + 1]

        if _s[i] in ('\'', '\"'):
            if quotation_type == _s[i]:
                i += 1
                break
            else:
                value += '\\' + _s[i]
                value_len += 1
        elif _s[i] == '\\':
            if next is not None and (
                    next == quotation_type or ('r' not in prefix and next in '\'"rnt')
            ):
                value += _s[i] + next
                i += 1
                value_len += 1
            elif next is not None:
                value += '\\\\' + next
                value_len += 2
                i += 1
            else:
                _token = token.copy()
                _token.start = (token.start[0], token.start[1] + i + 1 - neg_i, token.start[2] + i + 1)
                _token.end = (token.end[0], token.end[1] + i + 1 - neg_i)

                if line_i > 0:
                    _token.line = s.split('\n')[token.start[0] + line_i - 1]

                errors_handler.final_push_segment(path, f'SyntaxError: invalid backslash character', _token)
                errors_handler.final_push_segment(
                    path,
                    f'if you meant to write a backslash, specify it twice `\\\\` or put `r` before the quotes',
                    token,
                    type=ErrorsHandler.HELP,
                    correct=None
                )
        elif _s[i] == '\n':
            neg_i += len(s.split('\n')[token.start[0] + line_i - 1]) + 2
            line_i += 1
            errors_handler.final_push_segment(path, f'SyntaxError: `{quotation_type}` is never closed here', token)
        else:
            value += _s[i]
            value_len += 1

        i += 1

    i -= 1

    if _s[i] != quotation_type:
        token.end = (token.end[0], token.end[1] + i + 1)
        errors_handler.final_push_segment(path, f'SyntaxError: `{quotation_type}` is never closed here', token)
        errors_handler.final_push_segment(
            path,
            f'insert `{quotation_type}` to the end',
            token,
            type=ErrorsHandler.HELP,
            correct=prefix + quotation_type + _s[:i + 1] + quotation_type,
            offset=len(prefix + _s[:i + 1]) + 1
        )
        return 0

    if prefix == 'c' and value_len != 1:
        if value_len == 0:
            errors_handler.final_push_segment(
                path,
                'SyntaxError: empty character literal',
                token,
                offset=2
            )
        else:
            errors_handler.final_push_segment(
                path,
                'SyntaxError: character literal may only contain one codepoint',
                token,
                offset=1,
                fill=True
            )
        errors_handler.final_push_segment(
            path,
            f'if you meant to write a `str` literal, remove `c` before quotes',
            token,
            type=ErrorsHandler.HELP,
            correct=quotation_type + _s[:i + 1],
            fill=True
        )

    token.value = value + quotation_type
    token.type = TokenTypes.STRING
    token.end = (token.end[0], token.end[1] + len(token.value) - len(prefix) - 1)

    return token.start[2] + i + 2 + len(prefix)


def _get_prevbody(_main_body: DummyToken, _current_body: DummyToken | Token) -> DummyToken | Token:
    if _main_body is _current_body:
        return _main_body

    body = _main_body

    prev = body
    while isinstance(body.value, list) and body is not _current_body:
        if len(body.value) >= 2 and isinstance(body.value[-2], list):
            if not isinstance(body.value[-2][-1].value, list):
                break

            prev = body
            body = body.value[-2][-1]
        elif body.value[-1].type == TokenTypes.ENDMARKER:
            prev = body
            body = body.value[-2]
        else:
            prev = body
            body = body.value[-1]

    return prev


BRACKETS = {
    '(': TokenTypes.PARENTHESIS,
    ')': TokenTypes.PARENTHESIS,
    '[': TokenTypes.SQUARE_BRACKETS,
    ']': TokenTypes.SQUARE_BRACKETS,
    '{': TokenTypes.CURLY_BRACES,
    '}': TokenTypes.CURLY_BRACES,
}


def _append(_current_body: DummyToken | Token, _token: DummyToken | Token):
    if _current_body.value and isinstance(_current_body.value[-1], list):
        _current_body.value[-1].append(_token)
    else:
        _current_body.value.append(_token)


def compose_tokens(s: str, path: str, tokens: List[Token], errors_handler: ErrorsHandler):
    main_body = DummyToken(TokenTypes.MAIN, [])
    current_body = main_body

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.type == TokenTypes.OP and token.value in '(){}[],':
            if token.value == ',':
                if current_body.type == TokenTypes.TUPLE:
                    if not current_body.value[-1]:
                        errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
                        return []

                    current_body.value.append([])
                else:
                    if not current_body.value:
                        errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
                        return []

                    _token = Token(TokenTypes.TUPLE, [current_body.value, []], (0, 0, 0), (0, 0), '')
                    current_body.value = [_token]
                    current_body = _token
            elif token.value in '([{':
                _token = token.copy()
                _token.type = BRACKETS[token.value]
                _token.value = []
                _append(current_body, _token)
                current_body = _token
            elif token.value in ')]}':
                if current_body is main_body or (
                        current_body.type == TokenTypes.TUPLE and _get_prevbody(main_body, current_body) is main_body
                ):
                    errors_handler.final_push_segment(path, f'SyntaxError: unmatched `{token.value}`', token)
                    _expected = list(BRACKETS.keys())[list(BRACKETS.keys()).index(token.value) - 1]
                    errors_handler.final_push_segment(
                        path,
                        f'just remove `{token.value}` or insert `{_expected}` to the beginning of expression',
                        token,
                        type=ErrorsHandler.HELP,
                        correct=None
                    )
                    return []

                if (
                        current_body.type != TokenTypes.TUPLE and
                        current_body.type != BRACKETS[token.value]
                ) or (
                        current_body.type == TokenTypes.TUPLE and
                        _get_prevbody(main_body, current_body).type != BRACKETS[token.value]
                ):
                    if current_body.type == TokenTypes.TUPLE:
                        current_body = _get_prevbody(main_body, current_body)

                    _expected = list(BRACKETS.keys())[list(BRACKETS.values()).index(current_body.type) + 1]

                    errors_handler.final_push_segment(
                        path,
                        f'SyntaxError: expected closing parenthesis \'{_expected}\' but got \'{token.value}\'',
                        token
                    )
                    errors_handler.final_push_segment(
                        path,
                        f'just remove `{token.value}` to `{_expected}`',
                        token,
                        type=ErrorsHandler.HELP,
                        correct=_expected
                    )
                    return []

                if current_body.type == TokenTypes.TUPLE:
                    _current_body = current_body
                    current_body = _get_prevbody(main_body, current_body)

                    _current_body.end = current_body.end = token.end
                    _current_body.line = current_body.line = '\n'.join(
                        s.split('\n')[current_body.start[0] - 1:current_body.end[0]]
                    )
                else:
                    current_body.end = token.end
                    current_body.line = '\n'.join(s.split('\n')[current_body.start[0] - 1:current_body.end[0]])

                current_body = _get_prevbody(main_body, current_body)

            i += 1
            continue
        elif token.type == TokenTypes.COMMENT:
            i += 1
            continue
        elif token.type == TokenTypes.MISMATCH:
            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
            return []
        elif token.type == TokenTypes.NEWLINE and (
                current_body.type in (TokenTypes.PARENTHESIS, TokenTypes.SQUARE_BRACKETS)
                or (
                        current_body.type == TokenTypes.TUPLE and
                        _get_prevbody(main_body, current_body).type in (
                                TokenTypes.PARENTHESIS,
                                TokenTypes.SQUARE_BRACKETS
                        )
                )
                or (i > 0 and tokens[i - 1].type == TokenTypes.NEWLINE)
        ):
                i += 1
                continue
        elif token.type == TokenTypes.ENDMARKER:
            main_body.value.append(token)
            break

        # current_body.value.append(token)
        _append(current_body, token)

        i += 1

    if (
            current_body.type != TokenTypes.TUPLE and current_body is not main_body
    ) or (
            current_body.type == TokenTypes.TUPLE and _get_prevbody(main_body, current_body) is not main_body
    ):
        if current_body.type == TokenTypes.TUPLE:
            current_body = _get_prevbody(main_body, current_body)

        errors_handler.final_push_segment(path, 'SyntaxError: is never closed', current_body)
        _got = list(BRACKETS.keys())[list(BRACKETS.values()).index(current_body.type)]
        _expected = list(BRACKETS.keys())[list(BRACKETS.values()).index(current_body.type) + 1]
        errors_handler.final_push_segment(
            path,
            f'just remove `{_got}` or insert `{_expected}` to the end of expression',
            current_body,
            type=ErrorsHandler.HELP,
            correct=None
        )
        return []

    return main_body.value


def view_in_file(token: Token) -> str:
    _lines = token.line.split('\n')
    _lines[0] = _lines[0][token.start[1]:]
    _lines[-1] = _lines[-1][:token.start[1]]
    return '\n'.join(_lines)


if __name__ == '__main__':
    with open('test.cft', 'r', encoding='utf-8') as f:
        file = f.read()

    errors_handler = ErrorsHandler()
    tokens = generate_tokens(file, 'test.cft', errors_handler)
    print('First stage:', tokens)

    if errors_handler.has_errors() or errors_handler.has_warnings():
        errors_handler.print()
    else:
        print('Second stage:',
              compose_tokens(file, 'test.cft', tokens, errors_handler))

        if errors_handler.has_errors() or errors_handler.has_warnings():
            errors_handler.print()
