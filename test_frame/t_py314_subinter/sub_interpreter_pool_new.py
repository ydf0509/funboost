from concurrent import interpreters
from concurrent.futures import ThreadPoolExecutor, Future
import pickle, base64, types




class InterpreterPool:
    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, func, *args, **kwargs) -> Future:
        if not isinstance(func, types.FunctionType):
            raise TypeError("func must be a Python function")

        pickled = base64.b64encode(pickle.dumps((func, args, kwargs))).decode("utf-8")
        code = f"""
import pickle, base64
func, args, kwargs = pickle.loads(base64.b64decode('{pickled}'))
func(*args, **kwargs)
"""

        def _run():
            interp_id = interpreters.create()
            try:
                interpreters.run_string(interp_id, code)
            finally:
                interpreters.destroy_interpreter(interp_id)

        return self._executor.submit(_run)

    def shutdown(self, wait: bool = True):
        self._executor.shutdown(wait=wait)

if __name__ == "__main__":
    import time

    pool = InterpreterPool(max_workers=3)

    def task(i):
        print(f"Task {i} start")
        time.sleep(1)
        print(f"Task {i} done")

    futures = [pool.submit(task, i) for i in range(5)]
    for f in futures:
        f.result()

    pool.shutdown()

