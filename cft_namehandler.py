from json import dumps, loads


def get_value_returned_type(obj: dict):
    return obj['returned-type'] if obj['returned-type'] != '$self' else obj['type']


NAME_HANDLER_TYPES = ['$mod']


class NameHandler:
    def __init__(self):
        self._core_namespace = {
            '$main': {
                'type': '$mod',
                'value': {}
            }
        }
        self._core_namespace['$main']['*parent'] = self._core_namespace

        self._current_namespace = self._core_namespace['$main']['value']
        self._accessible_names = {}

    def has_localname(self, name: str):
        return name in self._current_namespace

    def has_globalname(self, name: str, only_global=False):
        return name in self._accessible_names and not (only_global and self.has_localname(name))

    def force_set_name(self, name: str, **attrs):
        attrs['*parent'] = self._current_namespace

        if name not in self._accessible_names:
            self._current_namespace[name] = {}

        self._current_namespace[name].update(attrs)
        self._accessible_names[name] = self._current_namespace[name]

    def set_name(self, name: str, _type: str, value: dict, **attrs):
        if (get_value_returned_type(value) != _type and get_value_returned_type(value) not in '$undefined') \
                or \
                (self.has_globalname(name) and self._accessible_names[name]['type'] != get_value_returned_type(value)):
            return False

        self.force_set_name(name, type=_type, value=value, **attrs)

        return True

    def to_json(self) -> str:
        def remove_parent(_dict: dict):
            if '*parent' in _dict:
                del _dict['*parent']

            if _dict['type'] in NAME_HANDLER_TYPES and 'value' in _dict:
                for name in _dict['value']:
                    remove_parent(_dict['value'][name])

        copy = self._core_namespace.copy()

        for name in copy:
            remove_parent(copy[name])

        return dumps(copy)

    def from_json(self, s: str):
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
