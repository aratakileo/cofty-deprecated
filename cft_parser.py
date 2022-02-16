from cft_lexer import Token, TokenTypes, DummyToken, TokenType
from errors_handler import ErrorsHandler
from typing import List, Tuple


# def compile_num(num: str):
#     value = num.split('@')
#
#     if len(value[0]) > 1 and value[0][1] in ('b', 'B', 'x', 'X', 'o', 'O'):
#         if value[0][1] in ('b', 'B'):
#             number_sys = 2
#         elif value[0][1] in ('o', 'O'):
#             number_sys = 8
#         else:
#             number_sys = 16
#
#         value[0] = str(int(value[0][2:], number_sys))
#
#     return '@'.join(value)
#
#
# def get_num_max(type: str):
#     bits = int(type[1:])
#
#     if type[0] == 'i':
#         bits -= 1
#
#     return int('1' * bits, 2)
#
#
# def get_num_min(type: str):
#     return 0 if type[0] == 'u' else -get_num_max(type)


def _compile_num(num: str):
    if len(num) > 1 and num[1] in 'bBxXoO':
        if num[1] in 'bB':
            number_sys = 2
        elif num[1] in 'oO':
            number_sys = 8
        else:
            number_sys = 16

        return str(int(num[2:], number_sys))

    return num


