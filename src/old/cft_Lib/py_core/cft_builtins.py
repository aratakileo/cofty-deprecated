from parsemod.cft_syntaxtree_values import None_type, str_type


_cft_print_fn = {
    'type': 'fn',
    'name': 'print',
    'compile-name': '_cft_print',
    'args': {
        's': {
            'type': str_type,
            'value': {
                'type': str_type,
                'value': '',
                'returned-type': '$self'
            },
            'mut': True,
            'name': 's'
        }
    },
    'value': {},
    'returned-type': None_type,
    'positional-args': 0,
    'max-args': 2
}


cft_all = {
    _cft_print_fn['name']: _cft_print_fn
}


def define(namehandler: 'NameHandler'):
    global cft_all

    _cft_all = cft_all.copy()

    for name in _cft_all:
        _cft_all[name]['*parent'] = namehandler.abs_current_obj

    namehandler.abs_current_obj['value'].update(_cft_all)
    namehandler._accessible_names.update(_cft_all)
