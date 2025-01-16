

# Python2 allows specifying an alternate traceback.
def raise_exception(exception):
    '''
    raise exception[0] , None , exception[0].__traceback__  # noqa
    '''
