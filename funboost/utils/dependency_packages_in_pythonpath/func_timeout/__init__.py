'''
    Copyright (c) 2016, 2017, 2019 Tim Savannah All Rights Reserved.

    Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
    LICENSE, otherwise it is available at https://github.com/kata198/func_timeout/LICENSE
'''


__version__ = '4.3.5'
__version_tuple__ = (4, 3, 5)

__all__ = ('func_timeout', 'func_set_timeout', 'FunctionTimedOut', 'StoppableThread')

from .exceptions import FunctionTimedOut
from .dafunc import func_timeout, func_set_timeout
from .StoppableThread import StoppableThread
