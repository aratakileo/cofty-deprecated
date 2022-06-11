from lexermod.cft_token import TokenTypes, Token, LiteralToken, NumberToken, AnyToken, DummyToken
from lexermod.cft_regex import regex
from handler import Handler
from re import finditer


def get_str_token(token: Token, handler: Handler):
    quote = token.value[-1]  # `'` or `"`
    prefix = token.value[0].lower()
    prefix = '' if prefix in '\'\"' else prefix

    abs_start_char_index = len('\n'.join(doc.split('\n')[:token.start[0]])) + token.start[1]  # char index in doc
    doc_after_quote = handler.current_doc[abs_start_char_index:]

    if doc_after_quote.startswith('\n') or doc_after_quote.startswith(' '):
        abs_start_char_index += 1
        doc_after_quote = doc_after_quote[1:]

    doc_after_quote = doc_after_quote[len(prefix) + len(quote):]

    is_char = prefix == 'c'

    value = prefix + quote
    literal_value = ''

    if len(doc_after_quote) == 0:
        handler.error_handler.push_problem_by_token_data(
            f'SyntaxError: `{quote}` is never closed here',
            handler.current_doc,
            token.value,
            (token.start[0], token.start[1] + len(value)),
            (token.start[0], 0)
        )
        handler.error_handler.push_problem_by_token(
            token,
            f'just insert `{quote}` to the end',
            handler.current_doc,
            correct_token_value=prefix + quote * 2,
            type=ErrorHandler.ProblemType.HELP,
            point_off=1 + len(prefix)
        )
        return None

    k = 0
    while k < len(doc_after_quote):
        nextchar = None if k == len(doc_after_quote) - 1 else doc_after_quote[k + 1]
        char = doc_after_quote[k]
        value += char

        if char in '\'\"':
            if quote == char:
                k += 1
                break
        elif char == '\\':
            if nextchar is None:
                handler.error_handler.push_problem_by_token_data(
                    f'SyntaxError: invalid backslash character',
                    handler.current_doc,
                    token.value,
                    (token.start[0], token.start[1] + len(value)),
                    (token.start[0], 0)
                )
                handler.error_handler.push_problem_by_token_data(
                    f'if you meant to write a backslash, specify it twice `\\\\`',
                    handler.current_doc,
                    token.value + value,
                    (token.start[0], token.start[1]),
                    (token.start[0], 0),
                    correct_token_value=value + '\\',
                    fill_point=True,
                    point_off=len(value) - 1,
                    fill_point_right_off=-len(value) + 1,
                    type=ErrorHandler.ProblemType.NOTE
                )
                return None

            value += nextchar

            if nextchar == char or ('r' not in prefix and nextchar in '\'\"rnt'):
                literal_value += char + nextchar
            else:
                literal_value += char * 2 + nextchar
            k += 1
        elif char == '\n':
            handler.error_handler.push_problem_by_token_data(
                f'SyntaxError: `{quote}` is never closed here',
                handler.current_doc,
                token.value,
                (token.start[0], token.start[1] + len(value) - (value[-1] == '\n')),
                (token.start[0], 0)
            )
            handler.error_handler.push_problem_by_token_data(
                f'just insert `{quote}` to the end',
                handler.current_doc,
                token.value + value,
                (token.start[0], token.start[1]),
                (token.start[0], 0),
                correct_token_value=value[:-1].rstrip('\n') + quote,
                point_off=len(value) - (value[-1] == '\n'),
                type=ErrorHandler.ProblemType.HELP
            )
            handler.error_handler.push_problem_by_token_data(
                f'if you mean newline character, replace it to `\\n` and insert at the end `{quote}`',
                handler.current_doc,
                token.value + value,
                (token.start[0], token.start[1]),
                (token.start[0], 0),
                correct_token_value=value[:-1].rstrip('\n') + '\\n' + quote,
                fill_point=True,
                point_off=len(value) - len(quote) - (value[-1] == '\n') + 1,
                fill_point_right_off=-len(value) + (value[-1] == '\n'),
                type=ErrorHandler.ProblemType.NOTE
            )
            return None
        else:
            literal_value += char

        k += 1

    if value[-1] != quote:
        handler.error_handler.push_problem_by_token_data(
            f'SyntaxError: `{quote}` is never closed here',
            handler.current_doc,
            token.value + value,
            (token.start[0], token.start[1]),
            (token.start[0], 0),
            point_off=len(value) - (value[-1] == '\n')
        )
        handler.error_handler.push_problem_by_token_data(
            f'just insert `{quote}` to the end',
            handler.current_doc,
            token.value + value,
            (token.start[0], token.start[1]),
            (token.start[0], 0),
            correct_token_value=value.rstrip('\n') + quote,
            point_off=len(value) - (value[-1] == '\n'),
            type=ErrorHandler.ProblemType.HELP
        )
        return None

    clean_value = value[1 + len(prefix):-1]
    clean_value_len = len(clean_value)
    if is_char and clean_value_len != 1:
        if clean_value_len == 0:
            handler.error_handler.push_problem_by_token_data(
                f'SyntaxError: empty character literal',
                handler.current_doc,
                value,
                (token.start[0], token.start[1]),
                (token.start[0], 0),
                fill_point=True
            )
        elif clean_value[1:] not in '\'\"rnt\\':
            handler.error_handler.push_problem_by_token_data(
                f'SyntaxError: character literal may only contain one codepoint',
                handler.current_doc,
                value,
                (token.start[0], token.start[1]),
                (token.start[0], 0),
                fill_point=True
            )

        if handler.error_handler.has_errors():
            handler.error_handler.push_problem_by_token_data(
                f'if you meant to write a `str` literal, remove `c` before quotes',
                handler.current_doc,
                token.value + value,
                (token.start[0], token.start[1]),
                (token.start[0], 0),
                correct_token_value=value[1:],
                fill_point=True,
                type=ErrorHandler.ProblemType.NOTE
            )
            return None

    return LiteralToken(
        value,
        literal_value,
        token.start,
        (
            token.end[0],
            token.start[1] + len(value)
        ),
        is_char
    )


