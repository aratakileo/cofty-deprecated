from lexermod.cft_token import Token, TokenTypes
from cft_ops import OPS


# that names can not be used like a variable's, a function's name etc.
KEYWORDS = ['if', 'else', 'elif', 'let', 'var', 'True', 'False']


def _is_kw(
        token: Token,
        kws=()  # TODO: Why is this necessary?
):
    if len(kws) != 0:
        return _is_kw(token) and token.value in kws

    return token.type == TokenTypes.NAME and token.value in KEYWORDS or token.value in OPS


__all__ = (
    'KEYWORDS',
    '_is_kw'
)
