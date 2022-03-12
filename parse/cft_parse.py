from cft_lexer import Token, TokenTypes, DummyToken, TokenType
from cft_namehandler import get_value_returned_type
from compile.cft_compile import get_num_type
from cft_errors_handler import ErrorsHandler
from cft_namehandler import NameHandler
from parse import cft_ops as ops
from typing import List, Tuple


DEBUG = False


def _is_type_expression(token: Token) -> bool:
    if token.type == TokenTypes.NAME:
        return True

    return False


# that names can not be used like a variable's, a function's name etc.
KEYWORDS = ['if', 'else', 'elif', 'let', 'var', 'True', 'False']


def _is_kw(token: Token, kws=()):
    if len(kws) != 0:
        return _is_kw(token) and token.value in kws

    return token.type == TokenTypes.NAME and token.value in KEYWORDS or token.value in ops.OPS


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
        elif ops.is_op(tokens[0]) and not ops.is_op(tokens[1]) and _is_value_expression(tokens, 1):
            if tokens[0].value not in ops.LOPS: return False
            return True
        elif len(tokens) >= 3 and not ops.is_op(tokens[0]) and ops.is_op(tokens[1]) \
                and _is_value_expression(tokens[0]) and _is_value_expression(tokens, 2):
            return True

    return False


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
                'returned-type': get_num_type(token.value)
            })
        elif token.type == TokenTypes.NAME:
            res['value'] = token.value

            if token.value in ('True', 'False'):
                res['type'] = 'bool'
            else:
                res['type'] = 'name'
                res['returned-type'] = '$undefined' \
                    if not DEBUG \
                    else namehandler.get_current_name_body(token.value)['type']
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
        res.update(ops.generate_op_expression(tokens, errors_handler, path, _generate_expression_syntax_object))

    if get_value_returned_type(res) == '$undefined':
        errors_handler.final_push_segment(
            path,
            'unpredictable behavior (it is impossible to calculate the return type)',
            tokens[0],
            type=ErrorsHandler.WARNING
        )
    elif expected_type is not ... and get_value_returned_type(res) != expected_type:
        errors_handler.final_push_segment(
            path,
            f'TypeError: expected type `{expected_type}`, got `{get_value_returned_type(res)}`',
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


def _generate_setvalue_syntax_object(
        tokens: List[Token],
        errors_handler: ErrorsHandler,
        path: str,
        i: int,
        namehandler: NameHandler
):
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

    if res['value-type'] is None and res['new-value'] is not None:
        res['value-type'] = get_value_returned_type(res['new-value'])

    if not namehandler.set_name(tokens[i].value, res['value-type'], res['new-value'], mut=True):
        errors_handler.final_push_segment(path, '<Set name value error>', tokens[i])

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


def generate_code_body(
        tokens: List[Token],
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        body_type: str = '$main-body'
):
    main_body = {
        'type': body_type,
        'value': []
    }
    current_body = main_body

    if body_type != '$main-body':
        print('before:', namehandler._accessible_names)
        namehandler.init_new_localspace()
        print('after:', namehandler._accessible_names)

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if _is_setvalue_expression(tokens, errors_handler, path, i, type_annotation=False):
            # set variable value
            # <name> "=" <expr>

            current_body['value'].append(_generate_setvalue_syntax_object(tokens, errors_handler, path, i, namehandler))

            i += current_body['value'][-1]['$tokens-len']
            del current_body['value'][-1]['$tokens-len']
        elif _is_kw(token, ('let', 'var')) and _is_setvalue_expression(tokens, errors_handler, path, i + 1):
            # init variable
            # "let" | "var" <name>(":" <typename>)? "=" <expr>

            current_body['value'].append(
                _generate_setvalue_syntax_object(tokens, errors_handler, path, i + 1, namehandler)
            )

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
                            namehandler,
                            body_type='$code-body'
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
                            namehandler,
                            body_type='$code-body'
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

    if body_type != '$main-body':
        namehandler.leave_current_localspace()

    return main_body


if __name__ == '__main__':
    from cft_lexer import generate_tokens, compose_tokens

    with open('../test.cft', 'r', encoding='utf-8') as f:
        file = f.read()

    errors_handler = ErrorsHandler()
    tokens = generate_tokens(file, '../test.cft', errors_handler)
    print('First stage:', tokens)

    if errors_handler.has_errors() or errors_handler.has_warnings():
        errors_handler.print()
    else:
        tokens = compose_tokens(file, '../test.cft', tokens, errors_handler)
        print('Second stage:', tokens)

        if errors_handler.has_errors() or errors_handler.has_warnings():
            errors_handler.print()
        else:
            namehandler = NameHandler()

            syntaxtree = generate_code_body(tokens, errors_handler, '../test.cft', namehandler)
            print('Third stage:', syntaxtree, '\n   - NameHandler:', namehandler.to_json())

            if errors_handler.has_errors() or errors_handler.has_warnings():
                errors_handler.print()
