from os.path import abspath


def _segment_to_str(segment):
    if len(segment) == 0:
        return '', None

    res = (' ' * 3)

    if segment[-1]['type'] in (ErrorsHandler.ERROR, ErrorsHandler.WARNING):
        res += f'File \"{abspath(segment[1])}\", line {segment[2].start[0]}'
    elif segment[-1]['type'] == ErrorsHandler.HELP:
        res += '\033[36m==help:\033[0m '
    elif segment[-1]['type'] == ErrorsHandler.NOTE:
        res += '\033[36m==note:\033[0m '

    body = ''

    if 'correct' in segment[-1] and segment[-1]['correct'] is not None:
        _start = segment[2].line[:segment[2].start[1]]
        _end = segment[2].line[segment[2].end[1]:]

        body = _start + segment[-1]['correct'] + _end
    elif 'correct' not in segment[-1]:
        body = segment[2].line

    if 'correct' not in segment[-1] or ('correct' in segment[-1] and segment[-1]['correct'] is not None):
        body = (' ' * 5) + body.strip() + '\n'

    if isinstance(segment[0], str):
        _fill = 1

        if 'fill' in segment[-1] and segment[-1]['fill']:
            _fill = (segment[2].end[1] - segment[2].start[1]) if 'correct' not in segment[-1] \
                else len(segment[-1]['correct'])

            if 'offset' in segment[-1]:
                _fill -= segment[-1]['offset']

            if 'backspace' in segment[-1]:
                _fill -= segment[-1]['backspace']

        if 'correct' not in segment[-1] or ('correct' in segment[-1] and segment[-1]['correct'] is not None):
            body += (
                (' ' * (
                        5
                        + segment[2].start[1]
                        + (0 if 'offset' not in segment[-1] else segment[-1]['offset'])
                ))
                + '^' * _fill)

            body = '\n' + body

        if segment[-1]['type'] in (ErrorsHandler.ERROR, ErrorsHandler.WARNING):
            res += body + '\n' + (' ' * 3) + segment[0]
        else:
            res += segment[0] + body

        return res, segment[-1]

    returned = _segment_to_str(segment[0])

    if returned[1] is None:
        return '', None

    return res + returned[0], returned[1]


class ErrorsHandler:
    ERROR = 0
    WARNING = 1
    NOTE = 2
    HELP = 3

    def __init__(self):
        self._data = [
            0,
            0,
            [[]]
        ]
        self._current_segment = self._data[-1][-1]

    def __str__(self):
        res = ''

        i = 0
        for chain in self._data[-1]:
            returned = _segment_to_str(chain)

            if returned[1] is None: continue

            if returned[1]['type'] == ErrorsHandler.ERROR:
                i += 1
                res += '%i.\033[38;2;254;106;102mERROR' % i
            elif returned[1]['type'] == ErrorsHandler.WARNING:
                i += 1
                res += '%i.\033[93mWARNING' % i

            res += '\033[0m'
            res += '' if 'errcode' not in returned[1] else '[E%04i]' % returned[1]["errcode"]

            if returned[1]['type'] in (ErrorsHandler.ERROR, ErrorsHandler.WARNING):
                res += ':\n'

            res += returned[0]
            res += '\n'

        if len(res) == 0:
            return 'No errors'

        if bool(self._data[0]):
            res += f'\033[38;2;254;106;102merror:\033[0m aborting due to {(str(self._data[0]) + " ") if self._data[0] > 1 else ""}previous error'

            if bool(self._data[1]):
                res += '; '
        elif bool(self._data[1]):
            res += '\033[93mwarning:\033[0m '

        if bool(self._data[1]):
            res += f'{(str(self._data[1]) + " warnings") if self._data[1] > 1 else "warning"} emitted'

        return res

    def has_errors(self):
        return bool(self._data[0])

    def has_warnings(self):
        return bool(self._data[1])

    def push_segment(self, path: str, token):
        self._current_segment.append([])
        self._current_segment.append(path)
        self._current_segment.append(token)
        self._current_segment = self._current_segment[0]

    def final_push_segment(self, path: str, reason: str, token, **kwargs):
        if 'type' not in kwargs:
            kwargs['type'] = ErrorsHandler.ERROR

        self._current_segment.append(reason)
        self._current_segment.append(path)
        self._current_segment.append(token)
        self._current_segment.append(kwargs)
        self._current_segment = []
        self._data[-1].append(self._current_segment)

        if ErrorsHandler.ERROR <= kwargs['type'] <= ErrorsHandler.WARNING:
            self._data[int(kwargs['type'] != ErrorsHandler.ERROR)] += 1

    def pop_chain(self):
        if self._data[-1][-1]:
            del self._data[-1][-1]

        if not self._data[-1]:
            self._data[-1].append([])

        self._current_segment = self._data[-1][-1]

    def clear(self):
        self._data[-1] = [[]]
        self._current_segment = self._data[-1][-1]

    def print(self, clear=True):
        print(self)

        if clear:
            self.clear()
