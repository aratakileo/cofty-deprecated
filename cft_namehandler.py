from cft_Lib.py_core import cft_builtins
from py_utils import isnotfinished
from json import dumps, loads
from copy import deepcopy


def get_value_returned_type(obj: dict):
    return obj['returned-type'] if obj['returned-type'] != '$self' else obj['type']


NAME_HANDLER_TYPES = ['$mod', '$local-space', '$handler', 'fn']


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

        self.current_obj = self._core_namespace['$main']
        self._accessible_names = {}
        self._used_compile_names = set()
        self._compile_names_prefix = ''

        cft_builtins.define(self)

    @property
    def abs_current_obj(self):
        if isinstance(self.current_obj['value'], list):
            return self.current_obj['value'][-1]

        return self.current_obj

    @property
    def base_current_obj(self):
        current = self.abs_current_obj

        while current['type'] == NAME_HANDLER_TYPES[1]:
            current = current['*parent']

        return current

    def has_localname(self, name: str):
        return name in self.abs_current_obj['value']

    def has_globalname(self, name: str, exclude_local=False):
        return name in self._accessible_names and not (exclude_local and self.has_localname(name))

    def is_overloaded(self, name: str, only_local=False):
        if only_local:
            return self.has_localname(name) and isinstance(self.abs_current_obj['value'][name]['value'], list)

        return self.has_globalname(name) and isinstance(self._accessible_names[name]['value'], list)

    def isinstance(self, name: str, _type: str = None, returned_type: str = None):
        _body = self.get_current_body(name)
        return (_type is None or _body['type'] == _type) and (
                returned_type is None or ('returned-type' in _body['value'] and get_value_returned_type(_body['value']))
        )

    def get_current_body(self, name: str):
        if self.is_overloaded(name):
            return self._accessible_names[name]['value'][-1]

        return self._accessible_names[name]

    def get_compile_name(self, name: str):
        prefix = self._compile_names_prefix + '_'

        if prefix == '_':
            prefix = ''

        compile_name = f'_cft_{prefix}{name}'

        i = 0
        while compile_name in self._used_compile_names:
            compile_name = f'_cft_{prefix}{name}{i}'
            i += 1

        self._used_compile_names.add(compile_name)

        return compile_name

    def force_set_name(self, name: str, **attrs):
        if isinstance(attrs['value'], list):
            for val in attrs['value']:
                val.update({
                    'name': name,
                    '*parent': self.current_obj
                })
        else:
            attrs.update({
                'name': name,
                '*parent': self.current_obj
            })

            if not self.has_localname(name) and 'compile-name' not in attrs:
                attrs['compile-name'] = self.get_compile_name(name)

        if name not in self.abs_current_obj['value']:
            self.abs_current_obj['value'][name] = {}

        self.abs_current_obj['value'][name].update(attrs)

        if self.has_globalname(name):
            temp = [self.abs_current_obj['value'][name]]

            if isinstance(self.abs_current_obj['value'][name]['value'], list):
                temp = self.abs_current_obj['value'][name]['value']

            if self.is_overloaded(name):
                self._accessible_names[name]['value'] = self._accessible_names[name]['value'] + temp
            else:
                self._accessible_names[name] = {
                    'type': NAME_HANDLER_TYPES[2],
                    'value': [self._accessible_names[name]] + temp
                }

            return

        self._accessible_names[name] = self.abs_current_obj['value'][name]

    def overload_name(self, name: str, _type: str, value: dict, **attrs):
        new_obj = {
            'type': _type,
            'value': value,
            'name': name,
            'compile-name': self.get_compile_name(name),
            '*parent': self.current_obj,
            **attrs
        }

        if self.has_localname(name):
            if self.is_overloaded(name, True):
                self.abs_current_obj['value'][name]['value'].append(new_obj)
            else:
                temp = self.abs_current_obj['value'][name]

                del self.abs_current_obj['value'][name]

                self.force_set_name(name, type=NAME_HANDLER_TYPES[2], value=[temp, new_obj])

            return

        self.force_set_name(**new_obj)

    def use_localspace(self, name: str):
        self.current_obj = self.get_current_body(name)

        if not name.startswith('$'):
            self._compile_names_prefix += ('_' if self._compile_names_prefix else '') + name

        for name in self.abs_current_obj['value']:
            obj = self.abs_current_obj['value'][name]

            if name in self._accessible_names:
                if self.is_overloaded(name):
                    if self._accessible_names[name]['value'][-1] != obj:
                        self._accessible_names[name]['value'].append(obj)
                elif self._accessible_names[name] != obj:
                    temp = self._accessible_names[name]
                    self._accessible_names[name] = {
                        'type': NAME_HANDLER_TYPES[2],
                        'value': [temp, obj]
                    }
            else:
                self._accessible_names[name] = obj

    def init_new_localspace(self):
        self.overload_name(NAME_HANDLER_TYPES[1], NAME_HANDLER_TYPES[1], {})

        self.use_localspace(NAME_HANDLER_TYPES[1])

    def leave_current_localspace(self):
        for name in self.abs_current_obj['value']:
            if self.is_overloaded(name):
                if self.is_overloaded(name, True):
                    for obj in self.abs_current_obj['value'][name]['value']:
                        self._accessible_names[name]['value'].remove(obj)
                else:
                    self._accessible_names[name]['value'].remove(self.abs_current_obj['value'][name])
            else:
                del self._accessible_names[name]

        name = self.abs_current_obj['name']
        if not name.startswith('$'):
            self._compile_names_prefix = self._compile_names_prefix[
                                         :-len(name) + (1 if self._compile_names_prefix == name else 0)
                                         ]
        self.current_obj = self.abs_current_obj['*parent']

    # DO NOT USE THIS METHODS
    def to_json(self) -> str:
        def remove_parent(_dict: dict):
            if '*parent' in _dict:
                del _dict['*parent']

            if _dict['type'] in NAME_HANDLER_TYPES and 'value' in _dict:
                if isinstance(_dict['value'], list):
                    for obj in _dict['value']:
                        remove_parent(obj)
                else:
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
    namehandler.leave_current_localspace()
    print(namehandler.to_json())
