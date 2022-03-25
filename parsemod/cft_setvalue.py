from cft_namehandler import NameHandler, get_value_returned_type
from parsemod.cft_others import extract_tokens
from cft_errors_handler import ErrorsHandler
from parsemod.cft_kw import _is_name, _is_kw
from lexermod.cft_token import Token
from parsemod.cft_ops import is_op
from parsemod.cft_expr import *


def _is_setvalue_expression(
        tokens: list[Token],
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0,
        init_type=''
) -> bool:
    tokens = extract_tokens(tokens, i)

    if tokens is None:
        return False

    if _is_kw(tokens[0], 'mut'):
        if len(tokens) < 4:
            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[-1], fill=True)
            return False

        if not init_type:
            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[0], fill=True)
            return False

        if init_type == 'val':
            errors_handler.final_push_segment(path, 'TypeError: constant value cannot be mutable', tokens[0], fill=True)
            return False

        tokens = tokens[1:]

    if len(tokens) >= 3 and _is_name(tokens[0]):
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

            if not _is_type_expression(tokens[2], errors_handler, path, namehandler):
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
    _tokens = tokens = extract_tokens(tokens, i)

    if _is_kw(_tokens[0], 'mut'):
        _tokens = _tokens[1:]

    name = _tokens[0].value
    new_value = None
    value_type = None

    # <value-name>
    res = {
        'type': 'set-value',
        '$tokens-len': len(tokens),  # temp value
        '$constant-expr': True  # temp value
    }

    namehandler_res = {
        'const': init_type == 'val'
    }

    _tokens = _tokens[1:]  # remove name-token

    if is_op(_tokens[0], ':'):
        # : <value-type>
        value_type = _tokens[1].value

        _tokens = _tokens[2:]

    if _tokens and is_op(_tokens[0], '='):
        # = <new-value>
        new_value = _generate_expression_syntax_object(
            _tokens,
            errors_handler,
            path,
            namehandler,
            i=1,
            expected_type=... if value_type is None else value_type
        )

        if value_type is None:
            value_type = get_value_returned_type(new_value)

        if errors_handler.has_errors():
            return {}

        res['$constant-expr'] = new_value['$constant-expr']

        del new_value['$tokens-len'], new_value['$constant-expr']

    res.update({
        'value-name': name,
        'value-type': value_type,
        'new-value': new_value
    })

    namehandler_res.update({
        'type': value_type,
        'value': new_value
    })

    if namehandler.has_localname(name):
        name_obj = namehandler.abs_current_obj['value'][name]

        if name_obj['const'] or name_obj['value'] is not None and not name_obj['mut']:
            errors_handler.final_push_segment(
                path,
                f'TypeError: cannot assign twice to {"constant" if name_obj["const"] else "immutable"} variable',
                tokens[0],
                fill=True
            )
            return {}

        if name_obj['const'] != namehandler_res['const']:
            errors_handler.final_push_segment(
                path,
                f'TypeError: `{name}` is interpreted as a constant, not a new binding',
                tokens[0],
                fill=True
            )
            return {}

        if name_obj['type'] != '$undefined' and name_obj['type'] != value_type and not init_type:
            errors_handler.final_push_segment(
                path,
                f'TypeError: expected type `{name_obj["type"]}`, got `{value_type}`',
                _tokens[1],
                fill=True
            )
            return {}

    if init_type:
        namehandler_res['mut'] = _is_kw(tokens[0], 'mut')

    namehandler.force_set_name(name, **namehandler_res)

    return res


__all__ = (
    '_is_setvalue_expression',
    '_generate_setvalue_syntax_object'
)
