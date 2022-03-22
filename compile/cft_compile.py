from os.path import abspath
from cft_namehandler import NameHandler
from re import findall


def compile_num(num: str):
    if len(num) > 1 and num[1] in 'bBxXoO':
        if num[1] in 'bB':
            number_sys = 2
        elif num[1] in 'oO':
            number_sys = 8
        else:
            number_sys = 16

        return str(int(num[2:], number_sys))

    return num


MAX_NUM_SIZE = {
    'i8': 0x7f,
    'i16': 0x7fff,
    'i32': 0x7fffff,
    'i64': 0x7fffffff,
    'i128': 0x7fffffffff,
    'u8': 0xff,
    'u16': 0xffff,
    'u32': 0xffffff,
    'u64': 0xffffffff,
    'u128': 0xffffffffff,
    'f32': 3.40282347e+38,
    'f64': 1.7976931348623157e+308,
}


def get_num_type(num: str):
    if '@' in num:
        return num.split('@')[1]

    cnum = float(compile_num(num))

    if '.' in num or 'e' in num or 'E' in num:
        return 'f32' if cnum <= MAX_NUM_SIZE['f32'] else 'f64'

    for t in ('i8', 'i16', 'i32', 'i64', 'i128'):
        if cnum <= MAX_NUM_SIZE[t]:
            return t

    return 'u128'


CVARS = {
    'standard_lib_path': abspath('./cft_Lib').replace('\\', '/'),
    'main_body': '',
    'global_body': ''
}


_used_compile_names = set()


def _get_compile_name(cft_name: str, namehandler: NameHandler):
    _name_obj = namehandler.get_current_body(cft_name)

    if 'compile-name' in _name_obj:
        compile_name = _name_obj['compile-name']
    else:
        compile_name = '_cft_' + cft_name

        i = 0
        while compile_name in _used_compile_names:
            compile_name = f'_cft_{cft_name}{i}'
            i += 1

    _used_compile_names.add(compile_name)
    return compile_name


def _obj_to_c(syntaxtree: dict, namehandler: NameHandler, auto_add=True):
    res = ''
    _type = syntaxtree['type']
    if _type == '$main-body':
        for obj in syntaxtree['value']:
            res += _obj_to_c(obj, namehandler, True)
    elif _type == '$call-name':
        res += f'{_get_compile_name(syntaxtree["called-name"], namehandler)}' \
               + f'({", ".join([_obj_to_c(obj, namehandler, False) for obj in syntaxtree["args"]])})' + ';\n'
    elif _type == 'str':
        res += f'"{syntaxtree["value"]}"'

    if auto_add:
        CVARS['main_body'] += res

    return res


def compile_to_c(syntaxtree: dict, namehandler: NameHandler):
    with open('./compile/main.c', 'r', encoding='utf-8') as f:
        main_c = f.read()

    CVARS['main_body'] = CVARS['global_body'] = ''

    _obj_to_c(syntaxtree, namehandler, False)

    for var in findall(r'\${(.+)}', main_c):
        main_c = main_c.replace(f'${{{var}}}', CVARS[var.strip()])

    return main_c


__all__ = (
    'compile_num',
    'get_num_type',
    'compile_to_c'
)


if __name__ == '__main__':
    print(compile_to_c({}))