MAX_NUM = {
    'i8': 0x7f,
    'i16': 0x7fff,
    'i32': 0x7fffff,
    'i64': 0x7fffffff,
    'i128': 0x7fffffffff,
    'u8': 0xff,
    'u16': 0xffff,
    'u32': 0xffffff,
    'u64': 0xffffffff,
    'u128': 0xffffffffff,
    'f32': 3.40282347e+38,
    'f64': 1.7976931348623157e+308,
}

MIN_NUM = {
    'i8': ~0x7f,
    'i16': ~0x7fff,
    'i32': ~0x7fffff,
    'i64': ~0x7fffffff,
    'i128': ~0x7fffffffff,
    'u8': 0,
    'u16': 0,
    'u32': 0,
    'u64': 0,
    'u128': 0,
    'f32': -3.40282347e+38,
    'f64': -1.7976931348623157e+308,
}


def get_number_token(token: Token, handler: Handler):
    value, expected_type, *_ = (*token.value.split('@'), '', '')
    value = value.replace('_', '').lower()

    if value == '.':
        handler.error_handler.push_problem_by_token(token, 'SyntaxError: invalid syntax', handler.current_doc)
        return None

    if '.' in token.value or 'e' in token.value:
        value = float(value)
    elif len(value) > 2 and value[1] in 'xbo':
        value = int(value[2:], {'x': 16, 'b': 2, 'o': 8}[value[1]])
    else:
        value = int(value)

    str_value = str(value)

    if str_value == 'inf':
        str_value = 'toolong'
    elif str_value == '-inf':
        str_value = 'tooshort'

    if expected_type:
        value_type = expected_type

        is_maximum_problem = value > 0 and expected_type[0] == 'u' or value >= 0 and expected_type[0] != 'u'

        if is_maximum_problem and MAX_NUM[expected_type] < value \
                or not is_maximum_problem and MIN_NUM[expected_type] > value:
            handler.error_handler.push_problem_by_token(
                token,
                f'ValueError: the value is {"greater" if is_maximum_problem else "less"} than specified',
                handler.current_doc,
                fill_point=True
            )
            handler.error_handler.push_problem(
                problem=f'got number `{str_value}`, '
                        f'but {"maximum" if is_maximum_problem else "minimum"} allowed value for type `{expected_type}` '
                        f'is `{MAX_NUM[expected_type] if is_maximum_problem else MIN_NUM[expected_type]}`',
                type=ErrorHandler.ProblemType.NOTE
            )
            return None
    else:
        greater_max_value = False
        value_type = ''

        if isinstance(value, int):
            for _type in 'i8', 'i16', 'i32', 'i64':
                if 0 <= value <= MAX_NUM[_type] or MIN_NUM[_type] <= value < 0:
                    value_type = _type
                    break

            if not value_type:
                value_type = 'i64'
                greater_max_value = True
        else:
            for _type in 'f32', 'f64':
                if 0 <= value <= MAX_NUM[_type] or MIN_NUM[_type] <= value < 0:
                    value_type = _type
                    break

            if not value_type:
                value_type = 'f64'
                greater_max_value = True

        if greater_max_value:
            handler.error_handler.push_problem_by_token(
                token,
                f'ValueError: the value is {"greater" if value >= 0 else "less"} '
                f'than the {"maximum" if value >= 0 else "minimum"} allowed',
                handler.current_doc,
                fill_point=True
            )
            handler.error_handler.push_problem(
                problem=f'got number `{str_value}`, '
                        f'but {"maximum" if value >= 0 else "minimum"} allowed value for type `{value_type}` '
                        f'is `{MAX_NUM[value_type] if value >= 0 else MIN_NUM[value_type]}`',
                type=ErrorHandler.ProblemType.NOTE
            )
            return None

    return NumberToken(token.value, value, token.start, token.end, value_type)


