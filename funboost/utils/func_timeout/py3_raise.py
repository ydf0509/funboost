
# PEP 409 - Raise with the chained exception context disabled
#  This, in effect, prevents the "funcwrap" wrapper ( chained
#   in context to an exception raised here, due to scope )
# Only available in python3.3+
def raise_exception(exception):
    raise exception[0] from None
