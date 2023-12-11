

class FunboostBaseConcurrentPool:

    def __deepcopy__(self, memodict={}):
        """
        pydantic 的默认类型声明，对象需要能deepcopy
        """
        return self