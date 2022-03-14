from parsemod.cft_extract_tokens import extract_tokens
from parsemod.cft_kw import _is_kw, _is_name
from parsemod.cft_is_codebody import *
from lexermod.cft_token import *
from typing import List, Tuple

from py_utils import isnotfinished  # temp import


def _is_fn_init(tokens: List[Token] | Token, i: int = 0, stop_tokens: Tuple[DummyToken | TokenType] = ...):
    """ "fn" <fn-name> "("<kwargs>")" ("->" <returned-type>)? <code-body>"""

    tokens = extract_tokens(tokens, i, stop_tokens)

    if len(tokens) != 4:
        return False

    if not _is_kw(tokens[0], 'fn') or not _is_name(tokens[1]) \
            or tokens[2].type != TokenTypes.PARENTHESIS or not _is_code_body(tokens[3]):
        return False

    if not tokens[2].value:
        return True

    return False


def _generate_fn_init(): isnotfinished()
