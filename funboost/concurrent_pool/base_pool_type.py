

class FunboostBaseConcurrentPool:

    def __deepcopy__(self, memodict={}):
        """
        pydantic 的默认值，需要deepcopy
        """
        return self