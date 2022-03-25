from lexermod.cft_token import TokenTypes
from re import compile


regex_specifications = [
    (TokenTypes.COMMENT, r'--.*'),
    (TokenTypes.QUOTATION_MARK, r'[rRcC]?[\'"]'),
    (TokenTypes.NAME, r'(?!_*\d+)[A-Za-z\d_]+'),
    (TokenTypes.NUMBER, r'(?:0(?:'
                        r'[xX][\dA-Fa-f_]+'           # HEX number
                        r'|'
                        r'[bB][01_]+'                 # binary number
                        r'|'
                        r'[oO][0-7_]+'                # octo number
                        r')|(?:'
                        r'\d+\.\d+|\d+'               # exponent number prefix
                        r')'
                        r'[eE][+-]?\d+'               # exponent number postfix
                        r'|'
                        r'[\d_]*\.[\d_]+'             # decimal number (without prefix)
                        r'|'
                        r'[\d_]+\.[\d_]*'             # decimal number (without postfix)
                        r'|'
                        r'[\d_]+'                     # integer number
                        r')(?:@(?:'
                        r'f(?:32|64)'                 # explicit typing for float number
                        r'|'
                        r'(?:i|u)(?:8|16|32|64|128)'  # explicit typing for integer and unsigned number
                        r'))?'),
    (
        TokenTypes.OP,
        r'->|~>|!|!!|\?|@|,|\.|::|:|\(|\)|\[|\]|\{|\}|\$'        # not user operators (non-overloadable)
        r'|'
        r'~|%|\^|&|\||\-|\+|\*\*|\*|//|/|<=>|>=|<=|=>|>|<|==|='  # user operators (overloadable)
    ),
    (TokenTypes.NEWLINE, r'\n'),
    (TokenTypes.SKIP, r'\s+'),
    (TokenTypes.MISMATCH, r'.'),
]
regex = compile('|'.join(['(?P<%s>%s)' % (pair[0].name, pair[1]) for pair in regex_specifications]))


__all__ = (
    'regex_specifications',
    'regex'
)
