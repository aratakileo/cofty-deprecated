from parsemod.cft_extract_tokens import extract_tokens
from lexermod.cft_token import *


def _is_code_body(tokens: list[Token] | Token, i: int = 0):
    """<code-body>"""

    tokens = extract_tokens(tokens, i)

    if tokens is None or len(tokens) != 1 and tokens[0].type != TokenTypes.CURLY_BRACES:
        return False

    return True


__all__ = (
    '_is_code_body',
)
