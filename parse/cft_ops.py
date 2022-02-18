from cft_errors_handler import ErrorsHandler
from cft_lexer import Token, TokenTypes
from typing import List


# left operators: <op> <expr>
LOPS = ['+', '-', '*', '~', 'not']

# <expr> <op> <expr>
MIDDLE_OPS = [
    *LOPS[:3],
    '**', '|', '&', '<<', '>>', '%', '==', '<=', '>=', '>', '<', 'or', 'and', 'in', 'not in', 'is', 'is not'
]

# all user's operators
OPS = list(set(LOPS) | set(MIDDLE_OPS))

# operators that are always return type `bool`
BOOL_OPS = ('not', 'or', 'and', 'in', 'not in', 'is', 'is not', '==', '<=', '>=', '<', '>')


def is_op(token: Token):
    return token.type in (TokenTypes.OP, TokenTypes.NAME) and token.value in OPS


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
        tokens: List[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        fn_generate_expression_syntax_object
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

    if 'value' not in last_lvalue:
        last_lvalue.update(fn_generate_expression_syntax_object(tokens[i], errors_handler, path))

    tokens = tokens[i:]

    del last_lvalue['$tokens-len']

    if len(tokens) == 1:
        res.update(invalid_lvalue)
    else:
        invalid_rvalue = fn_generate_expression_syntax_object(tokens, errors_handler, path, 2)

        del invalid_rvalue['$tokens-len']

        new_value = {
            'type': 'op',
            'op': tokens[1].value,
            'lvalue': invalid_lvalue,
            'rvalue': invalid_rvalue
        }

        if invalid_rvalue['type'] == 'op' and 'value' not in invalid_rvalue \
                and MIDDLE_OPS_PRIORITY[invalid_rvalue['op']] < MIDDLE_OPS_PRIORITY[tokens[1].value]:
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
                    'op': tokens[1].value,
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
