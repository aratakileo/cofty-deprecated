from parsemod.cft_others import extract_tokens_with_code_body, _is_code_body
from parsemod.cft_setvalue import _is_setvalue_expression
from parsemod.cft_kw import _is_kw, _is_name
from cft_errors_handler import ErrorsHandler
from parsemod.cft_ops import is_op
from lexermod.cft_token import *


def _is_fn_init(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        i: int = 0
):
    """ "fn" <fn-name> "("<arg>*")" (":" <returned-type>)? <code-body>"""

    tokens = extract_tokens_with_code_body(tokens, i)

    if tokens is None or not _is_kw(tokens[0], 'fn'):
        return False

    type_annotation = len(tokens) != 4

    if len(tokens) not in (4, 6) or not _is_name(tokens[1]) or tokens[2].type != TokenTypes.PARENTHESIS or not (
            type_annotation or _is_code_body(tokens[3])
    ) or (
            type_annotation and not (is_op(tokens[3], '->') and _is_name(tokens[4]) and _is_code_body(tokens[5]))
    ):
        errors_handler.final_push_segment(
            path,
            'SyntaxError: invalid syntax',
            tokens[-1],
            fill=True
        )
        return False

    args_tokens = tokens[2].value

    if args_tokens:
        if args_tokens[0].type == TokenTypes.TUPLE:
            has_default_argument = False

            for arg_tokens in args_tokens[0].value:
                if not arg_tokens:
                    break

                if not _is_setvalue_expression(arg_tokens, errors_handler, path, init_type='let'):
                    errors_handler.final_push_segment(
                        path,
                        'SyntaxError: invalid syntax',
                        arg_tokens[0],
                        fill=True
                    )
                    return False

                if DummyToken(TokenTypes.OP, '=') in arg_tokens:
                    has_default_argument = True
                elif has_default_argument:
                    errors_handler.final_push_segment(
                        path,
                        'SyntaxError: non-default argument follows default argument',
                        arg_tokens[0],
                        fill=True
                    )
                    return False
        elif not _is_setvalue_expression(args_tokens, errors_handler, path, init_type='let'):
            return False

    return True
