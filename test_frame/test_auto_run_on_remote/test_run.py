import os
from auto_run_on_remote import run_current_script_on_remote
from test_frame.test_auto_run_on_remote.show import show

print(os.name)
run_current_script_on_remote()
for i in range(10):
    show(i)