MAX_NUM_SIZE = {
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


def _get_num_type(num: str):
    if '@' in num:
        return num.split('@')[1]

    cnum = float(_compile_num(num))

    if '.' in num or 'e' in num or 'E' in num:
        return 'f32' if cnum <= MAX_NUM_SIZE['f32'] else 'f64'

    for t in ('i8', 'i16', 'i32', 'i64', 'i128'):
        if cnum <= MAX_NUM_SIZE[t]:
            return t

    return 'u128'


def _is_type_expression(token: Token) -> bool:
    if token.type == TokenTypes.NAME:
        return True

    return False


# left operators: <op> <expr>
LOPS = ['+', '-', '*', '~', 'not']

# <expr> <op> <expr>
MIDDLE_OPS = [
    *LOPS[:3],
    '**', '|', '&', '<<', '>>', '%', '==', '<=', '>=', '>', '<', 'or', 'and', 'in', 'not in', 'is', 'is not'
]

# all user's operators
OPS = list(set(LOPS) | set(MIDDLE_OPS))

# operators that are always return type `bool`
BOOL_OPS = ('not', 'or', 'and', 'in', 'not in', 'is', 'is not', '==', '<=', '>=', '<', '>')


def _is_op(token: Token):
    return token.type in (TokenTypes.OP, TokenTypes.NAME) and token.value in OPS


# that names can not be used like a variable's, a function's name etc.
KEYWORDS = ['if', 'else', 'elif', 'let', 'var', 'True', 'False']


def _is_kw(token: Token, kws=()):
    if len(kws) != 0:
        return _is_kw(token) and token.value in kws

    return token.type == TokenTypes.NAME and token.value in KEYWORDS or token.value in OPS


def _is_value_expression(
        tokens: List[Token] | Token,
        i: int = 0,
        stop_tokens: Tuple[DummyToken | TokenType] = ...
) -> bool:
    """<expr>"""
    if isinstance(tokens, Token):
        tokens = [tokens]

    if i >= len(tokens):
        return False

    tokens = tokens[i:]

    if stop_tokens is ...:
        stop_tokens = (TokenType(TokenTypes.ENDMARKER), TokenType(TokenTypes.NEWLINE))

    for k in range(len(tokens)):
        if tokens[k] in stop_tokens:
            tokens = tokens[:k]
            break

    if len(tokens) >= 1:
        if len(tokens) == 1:
            if tokens[0].type in (TokenTypes.NUMBER, TokenTypes.STRING):
                return True

            if tokens[0].type == TokenTypes.NAME and (not _is_kw(tokens[0]) or tokens[0].value in ('True', 'False')):
                return True

            if tokens[0].type == TokenTypes.TUPLE:
                for item in tokens[0].value:
                    if not _is_value_expression(item):
                        return False

                return True

            if tokens[0].type in (TokenTypes.PARENTHESIS, TokenTypes.SQUARE_BRACKETS, TokenTypes.CURLY_BRACES):
                return not tokens[0].value or _is_value_expression(tokens[0].value)
        elif _is_op(tokens[0]) and not _is_op(tokens[1]) and _is_value_expression(tokens, 1):
            if tokens[0].value not in LOPS: return False
            return True
        elif len(tokens) >= 3 and not _is_op(tokens[0]) and _is_op(tokens[1]) \
                and _is_value_expression(tokens[0]) and _is_value_expression(tokens, 2):
            return True

    return False


MIDDLE_OPS_PRIORITY = {
    'is': 0,
    'is not': 0,
    'and': 1,
    'or': 1,
    '==': 2,
    '!=': 2,
    '>=': 2,
    '<=': 2,
    '<': 2,
    '>': 2,
    'in': 3,
    'not in': 3,
    '|': 4,
    '&': 4,
    '>>': 5,
    '<<': 5,
    '%': 5,
    '-': 6,
    '+': 6,
    '//': 7,
    '/': 7,
    '*': 7,
    '**': 8
}


def _get_returned_type(obj: dict):
    return obj['returned-type'] if obj['returned-type'] != '$self' else obj['type']


def _generate_expression_syntax_object(
        tokens: List[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        i: int = 0,
        right_i: int = 0,
        stop_tokens: Tuple[DummyToken | TokenType] = ...,
        expected_type: dict | str = ...
):
    if isinstance(tokens, Token):
        tokens = [tokens]

    tokens = tokens[i:]

    if stop_tokens is ...:
        stop_tokens = (TokenType(TokenTypes.ENDMARKER), TokenType(TokenTypes.NEWLINE))

    for k in range(len(tokens)):
        if tokens[k] in stop_tokens:
            tokens = tokens[:k]
            break

    tokens = tokens[:len(tokens) - right_i]

    res = {
        '$tokens-len': len(tokens),  # temp value
        'tokens': tokens
    }

    if len(tokens) == 1:
        res['returned-type'] = '$self'  # it is necessary to refer to key 'type'

        token = tokens[0]

        if token.type == TokenTypes.STRING:
            # includes strings like `'Hello World'` or `"Hello World"`, and chars like `c'H'` or `c"H"`

            _index = token.value.index(token.value[-1])

            res.update({
                'type': 'string' if 'c' not in token.value[:_index].lower() else 'char',  # `c` is prefix before quotes
                'value': token.value[_index + 1:-1]
            })
        elif token.type == TokenTypes.NUMBER:
            # includes any number format like integer or decimal

            res.update({
                'type': 'number',
                'value': token.value,
                'returned-type': _get_num_type(token.value)
            })
        elif token.type == TokenTypes.NAME:
            res['value'] = token.value

            if token.value in ('True', 'False'):
                res['type'] = 'bool'
            else:
                res['type'] = 'name'
                res['returned-type'] = '$undefined'  # that type mean unpredictable behavior
        elif token.type == TokenTypes.TUPLE:
            # <expression>, <expression>

            res.update({
                'type': 'tuple',
                'value': []
            })

            for item in token.value:
                res['value'].append(_generate_expression_syntax_object(item, errors_handler, path))

                del res['value'][-1]['$tokens-len']
        elif token.type in (TokenTypes.PARENTHESIS, TokenTypes.SQUARE_BRACKETS, TokenTypes.CURLY_BRACES):
            if not token.value:
                res.update({
                    'type': {
                        TokenTypes.PARENTHESIS: 'tuple',
                        TokenTypes.SQUARE_BRACKETS: 'list',
                        TokenTypes.CURLY_BRACES: 'dict'
                    }[token.type],
                    'value': []
                })
            else:
                res = _generate_expression_syntax_object(token.value, errors_handler, path)

                if token.type != TokenTypes.PARENTHESIS:
                    res['type'] = 'list' if token.type == TokenTypes.SQUARE_BRACKETS else 'set'

                    if res['type'] != 'tuple':
                        res['value'] = [res['value']]
    else:
        invalid_lvalue = {
            'type': 'op'
        }
        last_lvalue = invalid_lvalue

        i = 0
        while _is_op(tokens[i]):
            last_lvalue.update({
                'op': tokens[i].value,
                'value': {'type': 'op'}
            })
            last_lvalue = last_lvalue['value']

            i += 1

        if 'value' not in last_lvalue:
            last_lvalue.update(_generate_expression_syntax_object(tokens[i], errors_handler, path))

        tokens = tokens[i:]

        del last_lvalue['$tokens-len']

        if len(tokens) == 1:
            res.update(invalid_lvalue)
        else:
            invalid_rvalue = _generate_expression_syntax_object(tokens, errors_handler, path, 2)

            del invalid_rvalue['$tokens-len']

            new_value = {
                'type': 'op',
                'op': tokens[1].value,
                'lvalue': invalid_lvalue,
                'rvalue': invalid_rvalue
            }

            if invalid_rvalue['type'] == 'op' and 'value' not in invalid_rvalue \
                    and MIDDLE_OPS_PRIORITY[invalid_rvalue['op']] < MIDDLE_OPS_PRIORITY[tokens[1].value]:
                # source expr:
                # 1 + 2 * 3

                # converting syntax tree, from:
                #   +
                #  / \
                # 1   *
                #    / \
                #   2   3

                # to:
                #     *
                #    / \
                #   +   3
                #  / \
                # 1   2

                new_value.update({
                    'op': invalid_rvalue['op'],
                    'lvalue': {
                        'type': 'op',
                        'op': tokens[1].value,
                        'lvalue': invalid_lvalue,
                        'rvalue': invalid_rvalue['lvalue']
                    },
                    'rvalue': invalid_rvalue['rvalue']
                })

                _lvalue = new_value['lvalue']
                if _lvalue['rvalue']['type'] == 'op' and 'value' not in _lvalue['rvalue'] \
                        and MIDDLE_OPS_PRIORITY[_lvalue['op']] > MIDDLE_OPS_PRIORITY[_lvalue['rvalue']['op']]:
                    # source expr:
                    # 1 ** 2 + 3 * 4

                    # converting syntax tree, from:
                    #   **
                    #  /  \
                    # 1    +
                    #     / \
                    #    2   *
                    #       / \
                    #      3   4

                    # to:
                    #       +
                    #     /   \
                    #   **     *
                    #  /  \   / \
                    # 1    2 3   4

                    _lvalue.update({
                        'op': _lvalue['rvalue']['op'],
                        'lvalue': _lvalue.copy() | {'rvalue': _lvalue['rvalue']['lvalue']},
                        'rvalue': _lvalue['rvalue']['rvalue']
                    })

            res.update(new_value)

        if res['op'] in BOOL_OPS:
            res['returned-type'] = 'bool'
        else:
            res['returned-type'] = '$undefined'  # that type mean unpredictable behavior

    if _get_returned_type(res) == '$undefined':
        errors_handler.final_push_segment(
            path,
            'unpredictable behavior (it is impossible to calculate the return type)',
            tokens[0],
            type=ErrorsHandler.WARNING
        )
    elif expected_type is not ... and _get_returned_type(res) != expected_type:
        errors_handler.final_push_segment(
            path,
            f'TypeError: expected type `{expected_type}`, got `{_get_returned_type(res)}`',
            tokens[0],
            fill=True
        )
        return {'$tokens-len': res['$tokens-len']}

    return res


def _is_setvalue_expression(
        tokens: List[Token],
        errors_handler: ErrorsHandler,
        path: str,
        i: int,
        type_annotation: bool = True
) -> bool:
    """<name>(":" <type>)? ("=" <expr>)?"""

    if i >= len(tokens) - 2:
        if type_annotation and i < len(tokens) and tokens[i].type == TokenTypes.NAME:
            errors_handler.final_push_segment(path, 'TypeError: type annotations needed', tokens[i], fill=True)

        return False

    if tokens[i].type == TokenTypes.NAME:
        if tokens[i + 1] == DummyToken(TokenTypes.OP, ':') and _is_type_expression(tokens[i + 2]):
            if i < len(tokens) - 4 and type_annotation:
                if tokens[i + 3] == DummyToken(TokenTypes.OP, '=') and _is_value_expression(tokens, i + 4):
                    return True

                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[i + 3], fill=True)
                return False

            if type_annotation:
                return True

            errors_handler.final_push_segment(
                path,
                'SyntaxError: type annotation is not possible for an already existing variable',
                tokens[i + 1]
            )
        elif tokens[i + 1] == DummyToken(TokenTypes.OP, '='):
            if _is_value_expression(tokens, i + 2):
                return True
            elif tokens[i + 2].type not in (TokenTypes.NEWLINE, TokenTypes.ENDMARKER):
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[i + 2], fill=True)
                return False

    if type_annotation or tokens[i + 1] == DummyToken(TokenTypes.OP, '='):
        errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[i + 1], fill=True)

    return False


