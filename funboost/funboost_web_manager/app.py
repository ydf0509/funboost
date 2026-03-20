"""
这个文件作用主要是兼容老的  from funboost.funboost_web_manager import xx
"""

from funboost.funweb.app import *



if __name__ == "__main__":
    start_funboost_web_manager(debug=False)