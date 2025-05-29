import os
import sys
import shutil

# Ensure dependencies
# os.system(f"{sys.executable} -m pip install --user --upgrade setuptools wheel twine")

# Delete previous build
import time
from test_frame import  git_funboot_all
git_funboot_all.push()

shutil.rmtree("dist", ignore_errors=True)

# Build
os.system(f"{sys.executable} setup.py sdist bdist_wheel")

# Upload
os.system(f"{sys.executable} -m twine upload dist/*")

shutil.rmtree("build", ignore_errors=True)

time.sleep(1000000)
