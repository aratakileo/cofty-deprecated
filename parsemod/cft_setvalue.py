from cft_namehandler import NameHandler, get_value_returned_type
from lexermod.cft_token import Token, TokenTypes
from parsemod.cft_others import extract_tokens
from cft_errors_handler import ErrorsHandler
from parsemod.cft_kw import _is_name
from parsemod.cft_ops import is_op
from parsemod.cft_expr import *


def _is_setvalue_expression(
        tokens: list[Token],
        errors_handler: ErrorsHandler,
        path: str,
        i: int = 0,
        init_type=''
) -> bool:
    tokens = extract_tokens(tokens, i)

    if tokens is not None and len(tokens) >= 3 and _is_name(tokens[0]):
        if is_op(tokens[1], '='):
            # <value-name> = <new-value>
            if _is_value_expression(tokens, 2):
                return True

            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[2], fill=True)
            return False

        if is_op(tokens[1], ':'):
            # <value-name>: <value-type>
            if not init_type:
                errors_handler.final_push_segment(
                    path,
                    'SyntaxError: type annotation is not possible for an already existing variable',
                    tokens[1],
                    fill=True
                )
                return False

            if not _is_type_expression(tokens[2]):
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[2], fill=True)
                return False

            if init_type == 'val' and (len(tokens) == 3 or not is_op(tokens[3], '=')):
                errors_handler.final_push_segment(path, 'SyntaxError: constant without value', tokens[0], fill=True)
                errors_handler.final_push_segment(
                    path,
                    f'provide a definition for the constant: `= <expr>`',
                    tokens[2],
                    type=ErrorsHandler.HELP,
                    offset=len(tokens[2].value) - 1
                )
                return False

            if len(tokens) >= 4:
                # <value-name>: <value-type> =
                if len(tokens) >= 5 and is_op(tokens[3], '=') and _is_value_expression(tokens, 4):
                    # <value-name>: <value-type> = <new-value>
                    return True

                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[3], fill=True)
                return False

            return True

    return False


def _generate_setvalue_syntax_object(
        tokens: list[Token],
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0,
        init_type=''
):
    tokens = extract_tokens(tokens, i)

    # <value-name>
    res = {
        'type': 'set-value',
        'value-name': tokens[0].value,
        'value-type': None,
        'new-value': None,
        '$tokens-len': len(tokens),  # temp value
        '$constant-expr': True  # temp value
    }

    _tokens = tokens[1:]

    if is_op(_tokens[0], ':'):
        # : <value-type>
        res['value-type'] = _tokens[1].value

        _tokens = _tokens[2:]

    if _tokens and is_op(_tokens[0], '='):
        # = <new-value>
        new_value = _generate_expression_syntax_object(
            _tokens,
            errors_handler,
            path,
            namehandler,
            i=1,
            expected_type=... if res['value-type'] is None else res['value-type']
        )

        if res['value-type'] is None:
            res['value-type'] = get_value_returned_type(new_value)

        if errors_handler.has_errors():
            return {}

        res['$constant-expr'] = new_value['$constant-expr']

        del new_value['$tokens-len'], new_value['$constant-expr']

        res['new-value'] = new_value

    if not namehandler.set_name(tokens[0].value, res['value-type'], res['new-value'], mut=True):
        errors_handler.final_push_segment(path, '<Set name value error>', tokens[0])

    return res


def _generate_setvalue_syntax_object_old(
        tokens: list[Token],
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0
):
    res = {
        'type': 'set-value',
        'value-name': tokens[i].value,
        'value-type': None,
        'new-value': None,
        '$tokens-len': 2,  # temp value
        '$constant-expr': True  # temp value
    }

    if tokens[i + 1].value == '=':
        # <value-name> = <new-value>
        _new_value = _generate_expression_syntax_object(
            tokens,
            errors_handler,
            path,
            namehandler,
            i + 2
        )

        if errors_handler.has_errors(): return {'$tokens-len': res['$tokens-len']}

        res['$tokens-len'] += _new_value['$tokens-len']
        res['$constant-expr'] = _new_value['$constant-expr']

        del _new_value['$tokens-len'], _new_value['$constant-expr']

        res['new-value'] = _new_value
    else:
        # <value-name>: <value-type>
        res['value-type'] = tokens[i + 2].value
        res['$tokens-len'] += 1

        if i < len(tokens) - 4 and is_op(tokens[i + 3], '='):
            # <value-name>: <value-type> = <new-value>
            _new_value = _generate_expression_syntax_object(
                tokens,
                errors_handler,
                path,
                namehandler,
                i + 4,
                expected_type=res['value-type']
            )

            if errors_handler.has_errors(): return {'$tokens-len': res['$tokens-len']}

            res['$tokens-len'] += _new_value['$tokens-len']
            res['$constant-expr'] = _new_value['$constant-expr']

            del _new_value['$tokens-len'], _new_value['$constant-expr']

            res['new-value'] = _new_value

    if res['value-type'] is None and res['new-value'] is not None:
        res['value-type'] = get_value_returned_type(res['new-value'])

    _type = res['value-type']

    if res['new-value'] is not None:
        _type = get_value_returned_type(res['new-value'])

    if not namehandler.set_name(tokens[i].value, _type, res['new-value'], mut=True):
        errors_handler.final_push_segment(path, '<Set name value error>', tokens[i])

    return res


__all__ = (
    '_is_setvalue_expression',
    '_generate_setvalue_syntax_object'
)
