from lexermod.cft_token import *


stop_tokens = (TokenType(TokenTypes.ENDMARKER), TokenType(TokenTypes.NEWLINE))


def extract_tokens(tokens: list[Token] | Token, i: int = 0):
    if isinstance(tokens, Token):
        tokens = [tokens]

    if i >= len(tokens):
        return None

    tokens = tokens[i:]

    for k in range(len(tokens)):
        if tokens[k] in stop_tokens:
            tokens = tokens[:k]
            break

    if len(tokens) == 0:
        return None

    return tokens


__all__ = (
    'extract_tokens',
)
