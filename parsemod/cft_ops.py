from lexermod.cft_token import Token, TokenTypes
from cft_errors_handler import ErrorsHandler
from cft_namehandler import NameHandler


LBOOL_OPS = ['not']
"""Left operators that are always return type `bool`"""

LOPS = ['+', '-', '*', '~', *LBOOL_OPS]
"""Left operators: <op> <expr>"""

MIDDLE_BOOL_OPS = ['or', 'and', 'in', 'not in', 'is', 'is not', '==', '<=', '>=', '<', '>']
"""Middle operators that are always return type `bool`"""

MIDDLE_OPS = [*LOPS[:3], '**', '|', '&', '<<', '>>', '%', *MIDDLE_BOOL_OPS]
"""Middle ops: <expr> <op> <expr>"""

ASSIGN_OPS = ['=']
"""Assign operators: <name> <op> <expr>"""

USER_OPS = list(set(LOPS) | set(MIDDLE_OPS)) + ASSIGN_OPS
"""All user's operators (overloadable)"""

NOTUSER_OPS = [':', '->']
"""All not user's operators (non-overloadable)"""

ALL_OPS = USER_OPS + NOTUSER_OPS
"""Absolutely all operators"""

BOOL_OPS = [*LBOOL_OPS, *MIDDLE_BOOL_OPS]
"""Operators that are always return type `bool`"""


def is_op(
        token: Token,
        ops: str | tuple | list = None,
        source=ALL_OPS
):
    if ops is not None:
        return is_op(token) and token.value in ops

    return token.type in (TokenTypes.OP, TokenTypes.NAME) and token.value in source


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


def generate_op_expression(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        fn_generate_expression_syntax_object,  # It's needs to avoid `CircularImport` error
        fn_is_name_call_expression,
        fn_generate_name_call_expression
):
    res = {}
    invalid_lvalue = {
        'type': 'op'
    }
    last_lvalue = invalid_lvalue

    i = 0
    while is_op(tokens[i]):
        last_lvalue.update({
            'op': tokens[i].value,
            'value': {'type': 'op'}
        })
        last_lvalue = last_lvalue['value']

        i += 1

    tokens = tokens[i:]

    if fn_is_name_call_expression(tokens):
        off = 1

        last_lvalue.update(fn_generate_name_call_expression(tokens, errors_handler, path, namehandler))
    else:
        off = 0

        last_lvalue.update(
            fn_generate_expression_syntax_object(tokens[0], errors_handler, path, namehandler, effect_checker=True)
        )

    if errors_handler.has_errors():
        return {}

    res['$has-effect'] = last_lvalue['$has-effect']  # temp value
    res['$constant-expr'] = last_lvalue['$constant-expr']  # temp value

    if '$tokens-len' in last_lvalue:
        del last_lvalue['$tokens-len']  # cleaning the temp value

    del last_lvalue['$has-effect'], last_lvalue['$constant-expr']  # cleaning the temp values

    if 1 <= len(tokens) <= 2:
        # LOPS generation
        res.update(invalid_lvalue)
    else:
        # MIDDLE_OPS generation

        invalid_rvalue = fn_generate_expression_syntax_object(
            tokens,
            errors_handler,
            path,
            namehandler,
            2 + off,
            effect_checker=True
        )

        if errors_handler.has_errors():
            return {}

        res['$has-effect'] = res['$has-effect'] or invalid_rvalue['$has-effect']  # temp value
        res['$constant-expr'] = res['$constant-expr'] and invalid_rvalue['$constant-expr'] \
            and res['$constant-expr'] is True  # `is True` needs when `False and False`
                                                    # for `False and False and False is not False => False`

        del invalid_rvalue['$tokens-len'], invalid_rvalue['$has-effect'], invalid_rvalue['$constant-expr']

        new_value = {
            'type': 'op',
            'op': tokens[1 + off].value,
            'lvalue': invalid_lvalue,
            'rvalue': invalid_rvalue
        }

        if invalid_rvalue['type'] == 'op' and 'value' not in invalid_rvalue \
                and MIDDLE_OPS_PRIORITY[invalid_rvalue['op']] < MIDDLE_OPS_PRIORITY[tokens[1 + off].value]:
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
                    'op': tokens[1 + off].value,
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

    return res


__all__ = (
    'LBOOL_OPS',
    'LOPS',
    'MIDDLE_BOOL_OPS',
    'MIDDLE_OPS',
    'ASSIGN_OPS',
    'USER_OPS',
    'NOTUSER_OPS',
    'ALL_OPS',
    'BOOL_OPS',
    'is_op',
    'generate_op_expression'
)