def _generate_setvalue_syntax_object(tokens: List[Token], errors_handler: ErrorsHandler, path: str, i: int):
    res = {
        'type': 'set-value',
        'value-name': tokens[i].value,
        'value-type': None,
        'new-value': None,
        '$tokens-len': 2  # temp key
    }

    if tokens[i + 1].value == '=':
        # <value-name> = <new-value>
        _new_value = _generate_expression_syntax_object(tokens, errors_handler, path, i + 2)

        if errors_handler.has_errors(): return {'$tokens-len': res['$tokens-len']}

        res['$tokens-len'] += _new_value['$tokens-len']
        res['tokens'] = tokens[i: i + 2] + _new_value['tokens']
        del _new_value['$tokens-len'], _new_value['tokens']
        res['new-value'] = _new_value
    else:
        # <value-name>: <value-type>
        res['value-type'] = tokens[i + 2].value
        res['$tokens-len'] += 1
        res['tokens'] = tokens[i: i + 3]

        if i < len(tokens) - 4:
            # <value-name>: <value-type> = <new-value>
            _new_value = _generate_expression_syntax_object(
                tokens,
                errors_handler,
                path,
                i + 4,
                expected_type=res['value-type']
            )

            if errors_handler.has_errors(): return {'$tokens-len': res['$tokens-len']}

            res['$tokens-len'] += _new_value['$tokens-len']
            res['tokens'] = tokens[i:i + 4] + _new_value['tokens']
            del _new_value['$tokens-len'], _new_value['tokens']
            res['new-value'] = _new_value

    return res


