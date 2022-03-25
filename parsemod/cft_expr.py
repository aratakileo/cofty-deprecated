from cft_namehandler import NameHandler, get_value_returned_type
from parsemod.cft_others import extract_tokens
from cft_errors_handler import ErrorsHandler
from compile.cft_compile import get_num_type
from parsemod.cft_kw import _is_name, _is_kw
from py_utils import isnotfinished
from lexermod.cft_token import *
import parsemod.cft_ops as ops


def _is_type_expression(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0
) -> bool:
    tokens = extract_tokens(tokens, i)

    if _is_name(tokens[0]):
        name = tokens[0].value
        if namehandler.has_globalname(name):
            if namehandler.isinstance(name, 'struct'):
                return True

            errors_handler.final_push_segment(
                path,
                f'TypeError: name `{name}` is not a type',
                tokens[0],
                fill=True
            )

        errors_handler.final_push_segment(
            path,
            f'NameError: name `{name}` is not defined',
            tokens[0],
            fill=True
        )
        return False

    errors_handler.final_push_segment(
        path,
        f'SyntaxError: invalid syntax',
        tokens[0],
        fill=True
    )

    return False


def _is_name_call_expression(tokens: list[Token] | Token, i: int = 0, without_tail=False):
    tokens = tokens[i:]

    if len(tokens) < 2 or (without_tail and len(tokens) != 2) or not _is_name(tokens[0]) \
            or tokens[1].type != TokenTypes.PARENTHESIS:
        return False

    return True


def _is_value_expression(tokens: list[Token] | Token, i: int = 0) -> bool:
    """<expr>"""
    tokens = extract_tokens(tokens, i)

    if tokens is None:
        return False

    if len(tokens) == 1:
        if tokens[0].type in (TokenTypes.NUMBER, TokenTypes.STRING) \
                or _is_name(tokens[0]) or _is_kw(tokens[0], ('True', 'False')):
            return True

        if tokens[0].type == TokenTypes.TUPLE:
            for item in tokens[0].value:
                if not _is_value_expression(item):
                    return False
            return True

        if tokens[0].type in (TokenTypes.PARENTHESIS, TokenTypes.SQUARE_BRACKETS, TokenTypes.CURLY_BRACES):
            return not tokens[0].value or _is_value_expression(tokens[0].value)
    elif ops.is_op(tokens[0], source=ops.LOPS) and _is_value_expression(tokens, 1):
        # LOPS check

        return True
    elif len(tokens) >= 3:
        # MIDDLE_OPS check

        if _is_name_call_expression(tokens[:2], without_tail=True):
            off = 1
        elif _is_value_expression(tokens[0]):
            off = 0
        else:
            return False

        if ops.is_op(tokens[1 + off], source=ops.MIDDLE_OPS) and _is_value_expression(tokens, 2 + off):
            return True
    elif _is_name_call_expression(tokens, without_tail=True):
        # calling name expression check

        return True

    return False


def _generate_name_call_expression(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler
):
    name = tokens[0].value
    if not namehandler.has_globalname(name):
        errors_handler.final_push_segment(path, f'NameError: name `{name}` is not defined', tokens[0], fill=True)

        return {}

    if not namehandler.isinstance(name, ('fn', 'struct')):
        errors_handler.final_push_segment(
            path,
            f'NameError: name `{name}` is not a function or structure',
            tokens[0],
            fill=True
        )

        return {}

    args_tokens = []

    if tokens[1].value:
        if tokens[1].value[0].type == TokenTypes.TUPLE:
            args_tokens = tokens[1].value[0].value

            if not args_tokens[-1]:
                del args_tokens[-1]
        else:
            args_tokens = [tokens[1].value]

    namehandler_obj = namehandler.get_current_body(name).copy()

    if namehandler_obj['type'] == 'struct':
        args_dict = namehandler_obj['value']
        expected_kwargs = list(args_dict.keys())
        max_args = positional_args = len(expected_kwargs)
        returned_type = namehandler_obj['name']
    else:
        args_dict = namehandler_obj['args']
        expected_kwargs = list(args_dict.keys())
        max_args = namehandler_obj['max-args']
        positional_args = namehandler_obj['positional-args']
        returned_type = namehandler_obj['returned-type']

    required_positional_args = len(args_tokens)

    if required_positional_args > max_args:
        errors_handler.final_push_segment(
            path,
            f'TypeError: {name}() takes {max_args} positional arguments '
            f'but {required_positional_args} was given',
            tokens[1],
            fill=True
        )

        return {}

    if required_positional_args < positional_args:
        missing = positional_args - required_positional_args
        missed_args = expected_kwargs[required_positional_args: positional_args]
        error_tail = f'`{missed_args[-1]}`'

        if missing > 1:
            error_tail = f'`{missed_args[-2]}` and ' + error_tail

            if missing > 2:
                for missed_arg in missed_args[:-2][::-1]:
                    error_tail = f'`{missed_arg}`, ' + error_tail

        error_tail = ('' if missing == 1 else 's') + ': ' + error_tail

        errors_handler.final_push_segment(
            path,
            f'TypeError: {name}() missing {missing} required positional argument' + error_tail,
            tokens[1],
            fill=True
        )

        return {}

    args = []
    for i in range(len(args_tokens)):
        arg_tokens = args_tokens[i]

        if not arg_tokens:
            break

        arg = _generate_expression_syntax_object(arg_tokens, errors_handler, path, namehandler)

        if errors_handler.has_errors():
            return {}

        del arg['$tokens-len']

        expected_type = args_dict[expected_kwargs[i]]
        expected_type = expected_type['type'] if expected_type['value'] is None \
            else get_value_returned_type(expected_type['value'])

        if arg['returned-type'] != '$undefined' and get_value_returned_type(arg) != expected_type:
            errors_handler.final_push_segment(
                path,
                f'TypeError: expected type `{expected_type}`, got `{get_value_returned_type(arg)}`',
                arg_tokens[0],
                fill=True
            )

        args.append(arg)

    return {
        'type': '$call-name',
        'called-name': name,
        'args': args,
        'returned-type': returned_type,
        '$has-effect': True,  # temp value
        '$constant-expr': False  # temp value
    }


