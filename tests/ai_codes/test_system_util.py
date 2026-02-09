
import sys
import os
# Ensure funboost is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from funboost.utils import system_util

print(f"Is Windows: {system_util.is_windows()}")
print(f"Is Linux: {system_util.is_linux()}")
print(f"Is Mac: {system_util.is_mac()}")
print(f"OS Str: {system_util.get_os_str()}")
print(f"Hostname: {system_util.get_hostname()}")
print(f"Host IP: {system_util.get_host_ip()}")
print(f"MAC Address: {system_util.get_mac_address()}")
print(f"PID: {system_util.get_pid()}")
print(f"Thread ID: {system_util.get_thread_id()}")
print(f"Process Name: {system_util.get_process_name()}")
print(f"Thread Name: {system_util.get_current_thread_name()}")
print(f"CPU Count: {system_util.get_cpu_count()}")
print(f"Python Version: {system_util.get_python_version()}")
print(f"Current Function Name: {system_util.get_current_function_name()}") # Should print 'get_current_function_name' because it's called inside the print statement? NOTE: stack[1] is caller. Let's wrap it.

def test_func_name():
    print(f"Inside func: {system_util.get_current_function_name()}")

test_func_name()
