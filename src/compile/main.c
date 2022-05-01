#include "${standard_lib_path}/c_core/cft_builtins.h"


${global_body}


void main() {
    _cft_INIT_OUTPUT;
    ${main_body}
}

{
    'const': False,
    'type': ['$', 'Earth', 'SubEarth', 'People'],
    'value': {
        'name': {
            'type': 'str',
            'value': {
                '$constant-expr': True,
                'returned-type': '$self',
                'type': 'str',
                'value':
                'Lucy'
            },
            'name': 'name',
            '*parent': {...},
            'compile-name': '_cft_Earth_SubEarth_People_name'
        },
        'age': {
            'type': 'i8',
            'value': {
                '$constant-expr': True,
                'returned-type': '$self',
                'type': 'i8',
                'value': '16'
            },
            'name': 'age',
            '*parent': {...},
            'compile-name': '_cft_Earth_SubEarth_People_age'
        }
    },
    'mut': False
}

