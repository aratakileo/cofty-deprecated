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


def _is_code_body(tokens: list[Token] | Token, i: int = 0):
    """<code-body>"""

    tokens = extract_tokens(tokens, i)

    if tokens is None:
        return False

    if len(tokens) == 1 and tokens[0].type == TokenTypes.CURLY_BRACES \
            or len(tokens) == 2 and tokens[0].type == TokenTypes.NEWLINE and tokens[1].type == TokenTypes.CURLY_BRACES:
        return True

    return False


def extract_tokens_with_code_body(tokens: list[Token] | Token, i: int = 0):
    extracted_tokens = extract_tokens(tokens, i)

    if extracted_tokens is None or extracted_tokens[-1].type == TokenTypes.CURLY_BRACES \
            or len(tokens) < len(extracted_tokens) + 1:
        return extracted_tokens

    extracted_tokens = tokens[i:][:len(extracted_tokens) + 2]

    del extracted_tokens[-2]

    return extracted_tokens


def remove_newline_by_borders(tokens: list[Token]):
    tokens = tokens.copy()

    if tokens and tokens[0].type == TokenTypes.NEWLINE:
        del tokens[0]

    if tokens and tokens[-1].type == TokenTypes.NEWLINE:
        del tokens[-1]

    return tokens


__all__ = (
    'extract_tokens',
    'extract_tokens_with_code_body',
    'remove_newline_by_borders',
    '_is_code_body'
)
