from cft_namehandler import NameHandler, get_value_returned_type
from cft_extract_tokens import extract_tokens
from cft_errors_handler import ErrorsHandler
from compile.cft_compile import get_num_type
from cft_kw import _is_kw, _is_name
from lexermod.cft_token import *
from typing import List, Tuple
import cft_ops as ops


def _is_type_expression(token: Token) -> bool:
    if token.type == TokenTypes.NAME:
        return True

    return False


def _is_value_expression(
        tokens: List[Token] | Token,
        i: int = 0,
        stop_tokens: Tuple[DummyToken | TokenType] = ...
) -> bool:
    """<expr>"""
    tokens = extract_tokens(tokens, i, stop_tokens)

    if tokens is None:
        return False

    if len(tokens) >= 1:
        if len(tokens) == 1:
            if tokens[0].type in (TokenTypes.NUMBER, TokenTypes.STRING) \
                    or _is_name(tokens[0]) or _is_name(tokens[0], ('True', 'False')):
                return True

            if tokens[0].type == TokenTypes.TUPLE:
                for item in tokens[0].value:
                    if not _is_value_expression(item):
                        return False

                return True

            if tokens[0].type in (TokenTypes.PARENTHESIS, TokenTypes.SQUARE_BRACKETS, TokenTypes.CURLY_BRACES):
                return not tokens[0].value or _is_value_expression(tokens[0].value)
        elif ops.is_op(tokens[0]) and not ops.is_op(tokens[1]) and _is_value_expression(tokens, 1):
            if tokens[0].value not in ops.LOPS: return False
            return True
        elif len(tokens) >= 3 and not ops.is_op(tokens[0]) and ops.is_op(tokens[1]) \
                and _is_value_expression(tokens[0]) and _is_value_expression(tokens, 2):
            return True

    return False


def _generate_expression_syntax_object(
        tokens: List[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0,
        right_i: int = 0,
        stop_tokens: Tuple[DummyToken | TokenType] = ...,
        expected_type: dict | str = ...,
        clearly_result=False  # to make subvalues without 'tokens' key
):
    tokens = extract_tokens(tokens, i, stop_tokens)
    tokens = tokens[:len(tokens) - right_i]

    res = {
        '$tokens-len': len(tokens),  # temp value
        'tokens': tokens
    }

    if len(tokens) == 1:
        res['returned-type'] = '$self'  # it is necessary to refer to key 'type'

        token = tokens[0]

        if token.type == TokenTypes.STRING:
            # includes strings like `'Hello World'` or `"Hello World"`, and chars like `c'H'` or `c"H"`

            _index = token.value.index(token.value[-1])

            res.update({
                'type': 'string' if 'c' not in token.value[:_index].lower() else 'char',  # `c` is prefix before quotes
                'value': token.value[_index + 1:-1]
            })
        elif token.type == TokenTypes.NUMBER:
            # includes any number format like integer or decimal

            res.update({
                'type': 'number',
                'value': token.value,
                'returned-type': get_num_type(token.value)
            })
        elif token.type == TokenTypes.NAME:
            res['value'] = token.value

            if token.value in ('True', 'False'):
                res['type'] = 'bool'
            else:
                res['type'] = 'name'
                res['returned-type'] = '$undefined' \
                    if True \
                    else namehandler.get_current_name_body(token.value)['type']

                # TODO: remove this if-statement when, returned-type system will be finished
                # TODO: replace to:
                # TODO: namehandler.get_current_name_body(token.value)['type']
        elif token.type == TokenTypes.TUPLE:
            # <expression>, <expression>

            res.update({
                'type': 'tuple',
                'value': []
            })

            for item in token.value:
                res['value'].append(_generate_expression_syntax_object(item, errors_handler, path, namehandler))

                del res['value'][-1]['$tokens-len']
        elif token.type in (TokenTypes.PARENTHESIS, TokenTypes.SQUARE_BRACKETS, TokenTypes.CURLY_BRACES):
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
    else:
        res.update(
            ops.generate_op_expression(tokens, errors_handler, path, namehandler, _generate_expression_syntax_object)
        )

        if clearly_result:
            if 'value' in res:
                del res['value']['tokens']
            else:
                del res['rvalue']['tokens'], res['lvalue']['tokens']

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
        return {'$tokens-len': res['$tokens-len']}

    return res


__all__ = (
    '_is_value_expression',
    '_generate_expression_syntax_object',
    '_is_type_expression'
)
