from cft_namehandler import NameHandler, get_value_returned_type, get_abs_composed_name
from parsemod.cft_name import is_name, is_kw, compose_name
from parsemod.cft_others import extract_tokens
from cft_errors_handler import ErrorsHandler
from lexermod.cft_token import Token
from parsemod.cft_ops import is_op
from parsemod.cft_expr import *
from copy import deepcopy


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

    if is_kw(tokens[0], 'mut'):
        if len(tokens) < 4:
            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[-1], fill=True)
            return False

        if not init_type:
            errors_handler.final_push_segment(
                path,
                'NameError: using `mut` is not possible for an already existing variable',
                tokens[0],
                fill=True
            )
            return False

        if init_type == 'val':
            errors_handler.final_push_segment(
                path,
                'ValueError: constant value cannot be mutable',
                tokens[0],
                fill=True
            )
            return False

        tokens = tokens[1:]

    if is_kw(tokens[0]):
        return False

    if len(tokens) >= 3:
        sep_op_index = -1
        assign_op_index = -1

        for i in range(len(tokens)):
            if is_op(tokens[i], ':'):
                sep_op_index = i

            if is_op(tokens[i], '='):
                assign_op_index = i
                break

        if sep_op_index == -1 and assign_op_index == -1:
            return False

        nearest_index = sep_op_index if sep_op_index != -1 else assign_op_index

        if not is_name(
                tokens[:nearest_index],
                errors_handler,
                path,
                namehandler,
                check_define=not init_type,
                debug_info=_is_setvalue_expression.__name__
        ):
            return False

        # <value-name>: <value-type>
        if sep_op_index != -1:
            if not init_type:
                errors_handler.final_push_segment(
                    path,
                    'TypeError: type annotation is not possible for an already existing variable',
                    tokens[sep_op_index + 1],
                    fill=True
                )
                return False

            if not _is_type_expression(
                tokens[:assign_op_index if assign_op_index != -1 else None],
                errors_handler,
                path,
                namehandler,
                sep_op_index + 1
            ):
                return False

        # <value-name> (: <value-type)? = <new-value>
        if assign_op_index != -1:
            if not _is_value_expression(tokens, errors_handler, path, namehandler, assign_op_index + 1):
                if not errors_handler.has_errors():
                    errors_handler.final_push_segment(
                        path,
                        'SyntaxError: invalid syntax',
                        tokens[assign_op_index + 1],
                        fill=True
                    )
                return False
        elif init_type == 'val':
            errors_handler.final_push_segment(path, 'ValueError: constant without value', tokens[-1], fill=True)
            errors_handler.final_push_segment(
                path,
                f'provide a definition for the constant: `= <expr>`',
                tokens[-1],
                type=ErrorsHandler.HELP,
                offset=len(tokens[-1].value) - 1
            )
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
    tokens = _tokens = extract_tokens(tokens, i)

    if is_kw(_tokens[0], 'mut'):
        _tokens = _tokens[1:]

    sep_op_index = -1
    assign_op_index = -1

    for i in range(len(_tokens)):
        if is_op(_tokens[i], ':'):
            sep_op_index = i

        if is_op(_tokens[i], '='):
            assign_op_index = i
            break

    nearest_index = sep_op_index if sep_op_index != -1 else assign_op_index
    name_tokens = _tokens[:nearest_index]
    composed_name = compose_name(name_tokens)
    local_name = name_tokens[-1].value

    if len(name_tokens) > 1 and init_type:
        errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', name_tokens[1], fill=True)
        return {}

    new_value = None
    value_type = None

    res = {
        'type': 'init-value' if init_type else 'set-value',
        '$tokens-len': len(tokens),  # temp value
        '$constant-expr': True  # temp value
    }

    namehandler_res = {
        'const': init_type == 'val'
    }

    if init_type:
        namehandler_res.update({
            'name': composed_name,
            '*parent': namehandler.abs_current_obj
        })

    if sep_op_index != -1:
        # : <value-type>

        value_type = get_abs_composed_name(namehandler.get_name_obj(compose_name(_tokens[sep_op_index + 1: assign_op_index if assign_op_index != -1 else None]), from_obj=namehandler._accessible_names))

    if assign_op_index != -1:
        # = <new-value>

        new_value = _generate_expression_syntax_object(
            _tokens,
            errors_handler,
            path,
            namehandler,
            i=assign_op_index + 1,
            expected_type=... if value_type is None else value_type
        )

        if errors_handler.has_errors():
            return {}

        if value_type is None:
            value_type = get_value_returned_type(new_value)

        if errors_handler.has_errors():
            return {}

        res['$constant-expr'] = new_value['$constant-expr']

        del new_value['$tokens-len'], new_value['$constant-expr']

    res.update({
        'value-name': composed_name,
        'value-type': value_type,
        'new-value': new_value
    })

    namehandler_res.update({
        'type': value_type,
        'value': new_value
    })

    if new_value is not None and new_value['type'] == '$call-name':
        _value = deepcopy(namehandler.get_name_obj(new_value['returned-type'])['value'])

        k = 0
        for key in _value:
            _value[key].update({
                'value': new_value['args'][k],
                '*parent': namehandler_res
            })
            k += 1

        namehandler_res['value'] = _value

    if namehandler.has_localname(composed_name):
        name_obj = _name_obj = namehandler.get_name_obj(composed_name)

        while 'const' not in _name_obj:
            _name_obj = _name_obj['*parent']

        if _name_obj['const'] or _name_obj['value'] is not None and not _name_obj['mut']:
            errors_handler.final_push_segment(
                path,
                f'ValueError: cannot assign twice to {"constant" if _name_obj["const"] else "immutable"} variable',
                name_tokens[-1],
                fill=True
            )
            return {}

        if _name_obj['const'] != namehandler_res['const']:
            errors_handler.final_push_segment(
                path,
                f'ValueError: `{local_name}` is interpreted as a constant, not a new binding',
                name_tokens[-1],
                fill=True
            )
            return {}

        if value_type != '$undefined' and name_obj['type'] != value_type and not init_type:
            errors_handler.final_push_segment(
                path,
                f'TypeError: expected type `{name_obj["type"]}`, got `{value_type}`',
                _tokens[assign_op_index + 1],
                fill=True
            )
            return {}

    if init_type:
        namehandler_res['mut'] = is_kw(tokens[0], 'mut')

    namehandler.force_set_name(composed_name, **namehandler_res)

    return res


__all__ = (
    '_is_setvalue_expression',
    '_generate_setvalue_syntax_object'
)
