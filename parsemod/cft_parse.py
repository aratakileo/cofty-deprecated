from parsemod.cft_others import extract_tokens, extract_tokens_with_code_body, _is_code_body, remove_newline_by_borders
from cft_namehandler import NameHandler, get_value_returned_type
from parsemod.cft_name import is_kw, is_base_name, compose_name
from lexermod.cft_token import Token, TokenTypes, DummyToken
from parsemod.cft_syntaxtree_values import pNone
from parsemod.cft_struct import _is_struct_init
from cft_errors_handler import ErrorsHandler
from parsemod.cft_fn import _is_fn_init
from parsemod.cft_setvalue import *
from parsemod.cft_ops import is_op
from parsemod.cft_expr import *


def _is_if_or_elif(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0,
):
    """"if" <expr> <code-body> ("elif" <expr> <code-body>)?"""
    tokens = extract_tokens_with_code_body(tokens, i)

    if tokens is None:
        return False

    if len(tokens) < 3:
        return False

    if tokens[0].type == TokenTypes.NAME and tokens[0].value in ('if', 'elif') and _is_value_expression(
            tokens[:-1],
            errors_handler,
            path,
            namehandler,
            1
    ) and _is_code_body(tokens[-1]):
        return True

    return False


def _is_else(tokens: list[Token] | Token, i: int = 0):
    """("else" <code-body>)"""
    tokens = extract_tokens_with_code_body(tokens, i)

    if tokens is None:
        return False

    if len(tokens) != 2:
        return False

    if tokens[0] == DummyToken(TokenTypes.NAME, 'else') and _is_code_body(tokens, 1):
        return True

    return False


def _is_mod(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0
):
    # TODO: NEEDS TO ADD A SUPPORT OF OVERLOADING THE NAMES

    tokens = extract_tokens_with_code_body(tokens, i)

    if tokens is not None and is_kw(tokens[0], 'mod'):
        if len(tokens) == 3 and is_base_name(tokens[1]) and _is_code_body(tokens, 2):
            return True

        errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[-1], fill=True)

    return False


MAIN_BODY_ADVANCED_OPTIONS = {
    'constant-expr': True
}


def _has_constant_expr(main_body: dict[any, any], value: bool):
    if 'constant-expr' in main_body:
        main_body['constant-expr'] = main_body['constant-expr'] and value is True
        # `is True` needs when `False and False` for `False and False and False is not False => False`


