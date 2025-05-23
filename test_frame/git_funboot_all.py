# coding=utf-8
import subprocess
import os
import time
from pathlib import Path
# os.environ["path"] = r'C:\Program Files\Git\mingw64\libexec\git-core'
def getstatusoutput(cmd):
    try:
        data = subprocess.check_output(cmd, shell=True, universal_newlines=True,
                                       stderr=subprocess.STDOUT, encoding='utf8')
        exitcode = 0
    except subprocess.CalledProcessError as ex:
        data = ex.output
        exitcode = ex.returncode
    if data[-1:] == '\n':
        data = data[:-1]
    return exitcode, data


def do_cmd(cmd_strx):
    print(f'执行 {cmd_strx}')
    retx = getstatusoutput(cmd_strx)
    print(retx[0])
    # if retx[0] !=0:
    #     raise ValueError('要检查git提交')
    print(retx[1], '\n')
    return retx


def push():
    path = Path(__file__).parent.parent
    print(f'path: {path}')
    t0 = time.time()

    do_cmd('git pull')

    do_cmd('git diff')

    do_cmd(f'git add {path}')

    do_cmd('git commit -m commit')

    # do_cmd('git push --set-upstream origin {}')

    do_cmd('git push origin')

    do_cmd('git push github')

    # print(subprocess.getstatusoutput('git push github'))
    print(f'{time.strftime("%H:%M:%S")}  spend_time {time.time() - t0}')


'''dsdsab'''


if __name__ == '__main__':
    push()
    time.sleep(2000000)
