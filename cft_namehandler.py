def get_value_returned_type(obj: dict):
    return obj['returned-type'] if obj['returned-type'] != '$self' else obj['type']


class NameHandler:
    def __init__(self):
        self._core_namespace = {
            '$main': {}
        }
        self._core_namespace['$main']['*parent'] = self._core_namespace

        self._current_namespace = self._core_namespace['$main']
        self._accessible_names = {}

    def has_localname(self, name: str):
        return name in self._current_namespace

    def has_globalname(self, name: str, only_global=False):
        return name in self._accessible_names and not (only_global and self.has_localname(name))

    def force_set_name(self, name: str, **attrs):
        attrs['*parent'] = self._current_namespace

        if name not in self._current_namespace:
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


__all__ = (
    'NameHandler',
    'get_value_returned_type'
)
