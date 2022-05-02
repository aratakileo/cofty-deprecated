from parsemod.cft_others import extract_tokens_with_code_body, _is_code_body
from parsemod.cft_setvalue import _is_setvalue_expression
from parsemod.cft_expr import _is_type_expression
from parsemod.cft_name import is_kw, is_base_name
from cft_errors_handler import ErrorsHandler
from cft_namehandler import NameHandler
from parsemod.cft_ops import is_op
from lexermod.cft_token import *


def _is_fn_init(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0
):
    """ "fn" <fn-name> "("<arg>*")" (":" <returned-type>)? <code-body>"""

    tokens = extract_tokens_with_code_body(tokens, i)

    if tokens is None or not is_kw(tokens[0], 'fn'):
        return False

    has_type_annotation = len(tokens) >= 4 and is_op(tokens[3], '->')

    if len(tokens) < 4 or not is_base_name(tokens[1]) or tokens[2].type != TokenTypes.PARENTHESIS \
            or not _is_code_body(tokens[-1]) or (
                has_type_annotation and not _is_type_expression(tokens[:-1], errors_handler, path, namehandler, 4)
            ) or (not has_type_annotation and len(tokens) != 4):
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

                if not _is_setvalue_expression(arg_tokens, errors_handler, path, namehandler, init_type='let'):
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
        elif not _is_setvalue_expression(args_tokens, errors_handler, path, namehandler, init_type='let'):
            return False

    return True
