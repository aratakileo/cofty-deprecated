from lexermod.cft_token import TokenTypes
from re import compile


regex_specifications = [
    (TokenTypes.COMMENT, r'--.*'),
    (TokenTypes.QUOTATION_MARK, r'[rRcC]?[\'"]'),
    (TokenTypes.NAME, r'(?!\d+)[A-Za-zА-Яа-я\d_]+'),
    (TokenTypes.NUMBER, r'(?!_+)-?(?:0(?:'
                        r'[xX][\dA-Fa-f_]+'                      # HEX number
                        r'|'
                        r'[bB][01_]+'                            # binary number
                        r'|'
                        r'[oO][0-7_]+'                           # octo number
                        r')|'
                        r'[\d_]*\.?[\d_]*[eE][+-]?(?!_+)[\d_]+'  # exponent number postfix
                        r'|'
                        r'[\d_]*\.(?!_+)[\d_]*'                  # decimal number
                        r'|'
                        r'[\d_]+'                                # integer number
                        r')(?:@(?:'
                        r'f(?:32|64)'                            # explicit typing for float number
                        r'|'
                        r'(?:i|u)(?:8|16|32|64|128)'             # explicit typing for integer and unsigned number
                        r'))?'),
    (
        TokenTypes.OP,
        r'->|~>|!|!!|\?|@|,|\.|::|:|\(|\)|\[|\]|\{|\}|\$'         # not user operators (non-overloadable)
        r'|'
        r'~|%|\^|&|\||\-|\+|\*\*|\*|//|/|<=>|>=|<=|=>|>|<|==|='   # user operators (overloadable)
    ),
    (TokenTypes.NEWLINE, r'\n'),
    (TokenTypes.SKIP, r'\s+'),
    (TokenTypes.MISMATCH, r'.'),
]
regex = compile('|'.join(['(?P<%s>%s)' % (pair[0].name, pair[1]) for pair in regex_specifications]))


__all__ = (
    'regex',
)

if __name__ == '__main__':
    print(regex.pattern)