def generate_code_body(
        tokens: list[Token],
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        body_type: str = '$main-body',
        base_body_type: str = '$main-body',
        advanced_options: dict[any, any] = {}
):
    main_body = {
        'type': body_type,
        'value': []
    }
    main_body.update(advanced_options)

    current_body = main_body

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if _is_setvalue_expression(tokens, errors_handler, path, namehandler, i):
            # set variable value
            # <name> "=" <expr>

            generated = _generate_setvalue_syntax_object(tokens, errors_handler, path, namehandler, i)

            if errors_handler.has_errors():
                return {}

            current_body['value'].append(generated)

            i += generated['$tokens-len']
            del generated['$tokens-len'], generated['$constant-expr']

            _has_constant_expr(main_body, False)
        elif is_kw(token, ('let', 'val')) and _is_setvalue_expression(
                tokens, errors_handler, path, namehandler, i + 1, init_type=token.value
        ):
            # init variable
            # ("let" | "val") <name>(":" <typename>)? "=" <expr>

            # what does that mean?
            # let - visible only in current function
            # val - constant value, visible only in current function

            generated = _generate_setvalue_syntax_object(
                tokens,
                errors_handler,
                path,
                namehandler,
                i + 1,
                init_type=token.value
            )

            if errors_handler.has_errors():
                return {}

            current_body['value'].append(generated)

            i += generated['$tokens-len'] + 1

            _has_constant_expr(main_body, generated['$constant-expr'])

            del generated['$tokens-len'], generated['$constant-expr']
        elif _is_if_or_elif(tokens, errors_handler, path, namehandler, i):
            # if, elif statement
            # "if" | "elif" <expr> {...}

            index = i + len(extract_tokens(tokens, i)) - 1
            off = tokens[index].type != TokenTypes.CURLY_BRACES

            _condition = _generate_expression_syntax_object(
                tokens,
                errors_handler,
                path,
                namehandler,
                i + 1,
                right_i=1 - off,
                expected_type='bool'
            )

            off *= 2

            if errors_handler.has_errors():
                return {}

            namehandler.init_new_localspace()

            _body = generate_code_body(
                tokens[index + off].value,
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

            i += _condition['$tokens-len'] + 1 + off
            del _condition['$tokens-len']

            _has_constant_expr(main_body, False)
        elif _is_else(tokens, i):
            # ... else {...}
            if len(current_body['value']) == 0 or current_body['value'][-1]['type'] != 'if-statement':
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
                return {}

            namehandler.init_new_localspace()

            index = i + 1
            off = tokens[index].type == TokenTypes.NEWLINE

            current_body['value'][-1]['else-body'] = generate_code_body(
                tokens[index + off].value,
                errors_handler,
                path,
                namehandler,
                body_type='$sub-body',
                base_body_type=base_body_type
            )

            if errors_handler.has_errors():
                return {}

            i += 2 + off
        elif _is_fn_init(tokens, errors_handler, path, namehandler, i):
            type_specification = is_op(tokens[i + 3], '->')
            returned_type = 'None' if not type_specification else tokens[i + 4].value
            positional_args = 0
            name = tokens[i + 1].value

            if namehandler.has_globalname(name):
                errors_handler.final_push_segment(
                    path,
                    f'NameError: name `{name}` is already defined',
                    tokens[i + 1],
                    fill=True
                )
                return {}

            namehandler.force_set_name(name, type='fn', value={}, **{'returned-type': returned_type})
            namehandler.use_localspace(name)
            namehandler.abs_current_obj['args'] = {}

            args = []
            args_tokens = tokens[i + 2].value

            if args_tokens:
                temp = args_tokens[0].value

                if args_tokens[0].type != TokenTypes.TUPLE:
                    temp = [args_tokens]

                for arg_tokens in temp:
                    if not arg_tokens:
                        break

                    arg = _generate_setvalue_syntax_object(
                        arg_tokens,
                        errors_handler,
                        path,
                        namehandler,
                        init_type='let'
                    )

                    if errors_handler.has_errors():
                        return {}

                    if arg['new-value'] is None:
                        positional_args += 1

                    args.append(arg)

                    del arg['$tokens-len'], arg['$constant-expr']

                    args_name = arg['value-name']

                    namehandler.abs_current_obj['args'][args_name] = namehandler.abs_current_obj['value'][args_name]

            namehandler.abs_current_obj.update({
                'positional-args': positional_args,
                'max-args': len(args)
            })

            index = i + (5 if type_specification else 3)
            off = tokens[index].type == TokenTypes.NEWLINE

            body = generate_code_body(
                tokens[index + off].value,
                errors_handler,
                path,
                namehandler,
                body_type='$fn-body',
                base_body_type='$fn-body',
                advanced_options={
                    '$return-is-used': False  # temp value
                }
            )

            if errors_handler.has_errors():
                return {}

            current_body['value'].append({
                'type': 'fn-init',
                'fn-name': name,
                'args': args,
                'body': body,
                'returned-type': returned_type
            })

            if errors_handler.has_errors():
                return {}

            i += (6 if type_specification else 4) + off
        elif is_kw(token, 'return'):
            if base_body_type != '$fn-body':
                errors_handler.final_push_segment(path, 'SyntaxError: \'return\' outside function', token, fill=True)
                return {}

            returned_value = pNone \
                if extract_tokens(tokens, i + 1) is None or not _is_value_expression(
                    tokens,
                    errors_handler,
                    path,
                    namehandler,
                    i + 1
                ) else _generate_expression_syntax_object(
                    tokens,
                    errors_handler,
                    path,
                    namehandler,
                    i + 1,
                    expected_type=namehandler.base_current_obj['returned-type']
                )

            if errors_handler.has_errors():
                return {}

            if namehandler.base_current_obj['returned-type'] != 'None' and 'type' in returned_value \
                    and returned_value['type'] == 'None':
                errors_handler.final_push_segment(
                    path,
                    f'TypeError: expected type `{namehandler.base_current_obj["returned-type"]}`,'
                    f' got `{get_value_returned_type(returned_value)}`',
                    tokens[0],
                    fill=True
                )

                return {}

            current_body['value'].append({
                'type': 'return',
                'value': returned_value
            })

            main_body['$return-is-used'] = True

            if '$tokens-len' in returned_value:
                i += returned_value['$tokens-len']
                del returned_value['$tokens-len']

            i += 1
        elif _is_struct_init(tokens, errors_handler, path, namehandler, i):
            name = tokens[i + 1].value
            off = tokens[i + 2].type != TokenTypes.CURLY_BRACES
            body_token = tokens[i + 2 + off]

            if namehandler.has_globalname(name):
                errors_handler.final_push_segment(
                    path,
                    f'NameError: name `{name}` is already defined',
                    tokens[i + 1],
                    fill=True
                )
                return {}

            namehandler.force_set_name(name, type='$struct', value={})

            if body_token.value:
                namehandler.use_localspace(name)

                segments_tokens = body_token.value
                segments_tokens = [segments_tokens] if segments_tokens[0].type != TokenTypes.TUPLE \
                    else segments_tokens[0].value

                for segment_tokens in segments_tokens:
                    segment_tokens = remove_newline_by_borders(segment_tokens)

                    if not segment_tokens:
                        break

                    segment_name = segment_tokens[0].value

                    if namehandler.has_localname(segment_name):
                        errors_handler.final_push_segment(
                            path,
                            f'NameError: field `{segment_name}` is already declared',
                            segment_tokens[0],
                            fill=True
                        )
                        return {}

                    namehandler.force_set_name(
                        segment_name,
                        type=compose_name(segment_tokens[2:]),
                        value=None
                    )

                namehandler.leave_current_localspace()

            i += 3 + off
        elif _is_mod(tokens, errors_handler, path, namehandler, i):
            name = tokens[i + 1].value

            if namehandler.has_globalname(name):
                errors_handler.final_push_segment(
                    path,
                    f'NameError: name `{name}` is already defined',
                    tokens[i + 1],
                    fill=True
                )
                return {}

            namehandler.force_set_name(name, type='$mod', value={})
            namehandler.use_localspace(name)

            off = tokens[i + 2].type == TokenTypes.NEWLINE

            body = generate_code_body(
                tokens[i + off + 2].value,
                errors_handler,
                path,
                namehandler,
                '$mod-body',
                base_body_type='$mod-body',
                advanced_options=MAIN_BODY_ADVANCED_OPTIONS
            )

            if errors_handler.has_errors():
                return {}

            current_body['value'].append({
                'type': 'mod',
                'mod-name': name,
                'body': body
            })

            i += 3 + off
        elif _is_value_expression(tokens, errors_handler, path, namehandler, i):
            generated = _generate_expression_syntax_object(
                tokens,
                errors_handler,
                path,
                namehandler,
                i,
                effect_checker=True
            )

            if errors_handler.has_errors():
                return {}

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

            _has_constant_expr(main_body, False)
        elif token.type == TokenTypes.NEWLINE:
            pass
        elif token.type == TokenTypes.ENDMARKER:
            break
        elif not errors_handler.has_errors():
            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', token, fill=True)
            return {}

        if errors_handler.has_errors():
            return {}

        i += 1

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
        namehandler.leave_current_localspace()
    else:
        print(namehandler.accessible_to_json())

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

            syntaxtree = generate_code_body(
                tokens,
                errors_handler,
                '../test.cft',
                namehandler,
                advanced_options=MAIN_BODY_ADVANCED_OPTIONS
            )
            print('Third stage:', syntaxtree, '\n   - NameHandler:', namehandler.to_json())

            if errors_handler.has_errors() or errors_handler.has_warnings():
                errors_handler.print()
