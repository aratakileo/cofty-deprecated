from parsemod.cft_setvalue import _is_setvalue_expression
from parsemod.cft_extract_tokens import extract_tokens
from parsemod.cft_kw import _is_kw, _is_name
from cft_errors_handler import ErrorsHandler
from parsemod.cft_is_codebody import *
from lexermod.cft_token import *
from typing import List, Tuple


def _is_fn_init(
        tokens: List[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        i: int = 0,
        stop_tokens: Tuple[DummyToken | TokenType] = ...
):
    """ "fn" <fn-name> "("<args>")" ("->" <returned-type>)? <code-body>"""

    tokens = extract_tokens(tokens, i, stop_tokens)

    if tokens is None or len(tokens) != 4 or not _is_kw(tokens[0], 'fn') or not _is_name(tokens[1]) \
            or tokens[2].type != TokenTypes.PARENTHESIS or not _is_code_body(tokens[3]):
        return False

    args_tokens = tokens[2].value

    if args_tokens:
        if args_tokens[0].type == TokenTypes.TUPLE:
            has_default_argument = False

            for arg_tokens in args_tokens[0].value:
                if not _is_setvalue_expression(arg_tokens, errors_handler, path):
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
        elif not _is_setvalue_expression(args_tokens, errors_handler, path):
            return False

    return True
