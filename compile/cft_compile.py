from py_utils import isnotfinished


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


def __compile_op_expr(syntaxtree: dict) -> str:
    # !THIS FUNCTION IS NOT FOR RELEASE, NEEDED ONLY FOR DEBUG!

    isnotfinished()

    if syntaxtree['type'] == 'main':
        return __compile_op_expr(syntaxtree['value'][0])

    if syntaxtree['type'] == 'op':
        if 'value' in syntaxtree:
            return syntaxtree['op'] + ' ' + __compile_op_expr(syntaxtree['value'])

        return f'{{{__compile_op_expr(syntaxtree["lvalue"])} {syntaxtree["op"]} {__compile_op_expr(syntaxtree["rvalue"])}}}'

    if syntaxtree['type'] == 'number':
        return syntaxtree['value']

    if syntaxtree['type'] == 'bool':
        return 'true' if syntaxtree['value'] == 'True' else 'false'

    if syntaxtree['type'] == 'char':
        return "'" + syntaxtree['value'] + "'"

    return f'"{syntaxtree["value"]}"'


__all__ = (
    'compile_num',
    'get_num_type'
)
