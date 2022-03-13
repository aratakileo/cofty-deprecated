from py_utils import isnotfinished
from json import dumps, loads
from copy import deepcopy


def get_value_returned_type(obj: dict):
    return obj['returned-type'] if obj['returned-type'] != '$self' else obj['type']


NAME_HANDLER_TYPES = ['$mod', '$local-space', '$handler']


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

    @property
    def _abs_current_obj(self):
        if isinstance(self._current_obj['value'], list):
            return self._current_obj['value'][-1]

        return self._current_obj

    def has_localname(self, name: str):
        return name in self._abs_current_obj['value']

    def has_globalname(self, name: str, exclude_local=False):
        return name in self._accessible_names and not (exclude_local and self.has_localname(name))

    def is_overloaded(self, name: str, only_local=False):
        if only_local:
            return self.has_localname(name) and isinstance(self._abs_current_obj['value'][name]['value'], list)

        return self.has_globalname(name) and isinstance(self._accessible_names[name]['value'], list)

    def get_current_name_body(self, name: str):
        if self.is_overloaded(name):
            return self._accessible_names[name]['value'][-1]

        return self._accessible_names[name]

    def force_set_name(self, name: str, **attrs):
        if isinstance(attrs['value'], list):
            for val in attrs['value']:
                val.update({
                    'name': name,
                    '*parent': self._current_obj
                })
        else:
            attrs.update({
                'name': name,
                '*parent': self._current_obj
            })

        if name not in self._abs_current_obj['value']:
            self._abs_current_obj['value'][name] = {}

        self._abs_current_obj['value'][name].update(attrs)

        if name in self._accessible_names:
            temp = [self._abs_current_obj['value'][name]]

            if isinstance(self._abs_current_obj['value'][name]['value'], list):
                temp = self._abs_current_obj['value'][name]['value']

            if self.is_overloaded(name):
                self._accessible_names[name]['value'] = self._accessible_names[name]['value'] + temp
            else:
                self._accessible_names[name] = {
                    'type': '$handler',
                    'value': [self._accessible_names[name]] + temp
                }

            return

        self._accessible_names[name] = self._abs_current_obj['value'][name]

    def set_name(self, name: str, _type: str, value: dict, **attrs):
        if _type is not None and value is not None \
                and (get_value_returned_type(value) != _type and get_value_returned_type(value) not in '$undefined') \
                or \
                (self.has_globalname(name) and self._accessible_names[name]['type'] != get_value_returned_type(value)):
            return False

        self.force_set_name(name, type=_type, value=value, **attrs)

        return True

    def overload_name(self, name: str, _type: str, value: dict, **attrs):
        new_obj = {'type': _type, 'value': value, **attrs}
        piece = {'name': name, '*parent': self._current_obj}

        if self.has_localname(name):
            if self.is_overloaded(name, True):
                self._abs_current_obj['value'][name].append(new_obj | piece)
            else:
                temp = self._abs_current_obj['value'][name]

                del self._abs_current_obj['value'][name]

                self.force_set_name(name, type='$handler', value=[temp, new_obj])

            return

        self.force_set_name(**(new_obj | piece))

    def init_new_localspace(self):
        self.overload_name(NAME_HANDLER_TYPES[1], NAME_HANDLER_TYPES[1], {})
        self._current_obj = self._abs_current_obj['value'][NAME_HANDLER_TYPES[1]]

        for name in self._abs_current_obj['value']:
            obj = self._abs_current_obj['value'][name]

            if name in self._accessible_names:
                if self.is_overloaded(name):
                    if self._accessible_names[name]['value'][-1] != obj:
                        self._accessible_names[name]['value'].append(obj)
                elif self._accessible_names[name] != obj:
                    temp = self._accessible_names[name]
                    self._accessible_names[name] = {
                        'type': '$handler',
                        'value': [temp, obj]
                    }
            else:
                self._accessible_names[name] = obj

    def leave_current_localspace(self):
        for name in self._abs_current_obj['value']:
            if self.is_overloaded(name):
                if self.is_overloaded(name, True):
                    for obj in self._abs_current_obj['value'][name]['value']:
                        self._accessible_names[name]['value'].remove(obj)
                else:
                    self._accessible_names[name]['value'].remove(self._abs_current_obj['value'][name])
            else:
                del self._accessible_names[name]
        self._current_obj = self._abs_current_obj['*parent']

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
