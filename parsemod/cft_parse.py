from lexermod.cft_token import Token, TokenTypes, DummyToken, TokenType
from cft_extract_tokens import extract_tokens
from cft_errors_handler import ErrorsHandler
from cft_namehandler import NameHandler
from parsemod.cft_fn import _is_fn_init
from cft_is_codebody import *
from typing import List, Tuple
from cft_setvalue import *
from cft_kw import _is_kw
from cft_expr import *


def _is_if_or_elif(tokens: List[Token] | Token, i: int = 0, stop_tokens: Tuple[DummyToken | TokenType] = ...):
    """"if" <expr> <code-body> ("elif" <expr> <code-body>)? ("else" <code-body>)?"""
    tokens = extract_tokens(tokens, i, stop_tokens)

    if tokens is None:
        return False

    if len(tokens) < 3:
        return False

    if tokens[0].type == TokenTypes.NAME and tokens[0].value in ('if', 'elif') and _is_value_expression(tokens[:-1], 1)\
            and _is_code_body(tokens[-1]):
        return True

    return False


def _is_else(tokens: List[Token] | Token, i: int = 0, stop_tokens: Tuple[DummyToken | TokenType] = ...):
    tokens = extract_tokens(tokens, i, stop_tokens)

    if tokens is None:
        return False

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
            # TODO: What different between let and var? Remove let and var if it not make sense...
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
                namehandler,
                i + 1,
                right_i=1,
                expected_type='bool'
            )

            namehandler.root_init_new_localspace()

            _body = generate_code_body(
                            tokens[i + 1 + _condition['$tokens-len']].value,
                            errors_handler,
                            path,
                            namehandler,
                            body_type='$sub-body'
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

            namehandler.root_init_new_localspace()

            current_body['value'][-1]['else-body'] = generate_code_body(
                            tokens[i + 1].value,
                            errors_handler,
                            path,
                            namehandler,
                            body_type='$sub-body'
                        )

            i += 2
        elif _is_fn_init(tokens, i):
            if not namehandler.init_fn(tokens[i + 1].value):
                errors_handler.final_push_segment(path, f'<Init function `{tokens[i + 1].value}` error>', tokens[i])

            current_body['value'].append({
                'type': 'fn-init',
                'fn-name': tokens[i + 1].value,
                'args': {},
                'body': generate_code_body(tokens[i + 3].value, errors_handler, path, namehandler, body_type='$fn-body'),
                'returned-type': 'None'
            })
            i += 4
        elif _is_value_expression(tokens, i):
            current_body['value'].append(
                _generate_expression_syntax_object(tokens, errors_handler, path, namehandler, i)
            )

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
        namehandler.root_leave_current_localspace()

    return main_body


if __name__ == '__main__':
    from lexermod.cft_lexer import *

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