def _is_code_body(tokens: List[Token] | Token, i: int = 0, stop_tokens: Tuple[DummyToken | TokenType] = ...):
    """<code-body>"""

    if isinstance(tokens, Token):
        tokens = [tokens]

    tokens = tokens[i:]

    if stop_tokens is ...:
        stop_tokens = (TokenType(TokenTypes.ENDMARKER), TokenType(TokenTypes.NEWLINE))

    for k in range(len(tokens)):
        if tokens[k] in stop_tokens:
            tokens = tokens[:k]
            break

    if len(tokens) == 1 and tokens[0].type == TokenTypes.CURLY_BRACES:
        return True

    return False


def _is_if_or_elif(tokens: List[Token] | Token, i: int = 0):
    """"if" <expr> <code-body> ("elif" <expr> <code-body>)? ("else" <code-body>)?"""
    if isinstance(tokens, Token):
        tokens = [tokens]

    tokens = tokens[i:]

    for k in range(len(tokens)):
        if tokens[k] in (TokenType(TokenTypes.ENDMARKER), TokenType(TokenTypes.NEWLINE)):
            tokens = tokens[:k]
            break

    if len(tokens) < 3:
        return False

    if tokens[0].type == TokenTypes.NAME and tokens[0].value in ('if', 'elif') and _is_value_expression(tokens[:-1], 1)\
            and _is_code_body(tokens[-1]):
        return True

    return False


def _is_else(tokens: List[Token] | Token, i: int = 0, stop_tokens: Tuple[DummyToken | TokenType] = ...):
    if isinstance(tokens, Token):
        tokens = [tokens]

    tokens = tokens[i:]

    if stop_tokens is ...:
        stop_tokens = (TokenType(TokenTypes.ENDMARKER), TokenType(TokenTypes.NEWLINE))

    for k in range(len(tokens)):
        if tokens[k] in stop_tokens:
            tokens = tokens[:k]
            break

    if len(tokens) != 2:
        return False

    if tokens[0] == DummyToken(TokenTypes.NAME, 'else') and _is_code_body(tokens, 1):
        return True

    return False


