import subprocess

import time

def getstatusoutput(cmd):
    try:
        data = subprocess.check_output(cmd, shell=True, universal_newlines=True,
                                       stderr=subprocess.STDOUT, encoding='utf8')  # Must set encoding to utf8 to avoid errors.
        exitcode = 0
    except subprocess.CalledProcessError as ex:
        data = ex.output
        exitcode = ex.returncode
    if data[-1:] == '\n':
        data = data[:-1]
    return exitcode, data

def do_cmd(cmd_strx):
    print(f'exec {cmd_strx}')
    retx = getstatusoutput(cmd_strx)
    print(retx[0])

    print(retx[1], '\n')
    return retx

t0 = time.time()

do_cmd('git pull')

do_cmd('git diff')

do_cmd('git add .')

do_cmd('git commit -m commit')



do_cmd('git push origin')

# print(subprocess.getstatusoutput('git push github'))
print(f'spend_time {time.time() - t0}')


if __name__ == '__main__':

    time.sleep(100000)