def _generate_expression_syntax_object(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0,
        right_i: int = 0,
        expected_type: dict | str = ...,
        effect_checker=False
):
    tokens = extract_tokens(tokens, i)
    tokens = tokens[:len(tokens) - right_i]

    res = {
        '$tokens-len': len(tokens),  # temp value
        '$has-effect': False,  # temp value,
        '$constant-expr': True  # temp value
    }

    if len(tokens) == 1:
        res['returned-type'] = '$self'  # it is necessary to refer to key 'type'

        token = tokens[0]

        if token.type == TokenTypes.STRING:
            # includes strings like `'Hello World'` or `"Hello World"`, and chars like `c'H'` or `c"H"`

            _index = token.value.index(token.value[-1])

            res.update({
                # `c` is prefix before quotes that's means is char, not string
                'type': 'str' if 'c' not in token.value[:_index].lower() else 'char',
                'value': token.value[_index + 1:-1]
            })
        elif token.type == TokenTypes.NUMBER:
            # includes any number format like integer or decimal

            res.update({
                'type': get_num_type(token.value),
                'value': token.value
            })
        elif token.type == TokenTypes.NAME:
            res['value'] = token.value

            if token.value in ('True', 'False'):
                res['type'] = 'bool'
            elif not namehandler.has_globalname(token.value):
                errors_handler.final_push_segment(
                    path,
                    f'NameError: name `{token.value}` is not defined',
                    tokens[0],
                    fill=True
                )

                return {}
            else:
                res.update({
                    'type': 'name',
                    '$constant-expr': False
                })

                _obj = namehandler.get_current_body(token.value)

                if namehandler.isinstance(token.value, 'fn'):
                    res['returned-type'] = _obj['returned-type']
                else:
                    res['returned-type'] = _obj['type']
        elif token.type == TokenTypes.TUPLE:
            # <expression>, <expression>
            isnotfinished()

            res.update({
                'type': 'tuple',
                'value': []
            })

            for item in token.value:
                res['value'].append(_generate_expression_syntax_object(item, errors_handler, path, namehandler))

                del res['value'][-1]['$tokens-len']
        elif token.type in (TokenTypes.PARENTHESIS, TokenTypes.SQUARE_BRACKETS, TokenTypes.CURLY_BRACES):
            isnotfinished()

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
                res = _generate_expression_syntax_object(token.value, errors_handler, path, namehandler)

                if token.type != TokenTypes.PARENTHESIS:
                    res['type'] = 'list' if token.type == TokenTypes.SQUARE_BRACKETS else 'set'

                    if res['type'] != 'tuple':
                        res['value'] = [res['value']]
    elif _is_name_call_expression(tokens, without_tail=True):
        res.update(_generate_name_call_expression(tokens, errors_handler, path, namehandler))
    else:
        res.update(ops.generate_op_expression(
            tokens,
            errors_handler,
            path,
            namehandler,
            _generate_expression_syntax_object,
            _is_name_call_expression,
            _generate_name_call_expression
        ))

    if errors_handler.has_errors():
        return {}

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
        return {}

    if not effect_checker:
        del res['$has-effect']

    return res


__all__ = (
    '_is_value_expression',
    '_generate_expression_syntax_object',
    '_is_type_expression'
)
