from cft_namehandler import NameHandler, get_value_returned_type
from lexermod.cft_token import Token, TokenTypes
from cft_errors_handler import ErrorsHandler
from parsemod.cft_kw import _is_name
from parsemod.cft_ops import is_op
from cft_expr import *
from typing import List


def _is_setvalue_expression(
        tokens: List[Token],
        errors_handler: ErrorsHandler,
        path: str,
        i: int = 0,
        type_annotation: bool = True
) -> bool:
    """<name>(":" <type>)? ("=" <expr>)?"""

    if i >= len(tokens) - 2:
        if type_annotation and i < len(tokens) and _is_name(tokens[i]):
            errors_handler.final_push_segment(path, 'TypeError: type annotations needed', tokens[i], fill=True)

        return False

    if _is_name(tokens[i]):
        if is_op(tokens[i + 1], ':') and _is_type_expression(tokens[i + 2]):
            if i < len(tokens) - 4 and type_annotation:
                if is_op(tokens[i + 3], '=') and _is_value_expression(tokens, i + 4):
                    return True

                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[i + 3], fill=True)
                return False

            if type_annotation:
                if len(tokens) != 3:
                    errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[i + 3], fill=True)
                    return False

                return True

            errors_handler.final_push_segment(
                path,
                'SyntaxError: type annotation is not possible for an already existing variable',
                tokens[i + 1]
            )
        elif is_op(tokens[i + 1], '='):
            if _is_value_expression(tokens, i + 2):
                return True
            elif tokens[i + 2].type not in (TokenTypes.NEWLINE, TokenTypes.ENDMARKER):
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[i + 2], fill=True)
                return False

    if type_annotation or is_op(tokens[i + 1], '='):
        errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[i + 1], fill=True)

    return False


def _generate_setvalue_syntax_object(
        tokens: List[Token],
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
        '$tokens-len': 2  # temp key
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
        del _new_value['$tokens-len']
        res['new-value'] = _new_value
    else:
        # <value-name>: <value-type>
        res['value-type'] = tokens[i + 2].value
        res['$tokens-len'] += 1

        if i < len(tokens) - 4:
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
            del _new_value['$tokens-len']
            res['new-value'] = _new_value

    if res['value-type'] is None and res['new-value'] is not None:
        res['value-type'] = get_value_returned_type(res['new-value'])

    _type = res['new-value']['type']

    if _type != '$number':
        _type = res['value-type']

    if not namehandler.set_name(tokens[i].value, _type, res['new-value'], mut=True):
        errors_handler.final_push_segment(path, '<Set name value error>', tokens[i])

    return res


__all__ = (
    '_is_setvalue_expression',
    '_generate_setvalue_syntax_object'
)
