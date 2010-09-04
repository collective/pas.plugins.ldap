class debug:
    """ Decorator which helps to control what aspects of a program to debug
    on per-function basis. Aspects are provided as list of arguments.
    It DOESN'T slowdown functions which aren't supposed to be debugged.
    """
    def __init__(self, aspects=None):
        self.aspects = set(aspects)

    def __call__(self, func): 
        if self.aspects & WHAT_TO_DEBUG:
            def newfunc(*args, **kws):
                logger.debug('%s: args=%s, kws=%s', func.func_name, args, kws)
                result = func(*args, **kws)
                logger.debug('%s: --> %s', func.func_name, result)
                return result
            newfunc.__doc__ = func.__doc__
            return newfunc
        else:
            return func


