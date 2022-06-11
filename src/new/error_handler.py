from lexermod.cft_token import AnyToken
from enum import Enum


class ErrorHandler:
    class ProblemType(Enum):
        ERROR = 0
        WARNING = 1
        NOTE = 2
        HELP = 3

    def __init__(self):
        self.clean()

    def clean(self):
        self.data = {
            '$problems': [],
            '$statistic': [
                0,  # errors count
                0   # warnings count
            ]
        }

    def has_errors(self):
        return bool(self.data['$statistic'][0])

    def print(self):
        print(self)
        self.clean()

    def push_problem(
            self,
            line: int = None,
            line_str: str = None,
            problem: str = None,
            point: int = None,
            point_off: int = 0,
            fill_point=1,
            type=ProblemType.ERROR
    ):
        self.data['$problems'].append({
            'line': line,
            'type': type,
            'line_str': line_str,
            'problem': problem,
            'point': point,
            'point_off': point_off,
            'fill_point': fill_point
        })

        if type in (ErrorHandler.ProblemType.ERROR, ErrorHandler.ProblemType.WARNING):
            self.data['$statistic'][type.value] += 1

    def push_problem_by_token(self, token: AnyToken, problem: str, doc: str, **kwargs):
        self.push_problem_by_token_data(problem, doc, token.value, token.start, token.end, **kwargs)

    def push_problem_by_token_data(
            self,
            problem: str,
            doc: str,
            token_value: str,
            token_start: tuple,
            token_end: tuple,
            fill_point=False,
            fill_point_right_off=0,
            correct_token_value=None,
            **kwargs
    ):
        line = '\n'.join(doc.split('\n')[token_start[0]: token_end[0] + 1])

        if correct_token_value is not None:
            print(repr(line), token_start, token_end)
            line = line[:token_start[1]]\
                   + correct_token_value\
                   + line[token_start[1] + len(token_value):]
            token_value = correct_token_value
            print(repr(line))

        self.push_problem(
            line=token_start[0],
            line_str=line,
            problem=problem,
            point=token_start[1],
            fill_point=1 - (1 - len(token_value)) * fill_point + fill_point_right_off,
            **kwargs
        )

    def __str__(self):
        errors, warnings = self.data['$statistic']

        if (errors, warnings) == (0, 0):
            return 'No errors, no warnings'

        __return = ''

        i = 1
        for problem in self.data['$problems']:
            problem_type = problem['type']

            if problem_type == ErrorHandler.ProblemType.ERROR:
                __return += '%i.\033[38;2;254;106;102mERROR\033[0m:\n' % i
                i += 1
            elif problem_type == ErrorHandler.ProblemType.WARNING:
                __return += '%i.\033[93mWARNING\033[0m:\n' % i
                i += 1

            if problem['line'] is not None:
                line_str = problem['line_str']

                line = problem['line'] + 1

                border_off = len(str(line))
                __return += ' ' * (2 + border_off) + '|\n'
                __return += ' ' * 2 + f'{line}| ' + line_str.strip() + '\n'
                __return += ' ' * (2 + border_off) + '|\n'

                if problem['point'] is not None:
                    __return += ' ' * (
                            4 + border_off + problem['point'] - len(line_str) + len(line_str.lstrip()) + problem['point_off']
                    )
                    __return += '^' * problem['fill_point'] + '\n'

            if problem_type in (ErrorHandler.ProblemType.ERROR, ErrorHandler.ProblemType.WARNING):
                __return += ' ' * 2 + problem['problem'] + '\n'

            if problem_type == ErrorHandler.ProblemType.HELP:
                __return += '  \033[36m==help:\033[0m '
            elif problem_type == ErrorHandler.ProblemType.NOTE:
                __return += '  \033[38;2;255;165;0m==note:\033[0m '

            if problem_type in (ErrorHandler.ProblemType.HELP, ErrorHandler.ProblemType.NOTE):
                __return += problem['problem'] + '\n'

        if errors:
            __return += f'\033[38;2;254;106;102merror:\033[0m aborting due to '
            __return += (f'{errors} ' if errors > 1 else '') + 'previous error' + ('s' if errors > 1 else '')

        if warnings:
            __return += '; ' if errors else '\033[93mwarning:\033[0m '
            __return += 'warning' if warnings == 1 else f'{warnings} warnings'

        return __return


__all__ = (
    'ErrorHandler',
)
