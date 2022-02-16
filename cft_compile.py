from os.path import abspath, splitext
from subprocess import Popen, PIPE


FLAG_COMPILE_C_WARNINGS = 1 << 0x0


def compile_c(file: str, res_file: str = ..., flags=0):
    file = abspath(file)

    if splitext(file)[1] == '':
        file += '.c'

    if res_file is ...:
        res_file = file[:-len(splitext(file)[1])]

    res_file = abspath(res_file)

    if splitext(res_file)[1] == '':
        res_file += '.exe'

    cmd = f'gcc -o "{res_file}" "{file}"'

    if flags & FLAG_COMPILE_C_WARNINGS == 0:
        cmd += ' -w'

    compiler = Popen(cmd, shell=True, stderr=PIPE, encoding='utf-8')

    res = {
        'stderr': compiler.stderr.read()
    }
    res['code'] = int('error:' in res['stderr'])

    compiler.kill()

    return res


def interpret_syntaxtree(syntaxtree: dict):
    pass


if __name__ == '__main__':
    print(compile_c("C:/Users/teaco/Desktop/Projects/Codes/C/Functions defining/main.c"))
