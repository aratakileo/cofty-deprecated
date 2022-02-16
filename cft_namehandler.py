class NameHandler:
    def __init__(self):
        self._core_namespace = {
            '$main': {}
        }

        self._current_namespace = self._core_namespace['$main']
        self._current_uri = '$main://'
        self._accessible_names = {}

    def _get_uri_metadata(self, uri: str):
        if '://' in uri:
            splitted = uri.split('://')
            splitted = [splitted[0], *splitted[1].split('/')]
        else:
            splitted = self._current_uri.split('://')
            splitted = [splitted[0], *splitted[1].split('/')]

            if uri.startswith('..'):
                splitted = splitted[:-min(uri.count('.') - 1, len(splitted) - 1)]
                print(splitted)

            splitted += uri.lstrip('.').split('/')

        while '' in splitted:
            splitted.remove('')

        return {
            'uri': splitted[0] + '://' + '/'.join(splitted[1:]),
            'splitted': splitted
        }

    def _set_name(self, name: str, type: str, **attrs):
        if self.is_free_name(name):
            self._accessible_names[name] = {
                'type': type,
                'uri': self._current_uri + '/' + name
            }

        attrs['type'] = type
        self._current_namespace[name] = attrs

    def _remove_name(self, name: str):
        if name in self._accessible_names:
            del self._accessible_names[name]

        if name in self._current_namespace:
            del self._current_namespace[name]

    @property
    def current_uri(self):
        return self._current_uri

    def is_free_name(self, name: str):
        """Checking a global name is not existing"""

        return name not in self._accessible_names

    def has_name(self, name: str):
        """Checking for name in local code body"""

        return name in self._current_namespace

    def is_settable_name(self, name: str):
        # for future features

        return self.is_free_name(name) and self.has_name(name)

    def initvar(self, name: str, type: str, value: dict, **attrs):
        self._set_name(name, type, value=value, **attrs)
