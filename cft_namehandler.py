from cft_Lib.py_core import cft_builtins
from py_utils import isnotfinished
from json import dumps, loads
from copy import deepcopy


def get_value_returned_type(obj: dict):
    return obj['returned-type'] if obj['returned-type'] != '$self' else obj['type']


def get_local_name(composed_name: list | str):
    if isinstance(composed_name, str):
        return composed_name

    return composed_name[-1]


def is_local_name(composed_name: list | str):
    return isinstance(composed_name, str) or len(composed_name) == 1


def get_abs_composed_name(name_obj: dict):
    composed_name = []

    while name_obj['name'] != '$':
        composed_name.insert(0, name_obj['name'])
        name_obj = name_obj['*parent']

    return ['$'] + composed_name


NAME_HANDLER_TYPES = ['$mod', '$local-space', '$handler', 'fn', '$struct']


class NameHandler:
    def __init__(self):
        self._core_namespace = {
            'type': '$mod',
            'name': '$',
            'value': {}
        }

        self.current_obj = self._core_namespace
        self._accessible_names = {}
        self._used_compile_names = set()
        self._compile_names_prefix = ''
        self._obj_attributes_preset = {}

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

    def get_name_obj(self, composed_name: list | str, from_obj=...):
        """:param from_obj self.abs_current_obj"""
        if from_obj is ...:
            from_obj = self.abs_current_obj

        if from_obj is self._accessible_names:
            from_obj = {'value': from_obj}

        if isinstance(composed_name, str):
            composed_name = [composed_name]
        elif composed_name[0] == '$':
            return self.get_name_obj(composed_name[1:], self._core_namespace)

        for name in composed_name:
            if 'value' not in from_obj or from_obj['value'] is None or name not in from_obj['value']:
                return None

            from_obj = from_obj['value'][name]

        return from_obj

    def set_name_obj(self, composed_name: list | str, name_obj: dict, from_obj=...):
        """:param from_obj self.abs_current_obj"""
        if from_obj is ...:
            from_obj = self.abs_current_obj

        if from_obj is self._accessible_names:
            from_obj = {'value': from_obj}

        if isinstance(composed_name, str):
            composed_name = [composed_name]
        elif composed_name[0] == '$':
            return self.set_name_obj(composed_name[1:], name_obj, self._core_namespace)

        for name in composed_name[:-1]:
            if 'value' not in from_obj or from_obj['value'] is None or name not in from_obj['value']:
                return False

            from_obj = from_obj['value'][name]

        if 'value' not in from_obj or from_obj['value'] is None:
            return False

        from_obj['value'][composed_name[-1]] = name_obj

        return True

    def has_localname(self, composed_name: list | str):
        return self.get_name_obj(composed_name) is not None

    def has_globalname(self, composed_name: list | str, exclude_local=False):
        return self.get_name_obj(composed_name, self._accessible_names) is not None \
               and not (exclude_local and self.has_localname(composed_name))

    def is_overloaded(self, composed_name: list | str, only_local=False):
        if only_local:
            return self.has_localname(composed_name) and isinstance(self.get_name_obj(composed_name)['value'], list)

        return self.has_globalname(composed_name) and isinstance(
            self.get_name_obj(composed_name, self._accessible_names)['value'],
            list
        )

    def isinstance(self, composed_name: list | str, _type: tuple | list | str = None, returned_type: str = None):
        if isinstance(_type, tuple | list):
            for t in _type:
                if self.isinstance(composed_name, t, returned_type):
                    return True

            return False

        _body = self.get_current_body(composed_name)
        return (_type is None or _body['type'] == _type) and (
                returned_type is None or ('returned-type' in _body['value'] and get_value_returned_type(_body['value']))
        )

    def get_current_body(self, composed_name: str):
        if self.is_overloaded(composed_name):
            return self.get_name_obj(composed_name, self._accessible_names)['value'][-1]

        return self.get_name_obj(composed_name, self._accessible_names)

    def get_compile_name(self, composed_name: list | str):
        prefix = self._compile_names_prefix + '_'

        if prefix == '_':
            prefix = ''

        if isinstance(composed_name, str):
            composed_name = [composed_name]

        composed_name = '_'.join(composed_name)

        compile_name = f'_cft_{prefix}{composed_name}'

        i = 0
        while compile_name in self._used_compile_names:
            compile_name = f'_cft_{prefix}{composed_name}{i}'
            i += 1

        self._used_compile_names.add(compile_name)

        return compile_name

    def adjust_attrs(self, obj: dict):
        obj.update(self._obj_attributes_preset)
        self._obj_attributes_preset = {}

        if 'compile-name' not in obj:
            obj['compile-name'] = self.get_compile_name(obj['name'])

    def force_set_name(self, composed_name: list | str, **attrs):
        if isinstance(attrs['value'], list):
            for val in attrs['value']:
                if 'name' not in val:
                    val['name'] = get_local_name(composed_name)

                if '*parent' not in val:
                    val['*parent'] = self.current_obj
        else:
            if 'name' not in attrs:
                attrs['name'] = get_local_name(composed_name)

            if '*parent' not in attrs:
                attrs['*parent'] = self.current_obj

            if not self.has_localname(composed_name):
                self.adjust_attrs(attrs)

        if not self.has_localname(composed_name):
            self.set_name_obj(composed_name, {})

        name_obj = self.get_name_obj(composed_name)

        name_obj.update(attrs)

        if self.has_globalname(composed_name) and is_local_name(composed_name):
            temp = [name_obj]

            if isinstance(name_obj['value'], list):
                temp = name_obj['value']

            if self.is_overloaded(composed_name):
                self.get_name_obj(composed_name, self._accessible_names)['value'] += temp
            else:
                self.set_name_obj(composed_name, {
                    'type': NAME_HANDLER_TYPES[2],
                    'value': [self.get_name_obj(composed_name, self._accessible_names)] + temp
                }, from_obj=self._accessible_names)
            return

        self.set_name_obj(composed_name, name_obj, from_obj=self._accessible_names)

    def overload_name(self, name: str, _type: str, value: dict, **attrs):
        new_obj = {
            'type': _type,
            'value': value,
            'name': name,
            '*parent': self.current_obj,
            **attrs
        }

        self.adjust_attrs(new_obj)

        if self.has_localname(name):
            if self.is_overloaded(name, True):
                self.abs_current_obj['value'][name]['value'].append(new_obj)
            else:
                temp = self.abs_current_obj['value'][name]

                del self.abs_current_obj['value'][name]

                self.force_set_name(name, type=NAME_HANDLER_TYPES[2], value=[temp, new_obj])

            return

        self.force_set_name(**new_obj)

    def use_names_from_namespace(self, composed_name: list | str):
        current_obj = self.get_name_obj(composed_name)['value']

        if '$used-names' not in self.abs_current_obj:
            self.abs_current_obj['$used-names'] = []

        for name in current_obj:
            obj = current_obj[name]
            self.abs_current_obj['$used-names'].append(name)

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

        if self.has_localname('$used-names'):
            for name in self.get_name_obj('$used-names'):
                if self.is_overloaded(name):
                    self._accessible_names[name]['value'].remove(self.abs_current_obj['value'][name])
                else:
                    del self._accessible_names[name]

        name = self.abs_current_obj['name']
        if not name.startswith('$'):
            self._compile_names_prefix = self._compile_names_prefix[
                                         :-len(name) - (self._compile_names_prefix != name)
                                         ]
        self.current_obj = self.abs_current_obj['*parent']

    # DO NOT USE THIS METHODS
    def to_json(self) -> str:
        def remove_parent(_dict: dict):
            if '*parent' in _dict:
                del _dict['*parent']

            if 'value' in _dict and _dict['value'] is not None and (_dict['type'] in NAME_HANDLER_TYPES or 'type' not in _dict['value']):
                if isinstance(_dict['value'], list):
                    for obj in _dict['value']:
                        remove_parent(obj)
                else:
                    for name in _dict['value']:
                        remove_parent(_dict['value'][name])

        copy = deepcopy(self._core_namespace)

        for name in copy['value']:
            remove_parent(copy['value'][name])

        return dumps(copy)

    def accessible_to_json(self) -> str:
        """Debug method"""

        def remove_parent(_dict: dict):
            if '*parent' in _dict:
                del _dict['*parent']

            if 'value' in _dict and _dict['value'] is not None and (_dict['type'] in NAME_HANDLER_TYPES or 'type' not in _dict['value']):
                if isinstance(_dict['value'], list):
                    for obj in _dict['value']:
                        remove_parent(obj)
                else:
                    for name in _dict['value']:
                        remove_parent(_dict['value'][name])

        copy = deepcopy(self._accessible_names)

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

    def copy(self):
        return deepcopy(self)


__all__ = (
    'NameHandler',
    'get_value_returned_type',
    'get_local_name',
    'get_abs_composed_name'
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