def generate_base_tokens(handler: Handler):
    line_index = 0
    lines = handler.current_doc.split('\n')

    for i in range(len(lines)):
        lines[i] += '\n'

    tokens = []
    limit = -1

    for mo in finditer(regex, handler.current_doc):
        before_start = len(''.join(lines[:line_index]))

        if limit != -1:
            if mo.start() >= limit:
                limit = -1
            else:
                if TokenTypes.__getitem__(mo.lastgroup) == TokenTypes.NEWLINE:
                    line_index += 1

                continue

        token = Token(
            TokenTypes.__getitem__(mo.lastgroup),
            mo.group(),
            (line_index, mo.start() - before_start),
            (line_index, mo.end() - before_start)
        )

        if token.type in (TokenTypes.SKIP, TokenTypes.COMMENT):
            continue
        elif token.type == TokenTypes.QUOTATION_MARK:
            token = get_str_token(token, handler)

            if token is None:
                return []

            limit = mo.start() + token.end[1] - token.start[1]
        elif token.type == TokenTypes.NUMBER:
            token = get_number_token(token, handler)

            if token is None:
                return []
        elif token.type == TokenTypes.NEWLINE:
            line_index += 1
        elif token.type == TokenTypes.MISMATCH:
            handler.error_handler.push_problem_by_token(
                token,
                f'SyntaxError: missmatch `{token.value}`',
                handler.current_doc
            )
            return []

        tokens.append(token)

    tokens.append(Token(TokenTypes.ENDMARKER, 'ENDMARKER', (line_index, 0), (line_index, 0)))

    return tokens


