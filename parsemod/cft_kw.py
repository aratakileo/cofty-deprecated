from lexermod.cft_token import Token, TokenTypes
from cft_ops import OPS


# that names can not be used like a variable's, a function's name etc.
KEYWORDS = ['if', 'else', 'elif', 'let', 'var', 'True', 'False', 'fn']


def _is_kw(
        token: Token,
        kws: str | tuple | list = None  # name(s) of keyword(s)
):
    if kws is not None:
        return _is_kw(token) and token.value in kws

    return token.type == TokenTypes.NAME and token.value in KEYWORDS or token.value in OPS


def _is_name(token: Token, names: str | tuple | list = None):
    if names is not None:
        return _is_name(token) and token.value in names

    return token.type == TokenTypes.NAME and not _is_kw(token)


__all__ = (
    'KEYWORDS',
    '_is_kw',
    '_is_name'
)
