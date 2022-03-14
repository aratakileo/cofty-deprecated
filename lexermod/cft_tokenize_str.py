from cft_errors_handler import ErrorsHandler
from .cft_token import Token, TokenTypes


def tokenize_str_next(s: str, path: str, token: Token, errors_handler: ErrorsHandler) -> int:
    quotation_type = token.value[-1]
    _s = s[token.start[2] + len(token.value):]
    prefix = token.value[:-1]
    value = token.value
    value_len = 0

    if len(_s) == 0:
        errors_handler.final_push_segment(path, f'SyntaxError: `{quotation_type}` is never closed here', token)
        errors_handler.final_push_segment(
            path,
            f'just insert `{quotation_type}` to the end',
            token,
            type=ErrorsHandler.HELP,
            correct=token.value + quotation_type,
            offset=1
        )
        return 0

    line_i = 0
    neg_i = 0
    i = 0
    while i < len(_s):
        next = None if i == len(_s) - 1 else _s[i + 1]

        if _s[i] in ('\'', '\"'):
            if quotation_type == _s[i]:
                i += 1
                break
            else:
                value += '\\' + _s[i]
                value_len += 1
        elif _s[i] == '\\':
            if next is not None and (
                    next == quotation_type or ('r' not in prefix and next in '\'"rnt')
            ):
                value += _s[i] + next
                i += 1
                value_len += 1
            elif next is not None:
                value += '\\\\' + next
                value_len += 2
                i += 1
            else:
                _token = token.copy()
                _token.start = (token.start[0], token.start[1] + i + 1 - neg_i, token.start[2] + i + 1)
                _token.end = (token.end[0], token.end[1] + i + 1 - neg_i)

                if line_i > 0:
                    _token.line = s.split('\n')[token.start[0] + line_i - 1]

                errors_handler.final_push_segment(path, f'SyntaxError: invalid backslash character', _token)
                errors_handler.final_push_segment(
                    path,
                    f'if you meant to write a backslash, specify it twice `\\\\` or put `r` before the quotes',
                    token,
                    type=ErrorsHandler.HELP,
                    correct=None
                )
        elif _s[i] == '\n':
            neg_i += len(s.split('\n')[token.start[0] + line_i - 1]) + 2
            line_i += 1
            errors_handler.final_push_segment(path, f'SyntaxError: `{quotation_type}` is never closed here', token)
        else:
            value += _s[i]
            value_len += 1

        i += 1

    i -= 1

    if _s[i] != quotation_type:
        token.end = (token.end[0], token.end[1] + i + 1)
        errors_handler.final_push_segment(path, f'SyntaxError: `{quotation_type}` is never closed here', token)
        errors_handler.final_push_segment(
            path,
            f'insert `{quotation_type}` to the end',
            token,
            type=ErrorsHandler.HELP,
            correct=prefix + quotation_type + _s[:i + 1] + quotation_type,
            offset=len(prefix + _s[:i + 1]) + 1
        )
        return 0

    if prefix == 'c' and value_len != 1:
        if value_len == 0:
            errors_handler.final_push_segment(
                path,
                'SyntaxError: empty character literal',
                token,
                offset=2
            )
        else:
            errors_handler.final_push_segment(
                path,
                'SyntaxError: character literal may only contain one codepoint',
                token,
                offset=1,
                fill=True
            )
        errors_handler.final_push_segment(
            path,
            f'if you meant to write a `str` literal, remove `c` before quotes',
            token,
            type=ErrorsHandler.HELP,
            correct=quotation_type + _s[:i + 1],
            fill=True
        )

    token.value = value + quotation_type
    token.type = TokenTypes.STRING
    token.end = (token.end[0], token.end[1] + len(token.value) - len(prefix) - 1)

    return token.start[2] + i + 2 + len(prefix)


__all__ = (
    'tokenize_str_next',
)