def compose_tokens(tokens: list[AnyToken], handler: Handler):
    # method is not ended

    def get_prevbody():
        current = main_body
        prev = main_body

        while id(current) != id(current_body):
            prev = current
            current = current.value[-1]

        return prev

    def append_to_body(token: AnyToken):
        if current_body.value and isinstance(current_body.value[-1], list):
            current_body.value[-1].append(token)
            return

        current_body.value.append(token)

    main_body = DummyToken(TokenTypes.MAIN, [])
    current_body = main_body

    for i in range(len(tokens)):
        token = tokens[i]

        if token.type == TokenTypes.OP:
            if token.value == ',':
                if current_body.type == TokenTypes.TUPLE:
                    if not current_body.value[-1]:
                        handler.error_handler.push_problem_by_token(
                            token,
                            'SyntaxError: invalid syntax',
                            handler.current_doc
                        )
                        return []

                    current_body.value.append([])
                else:
                    if not current_body.value:
                        handler.error_handler.push_problem_by_token(
                            token,
                            'SyntaxError: invalid syntax',
                            handler.current_doc
                        )
                        return []

                    current_body.value = [DummyToken(TokenTypes.TUPLE, [current_body.value, []])]
                    current_body = current_body.value[0]
            elif token.value in '({[':
                body_token = Token(
                    {
                        '(': TokenTypes.PARENTHESIS,
                        '{': TokenTypes.CURLY_BRACES,
                        '[': TokenTypes.SQUARE_BRACKETS,
                    }[token.value],
                    [],
                    token.start,
                    token.end
                )

                append_to_body(body_token)

                current_body = body_token
            elif token.value in ']})':
                if current_body is main_body or current_body.type == TokenTypes.TUPLE and get_prevbody() is main_body:
                    handler.error_handler.push_problem_by_token(
                        token,
                        f'SyntaxError: unmatched `{token.value}`',
                        handler.current_doc
                    )
                    handler.error_handler.push_problem(
                        problem=f'just remove `{token.value}` or insert `'
                                + {
                                    ']': '[',
                                    '}': '{',
                                    ')': '(',
                                }[token.value] +
                                f'` to the beginning of expression',
                        type=ErrorHandler.ProblemType.HELP
                    )
                    return []

                bracket_type = {
                        ')': TokenTypes.PARENTHESIS,
                        '}': TokenTypes.CURLY_BRACES,
                        ']': TokenTypes.SQUARE_BRACKETS,
                    }[token.value]

                if current_body.type != TokenTypes.TUPLE and current_body.type != bracket_type\
                        or current_body.type == TokenTypes.TUPLE and get_prevbody().type != bracket_type:
                    if current_body.type == TokenTypes.TUPLE:
                        current_body = get_prevbody()

                    expected = {
                        TokenTypes.SQUARE_BRACKETS: ']',
                        TokenTypes.CURLY_BRACES: '}',
                        TokenTypes.PARENTHESIS: ')',
                    }[current_body.type]

                    handler.error_handler.push_problem_by_token(
                        token,
                        f'SyntaxError: expected closing parenthesis \'{expected}\' but got \'{token.value}\'',
                        handler.current_doc
                    )
                    handler.error_handler.push_problem_by_token(
                        token,
                        f'just remove `{token.value}` to `{expected}`',
                        handler.current_doc,
                        type=ErrorHandler.ProblemType.HELP,
                        correct_token_value=expected
                    )
                    return []

                if current_body.type == TokenTypes.TUPLE:
                    next_body = current_body
                    current_body = get_prevbody()

                    next_body.end = current_body.end = token.end
                else:
                    current_body.end = token.end

                current_body = get_prevbody()
        elif token.type == TokenTypes.ENDMARKER:
            main_body.value.append(token)
            break
        else:
            append_to_body(token)

    return main_body.value


__all__ = (
    'generate_base_tokens',
    'compose_tokens',
)

if __name__ == '__main__':
    from error_handler import ErrorHandler

    with open('../test.cft', 'r', encoding='utf-8') as f:
        doc = f.read()

    handler = Handler(doc, '../test.cft', ErrorHandler())
    tokens = generate_base_tokens(handler)

    if handler.error_handler.has_errors():
        handler.error_handler.print()
    else:
        tokens = compose_tokens(tokens, handler)
        handler.error_handler.print()

    print(tokens)
