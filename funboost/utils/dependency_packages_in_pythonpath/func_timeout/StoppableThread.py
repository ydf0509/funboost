'''
    Copyright (c) 2016, 2017, 2019 Timothy Savannah All Rights Reserved.

    Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
    LICENSE, otherwise it is available at https://github.com/kata198/func_timeout/LICENSE
'''

import os
import ctypes
import threading

__all__ = ('StoppableThread', 'JoinThread')

class StoppableThread(threading.Thread):
    '''
        StoppableThread - A thread that can be stopped by forcing an exception in the execution context.

          This works both to interrupt code that is in C or in python code, at either the next call to a python function,
           or the next line in python code.

        It is recommended that if you call stop ( @see StoppableThread.stop ) that you use an exception that inherits BaseException, to ensure it likely isn't caught.

         Also, beware unmarked exception handlers in your code. Code like this:

            while True:
                try:
                    doSomething()
                except:
                    continue

        will never be able to abort, because the exception you raise is immediately caught.

        The exception is raised over and over, with a specifed delay (default 2.0 seconds)
    '''


    def _stopThread(self, exception, raiseEvery=2.0):
        '''
            _stopThread - @see StoppableThread.stop
        '''
        if self.is_alive() is False:
            return True

        self._stderr = open(os.devnull, 'w')

        # Create "joining" thread which will raise the provided exception
        #  on a repeat, until the thread stops.
        joinThread = JoinThread(self, exception, repeatEvery=raiseEvery)

        # Try to prevent spurrious prints
        joinThread._stderr = self._stderr
        joinThread.start()
        joinThread._stderr = self._stderr


    def stop(self, exception, raiseEvery=2.0):
        '''
            Stops the thread by raising a given exception.

            @param exception <Exception type> - Exception to throw. Likely, you want to use something

              that inherits from BaseException (so except Exception as e: continue; isn't a problem)

              This should be a class/type, NOT an instance, i.e.  MyExceptionType   not  MyExceptionType()


            @param raiseEvery <float> Default 2.0 - We will keep raising this exception every #raiseEvery seconds,

                until the thread terminates.

                If your code traps a specific exception type, this will allow you #raiseEvery seconds to cleanup before exit.

                If you're calling third-party code you can't control, which catches BaseException, set this to a low number

                  to break out of their exception handler.


             @return <None>
        '''
        return self._stopThread(exception, raiseEvery)


class JoinThread(threading.Thread):
    '''
        JoinThread - The workhouse that stops the StoppableThread.

            Takes an exception, and upon being started immediately raises that exception in the current context
              of the thread's execution (so next line of python gets it, or next call to a python api function in C code ).

            @see StoppableThread for more details
    '''

    def __init__(self, otherThread, exception, repeatEvery=2.0):
        '''
            __init__ - Create a JoinThread (don't forget to call .start() ! )

                @param otherThread <threading.Thread> - A thread

                @param exception <BaseException> - An exception. Should be a BaseException, to prevent "catch Exception as e: continue" type code
                  from never being terminated. If such code is unavoidable, you can try setting #repeatEvery to a very low number, like .00001,
                  and it will hopefully raise within the context of the catch, and be able to break free.

                @param repeatEvery <float> Default 2.0 - After starting, the given exception is immediately raised. Then, every #repeatEvery seconds,
                  it is raised again, until the thread terminates.
        '''
        threading.Thread.__init__(self)
        self.otherThread = otherThread
        self.exception = exception
        self.repeatEvery = repeatEvery
        self.daemon = True

    def run(self):
        '''
            run - The thread main. Will attempt to stop and join the attached thread.
        '''

        # Try to silence default exception printing.
        self.otherThread._Thread__stderr = self._stderr
        if hasattr(self.otherThread, '_Thread__stop'):
            # If py2, call this first to start thread termination cleanly.
            #   Python3 does not need such ( nor does it provide.. )
            self.otherThread._Thread__stop()
        while self.otherThread.is_alive():
            # We loop raising exception incase it's caught hopefully this breaks us far out.
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.otherThread.ident), ctypes.py_object(self.exception))
            self.otherThread.join(self.repeatEvery)

        try:
            self._stderr.close()
        except:
            pass

# vim: set ts=4 sw=4 expandtab :