def generate_code_body(tokens: List[Token], errors_handler: ErrorsHandler, path: str, body_type: str = 'main'):
    main_body = {
        'type': body_type,
        'value': []
    }
    current_body = main_body

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if _is_setvalue_expression(tokens, errors_handler, path, i, type_annotation=False):
            # set variable value
            # <name> "=" <expr>

            current_body['value'].append(_generate_setvalue_syntax_object(tokens, errors_handler, path, i))
            i += current_body['value'][-1]['$tokens-len']
            del current_body['value'][-1]['$tokens-len']
        elif _is_kw(token, ('let', 'var')) and _is_setvalue_expression(tokens, errors_handler, path, i + 1):
            # init variable
            # "let" | "var" <name>(":" <typename>)? "=" <expr>

            current_body['value'].append(_generate_setvalue_syntax_object(tokens, errors_handler, path, i + 1))

            if not errors_handler.has_errors():
                current_body['value'][-1].update({
                    'type': 'init-value',
                    'init-type': token.value
                })
                current_body['value'][-1]['tokens'].insert(0, token)

            i += current_body['value'][-1]['$tokens-len'] + 1
            del current_body['value'][-1]['$tokens-len']
        elif _is_if_or_elif(tokens, i):
            # if, elif statement
            # "if" | "elif" <expr> {...}

            _condition = _generate_expression_syntax_object(
                tokens,
                errors_handler,
                path,
                i + 1,
                right_i=1,
                expected_type='bool'
            )
            _body = generate_code_body(
                            tokens[i + 1 + _condition['$tokens-len']].value,
                            errors_handler,
                            path,
                            'code-body'
                        )
            _value = {
                        'condition': _condition,
                        'body': _body
                    }

            if tokens[i].value == 'elif':
                if len(current_body['value']) == 0 or current_body['value'][-1]['type'] != 'if-statement':
                    errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
                    return {}

                if 'elif' not in current_body['value'][-1]:
                    current_body['value'][-1]['elif'] = []

                current_body['value'][-1]['elif'].append(_value)
            else:
                current_body['value'].append({
                    'type': 'if-statement',
                    'if': _value
                })

            i += _condition['$tokens-len'] + 1
            del _condition['$tokens-len']
        elif _is_else(tokens, i):
            # ... else {...}
            if len(current_body['value']) == 0 or current_body['value'][-1]['type'] != 'if-statement':
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
                return {}

            current_body['value'][-1]['else-body'] = generate_code_body(
                            tokens[i + 1].value,
                            errors_handler,
                            path,
                            'code-body'
                        )

            i += 2
        elif _is_value_expression(tokens, i):
            current_body['value'].append(_generate_expression_syntax_object(tokens, errors_handler, path, i))

            errors_handler.final_push_segment(
                path,
                'path statement with no effect',
                tokens[i],
                type=ErrorsHandler.WARNING
            )

            i += current_body['value'][-1]['$tokens-len']
            del current_body['value'][-1]['$tokens-len']
        elif token.type == TokenTypes.NEWLINE:
            pass
        elif token.type == TokenTypes.ENDMARKER:
            break
        elif not errors_handler.has_errors():
            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
            return {}

        i += 1

        if errors_handler.has_errors():
            return {}

    return main_body


def __compile_op_expr(syntaxtree: dict) -> str:
    # !THIS FUNCTION IS NOT FOR RELEASE, NEEDED ONLY FOR DEBUG!

    if syntaxtree['type'] == 'main':
        return __compile_op_expr(syntaxtree['value'][0])

    if syntaxtree['type'] == 'op':
        if 'value' in syntaxtree:
            return syntaxtree['op'] + ' ' + __compile_op_expr(syntaxtree['value'])

        return f'{{{__compile_op_expr(syntaxtree["lvalue"])} {syntaxtree["op"]} {__compile_op_expr(syntaxtree["rvalue"])}}}'

    if syntaxtree['type'] == 'number':
        return syntaxtree['value']

    if syntaxtree['type'] == 'bool':
        return 'true' if syntaxtree['value'] == 'True' else 'false'

    if syntaxtree['type'] == 'char':
        return "'" + syntaxtree['value'] + "'"

    return f'"{syntaxtree["value"]}"'


if __name__ == '__main__':
    from cft_lexer import generate_tokens, compose_tokens

    with open('test.cft', 'r', encoding='utf-8') as f:
        file = f.read()

    errors_handler = ErrorsHandler()
    tokens = generate_tokens(file, 'test.cft', errors_handler)
    print('First stage:', tokens)

    if errors_handler.has_errors() or errors_handler.has_warnings():
        errors_handler.print()
    else:
        tokens = compose_tokens(file, 'test.cft', tokens, errors_handler)
        print('Second stage:', tokens)

        if errors_handler.has_errors() or errors_handler.has_warnings():
            errors_handler.print()
        else:
            syntaxtree = generate_code_body(tokens, errors_handler, 'test.cft')
            print('Third stage:', syntaxtree)

            if errors_handler.has_errors() or errors_handler.has_warnings():
                errors_handler.print()
