from os.path import abspath
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
    'standard_lib_path': abspath('../Lib').replace('\\', '/'),
    'main_body': '',
    'global_body': ''
}


def compile_to_c(syntaxtree: dict):
    with open('main.c', 'r', encoding='utf-8') as f:
        main_c = f.read()

    for var in findall(r'\${(.+)}', main_c):
        main_c = main_c.replace(f'${{{var}}}', CVARS[var.strip()])

    return main_c


__all__ = (
    'compile_num',
    'get_num_type'
)


if __name__ == '__main__':
    print(compile_to_c({}))
