from parsemod.cft_others import extract_tokens_with_code_body
from parsemod.cft_others import remove_newline_by_borders
from parsemod.cft_expr import _is_type_expression
from lexermod.cft_token import Token, TokenTypes
from cft_errors_handler import ErrorsHandler
from parsemod.cft_kw import _is_kw, _is_name
from cft_namehandler import NameHandler
from parsemod.cft_ops import is_op


def _is_segment(tokens: list[Token], errors_handler: ErrorsHandler, path: str, namehandler: NameHandler):
    if len(tokens) == 3 and _is_name(tokens[0]) and is_op(tokens[1], ':') and _is_type_expression(
            tokens[2],
            errors_handler,
            path,
            namehandler
    ):
        return True

    errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[-1], fill=True)
    return False


def _is_struct_init(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0
):
    tokens = extract_tokens_with_code_body(tokens, i)

    if tokens is None:
        return False

    if _is_kw(tokens[0], 'struct'):
        if len(tokens) == 3:
            if _is_name(tokens[1]) and tokens[2].type == TokenTypes.CURLY_BRACES:
                body_tokens = remove_newline_by_borders(tokens[2].value)

                if not body_tokens:
                    return True

                if body_tokens[0].type == TokenTypes.TUPLE:
                    for arg_tokens in body_tokens[0].value:
                        arg_tokens = remove_newline_by_borders(arg_tokens)

                        if not arg_tokens:
                            break

                        if not _is_segment(arg_tokens, errors_handler, path, namehandler):
                            return False

                    return True

                if _is_segment(body_tokens, errors_handler, path, namehandler):
                    return True

                return False

        errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[-1], fill=True)

    return False
