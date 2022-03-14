from parsemod.cft_extract_tokens import extract_tokens
from lexermod.cft_token import *
from typing import List, Tuple


def _is_code_body(tokens: List[Token] | Token, i: int = 0, stop_tokens: Tuple[DummyToken | TokenType] = ...):
    """<code-body>"""

    tokens = extract_tokens(tokens, i, stop_tokens)

    if tokens is None:
        return False

    if len(tokens) == 1 and tokens[0].type == TokenTypes.CURLY_BRACES:
        return True

    return False


__all__ = (
    '_is_code_body',
)
