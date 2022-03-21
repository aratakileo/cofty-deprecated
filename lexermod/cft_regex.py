from lexermod.cft_token import TokenTypes
from re import compile


regex_specifications = [
    (TokenTypes.COMMENT, r'--.*'),
    (TokenTypes.QUOTATION_MARK, r'[rRcC]?[\'"]'),
    (TokenTypes.NAME, r'(?!_*\d+)[A-Za-z\d_]+'),
    (TokenTypes.NUMBER, r'(?:0(?:[xX][\dA-Fa-f_]+|[bB][01_]+|[oO][0-7_]+)|(?:'
                        r'\d+\.\d+|\d+)[eE][+-]?\d+'
                        r'|[\d_]*\.[\d_]+'
                        r'|[\d_]+\.[\d_]*'
                        r'|[\d_]+'
                        r')(?:@(?:f(?:32|64)|(?:i|u)(?:8|16|32|64|128)))?'),
    (TokenTypes.DOT, r'\.'),
    (TokenTypes.OP, r'->|!|\?|@|\$|~|%|\^|&|\-|\+|\*\*|\*|//|/|\||<=>|>=|<=|=>|>|<|==|=|,|:|\(|\)|\[|\]|\{|\}'),
    (TokenTypes.NEWLINE, r'\n'),
    (TokenTypes.SKIP, r'\s+'),
    (TokenTypes.MISMATCH, r'.'),
]
regex = compile('|'.join(['(?P<%s>%s)' % (pair[0].name, pair[1]) for pair in regex_specifications]))


__all__ = (
    'regex_specifications',
    'regex'
)
