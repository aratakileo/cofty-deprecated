from lexermod.cft_token import Token, TokenTypes, DummyToken, TokenType
from cft_namehandler import NameHandler, get_value_returned_type
from cft_extract_tokens import extract_tokens
from cft_errors_handler import ErrorsHandler
from parsemod.cft_fn import _is_fn_init
from cft_syntaxtree_values import pNone
from parsemod.cft_ops import is_op
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
        body_type: str = '$main-body',
        base_body_type: str = '$main-body'
):
    main_body = {
        'type': body_type,
        'value': []
    }
    current_body = main_body

    if body_type == '$fn-body':
        main_body['$return-is-used'] = False  # temp value

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if _is_setvalue_expression(tokens, errors_handler, path, i, type_annotation=False):
            # set variable value
            # <name> "=" <expr>

            generated = _generate_setvalue_syntax_object(tokens, errors_handler, path, namehandler, i)

            current_body['value'].append(generated)

            i += generated['$tokens-len']
            del generated['$tokens-len']
        elif _is_kw(token, ('let', 'var')) and _is_setvalue_expression(tokens, errors_handler, path, i + 1):
            # TODO: What different between let and var? Remove let and var if it is not make sense...
            # init variable
            # "let" | "var" <name>(":" <typename>)? "=" <expr>

            generated = _generate_setvalue_syntax_object(tokens, errors_handler, path, namehandler, i + 1)

            current_body['value'].append(generated)

            if not errors_handler.has_errors():
                generated.update({
                    'type': 'init-value',
                    'init-type': token.value
                })

            i += generated['$tokens-len'] + 1
            del generated['$tokens-len']
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
                body_type='$sub-body',
                base_body_type=base_body_type
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
                body_type='$sub-body',
                base_body_type=base_body_type
            )

            i += 2
        elif _is_fn_init(tokens, errors_handler, path, i):
            type_specification = is_op(tokens[i + 3], ':')
            returned_type = 'None' if not type_specification else tokens[i + 4].value

            if not namehandler.init_fn(tokens[i + 1].value, returned_type):
                errors_handler.final_push_segment(path, f'<Init function `{tokens[i + 1].value}` error>', tokens[i])

            args = []
            args_tokens = tokens[i + 2].value

            if args_tokens:
                temp = args_tokens[0].value

                if args_tokens[0].type != TokenTypes.TUPLE:
                    temp = [args_tokens]

                for arg_tokens in temp:
                    args.append(_generate_setvalue_syntax_object(arg_tokens, errors_handler, path, namehandler))
                    del args[-1]['$tokens-len']

            namehandler.def_fn_args()

            current_body['value'].append({
                'type': 'fn-init',
                'fn-name': tokens[i + 1].value,
                'args': args,
                'body': generate_code_body(
                    tokens[i + (5 if type_specification else 3)].value,
                    errors_handler,
                    path,
                    namehandler,
                    body_type='$fn-body',
                    base_body_type='$fn-body'
                ),
                'returned-type': returned_type
            })

            i += 6 if type_specification else 4
        elif _is_kw(token, 'return'):
            if base_body_type != '$fn-body':
                errors_handler.final_push_segment(path, 'SyntaxError: \'return\' outside function', token, fill=True)
                return {}

            returned_value = pNone \
                if extract_tokens(tokens, i + 1) is None or not _is_value_expression(tokens, i + 1) \
                else _generate_expression_syntax_object(
                    tokens,
                    errors_handler,
                    path,
                    namehandler,
                    i + 1,
                    expected_type=namehandler.base_current_obj['returned-type']
                )

            if namehandler.base_current_obj['returned-type'] != 'None' and 'type' in returned_value \
                    and returned_value['type'] == 'None':
                errors_handler.final_push_segment(
                    path,
                    f'TypeError: expected type `{namehandler.base_current_obj["returned-type"]}`,'
                    f' got `{get_value_returned_type(returned_value)}`',
                    tokens[0],
                    fill=True
                )

            current_body['value'].append({
                'type': 'return',
                'value': returned_value
            })

            main_body['$return-is-used'] = True

            if '$tokens-len' in returned_value:
                i += returned_value['$tokens-len']
                del returned_value['$tokens-len']

            i += 1
        elif _is_value_expression(tokens, i):
            generated = _generate_expression_syntax_object(
                tokens,
                errors_handler,
                path,
                namehandler,
                i,
                effect_checker=True
            )

            current_body['value'].append(
                generated
            )

            if not generated['$has-effect']:
                errors_handler.final_push_segment(
                    path,
                    'path statement with no effect',
                    tokens[i],
                    type=ErrorsHandler.WARNING
                )

            i += generated['$tokens-len']
            del generated['$tokens-len'], generated['$has-effect']
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

    if '$return-is-used' in main_body:
        if not main_body['$return-is-used'] and namehandler.abs_current_obj['returned-type'] != 'None':
            errors_handler.final_push_segment(
                path,
                'SyntaxError: has no (final) `return` expression',
                tokens[-1],
                fill=True
            )
            return {}

        del main_body['$return-is-used']

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
