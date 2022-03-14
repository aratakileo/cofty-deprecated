from lexermod.cft_token import *
from typing import List, Tuple


default_stop_tokens = (TokenType(TokenTypes.ENDMARKER), TokenType(TokenTypes.NEWLINE))


def extract_tokens(
        tokens: List[Token] | Token,
        i: int = 0,
        stop_tokens: Tuple[DummyToken | TokenType] = ...
):
    if isinstance(tokens, Token):
        tokens = [tokens]

    if i >= len(tokens):
        return None

    tokens = tokens[i:]

    if stop_tokens is ...:
        stop_tokens = default_stop_tokens

    for k in range(len(tokens)):
        if tokens[k] in stop_tokens:
            return tokens[:k]

    return tokens


__all__ = (
    'extract_tokens',
    'default_stop_tokens'
)
