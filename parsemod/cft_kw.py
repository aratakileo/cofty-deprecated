from lexermod.cft_token import Token, TokenTypes
from parsemod.cft_others import extract_tokens
from cft_errors_handler import ErrorsHandler
from parsemod.cft_ops import ALL_OPS, is_op
from cft_namehandler import NameHandler


# that names can not be used like a variable's, a function's name etc.
KEYWORDS = ['if', 'else', 'elif', 'let', 'val', 'True', 'False', 'fn', 'return', 'None', 'mut', 'struct', 'mod']


def _is_kw(
        token: Token,
        kws: str | tuple | list = None  # name(s) of keyword(s)
):
    if kws is not None:
        return _is_kw(token) and token.value in kws

    return token.type == TokenTypes.NAME and token.value in KEYWORDS or token.value in ALL_OPS


def _is_base_name(token: Token):
    return token.type == TokenTypes.NAME and not _is_kw(token)


def _is_name(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0
):
    tokens = extract_tokens(tokens, i)
    namehandler = namehandler.copy()

    if len(tokens) > 1:
        if len(tokens) % 2 == 0:
            errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[-1], fill=True)
            return False

        next_is_namespace_name = True

        for i in range(0, len(tokens), 2):
            name_token = tokens[i]
            name = name_token.value

            if not _is_base_name(name_token):
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', name_token, fill=True)
                return False

            if not namehandler.has_globalname(name):
                errors_handler.final_push_segment(
                    path,
                    f'NameError: name `{name}` is not defined',
                    name_token,
                    fill=True
                )
                return False

            if len(tokens) - 1 == i:
                return True

            op_token = tokens[i + 1]

            if is_op(op_token, '.'):
                next_is_namespace_name = False
            elif not is_op(op_token, '::') or not next_is_namespace_name:
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', op_token, fill=True)
                return False

            if namehandler.get_current_body(name)['type'] not in ('$struct', '$mod') and next_is_namespace_name:
                errors_handler.final_push_segment(
                    path,
                    f'AccessError: `{name}` is not a module or structure',
                    name_token,
                    fill=True
                )
                return False

            temp = namehandler.get_current_body(name)

            if 'value' not in temp or temp['value'] is None or 'type' in temp['value']:
                errors_handler.final_push_segment(
                    path,
                    f'AccessError: cannot get access to names of `{name}`',
                    name_token,
                    fill=True
                )
                return False

            namehandler.use_localspace(name)

    return _is_base_name(tokens[0])


__all__ = (
    'KEYWORDS',
    '_is_kw',
    '_is_name',
    '_is_base_name'
)
