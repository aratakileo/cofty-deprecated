from lexermod.cft_token import Token, TokenTypes
from parsemod.cft_others import extract_tokens
from cft_errors_handler import ErrorsHandler
from parsemod.cft_ops import ALL_OPS, is_op
from cft_namehandler import NameHandler

# that names can not be used like a variable's, a function's name etc.
KEYWORDS = ['if', 'else', 'elif', 'let', 'val', 'True', 'False', 'fn', 'return', 'None', 'mut', 'struct', 'mod', 'use']


def is_kw(
        token: Token,
        kws: str | tuple | list = None  # name(s) of keyword(s)
):
    if kws is not None:
        return is_kw(token) and token.value in kws

    return token.type == TokenTypes.NAME and token.value in KEYWORDS or token.value in ALL_OPS


def is_base_name(token: Token):
    return token.type == TokenTypes.NAME and not is_kw(token)


def is_name(
        tokens: list[Token] | Token,
        errors_handler: ErrorsHandler,
        path: str,
        namehandler: NameHandler,
        i: int = 0,
        check_define=True,
        debug_info='None'
):
    tokens = extract_tokens(tokens, i)

    if tokens is None:
        return False

    namehandler = namehandler.copy()

    if len(tokens) > 1:
        if len(tokens) % 2 == 0:
            # if not errors_handler.has_errors():
            #     errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', tokens[-1], fill=True)
            return False

        next_is_namespace_name = True

        for k in range(0, len(tokens), 2):
            name_token = tokens[k]
            name = name_token.value

            if not is_base_name(name_token):
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

            if len(tokens) - 1 == k:
                return True

            op_token = tokens[k + 1]

            if is_op(op_token, '.'):
                next_is_namespace_name = False

                if namehandler.get_current_body(name)['type'] in ('$mod',):
                    errors_handler.final_push_segment(
                        path,
                        f'AccessError: `{name}` is not an initialized structure',
                        name_token,
                        fill=True
                    )
                    errors_handler.final_push_segment(
                        path,
                        f'did you mean `::` instead `.`?',
                        op_token,
                        type=ErrorsHandler.HELP
                    )
                    return False
            elif not is_op(op_token, '::') or not next_is_namespace_name:
                errors_handler.final_push_segment(path, 'SyntaxError: invalid syntax', op_token, fill=True)
                return False

            if namehandler.get_current_body(name)['type'] not in ('$mod',) and next_is_namespace_name:
                errors_handler.final_push_segment(
                    path,
                    f'AccessError: `{name}` is not a module',
                    name_token,
                    fill=True
                )
                return False

            temp = namehandler.get_current_body(name)

            if 'value' not in temp or temp['value'] is None:
                errors_handler.final_push_segment(
                    path,
                    f'ValueError: `{name}` is not initialized',
                    name_token,
                    fill=True
                )
                return False

            if 'type' in temp['value'] and temp['value']['type'] not in '$init-cls':
                errors_handler.final_push_segment(
                    path,
                    f'AccessError: cannot get access to names of `{name}`',
                    name_token,
                    fill=True
                )
                return False

            namehandler.use_localspace(name)

    if not is_base_name(tokens[0]):
        return False

    name_token = tokens[0]
    name = name_token.value

    if not namehandler.has_globalname(name) and check_define:
        errors_handler.final_push_segment(
            path,
            f'NameError: name `{name}` is not defined',
            name_token,
            fill=True
        )
        return False

    return True


def compose_name(name_tokens: list[Token] | Token):
    if isinstance(name_tokens, Token):
        return name_tokens.value

    if len(name_tokens) == 1:
        return name_tokens[0].value

    return [token.value for token in name_tokens[::2]]


__all__ = (
    'KEYWORDS',
    'is_kw',
    'is_name',
    'is_base_name',
    'compose_name'
)
