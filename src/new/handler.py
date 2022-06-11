from error_handler import ErrorHandler
from json import dumps, loads
from os.path import abspath


class Handler:
    error_handler: ErrorHandler

    data = {
        '$lib': {},
        '$namespace': {
            '$': {
                'name': '$',
                'value': {}
            }
        }
    }
    current_namespace_obj = data['$namespace']['$']
    current_file_obj = current_namespace_obj

    def __init__(self, doc: str, path: str, error_handler: ErrorHandler):
        self.current_namespace_obj['path'] = abspath(path)
        self.current_namespace_obj['doc'] = doc
        self.error_handler = error_handler

    @property
    def current_path(self):
        return self.current_file_obj['path']

    @property
    def current_doc(self):
        return self.current_file_obj['doc']

    def to_json(self):
        return dumps(self.data)

    def from_json(self, s: str):
        self.data = loads(s)


__all__ = (
    'Handler',
)
