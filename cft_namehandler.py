from py_utils import isnotfinished
from json import dumps, loads
from copy import deepcopy


def get_value_returned_type(obj: dict):
    return obj['returned-type'] if obj['returned-type'] != '$self' else obj['type']


NAME_HANDLER_TYPES = ['$mod', '$local-space']


class NameHandler:
    def __init__(self):
        self._core_namespace = {
            '$main': {
                'type': '$mod',
                'name': '$main',
                'value': {}
            }
        }
        self._core_namespace['$main']['*parent'] = self._core_namespace

        self._current_obj = self._core_namespace['$main']
        self._accessible_names = {}

    def has_localname(self, name: str):
        return name in self._current_obj['value']

    def has_globalname(self, name: str, exclude_local=False):
        return name in self._accessible_names and not (exclude_local and self.has_localname(name))

    def force_set_name(self, name: str, **attrs):
        attrs.update({
            '*parent': self._current_obj,
            'name': name
        })

        if name not in self._accessible_names:
            self._current_obj['value'][name] = {}

        self._current_obj['value'][name].update(attrs)
        self._accessible_names[name] = self._current_obj['value'][name]

    def set_name(self, name: str, _type: str, value: dict, **attrs):
        if _type is not None and value is not None \
                and (get_value_returned_type(value) != _type and get_value_returned_type(value) not in '$undefined') \
                or \
                (self.has_globalname(name) and self._accessible_names[name]['type'] != get_value_returned_type(value)):
            return False

        self.force_set_name(name, type=_type, value=value, **attrs)

        return True

    def init_new_localspace(self):
        self.force_set_name('$local-space', type='$local-space', value={})
        self._current_obj = self._current_obj['value']['$local-space']

    def deinit_current_localspace(self):
        name = self._current_obj['name']
        self._current_obj = self._current_obj['*parent']
        del self._current_obj['value'][name]
        del self._accessible_names[name]

    def to_json(self) -> str:
        def remove_parent(_dict: dict):
            if '*parent' in _dict:
                del _dict['*parent']

            if _dict['type'] in NAME_HANDLER_TYPES and 'value' in _dict:
                for name in _dict['value']:
                    remove_parent(_dict['value'][name])

        copy = deepcopy(self._core_namespace)

        for name in copy:
            remove_parent(copy[name])

        return dumps(copy)

    def from_json(self, s: str):
        isnotfinished()

        def add_parent(_dict: dict, parent: dict):
            _dict['*parent'] = parent

            if _dict['type'] in NAME_HANDLER_TYPES and 'value' in _dict:
                for name in _dict['value']:
                    add_parent(_dict['value'][name], _dict)

        new = loads(s)

        for name in new:
            add_parent(new[name], new)

        self._core_namespace = new


__all__ = (
    'NameHandler',
    'get_value_returned_type'
)


if __name__ == '__main__':
    namehandler = NameHandler()
    namehandler.set_name('test', '$test', {'returned-type': '$test'})
    print(namehandler.to_json())
    namehandler.init_new_localspace()
    namehandler.set_name('t', '$t', {'returned-type': '$t'})
    print(namehandler.to_json())
    namehandler.deinit_current_localspace()
    print(namehandler.to_json())
