import ldap
import logging
logger = logging.getLogger('bda.plone.ldap')


WHAT_TO_DEBUG = set([
    'authentication',
    'properties',
    'userenumeration',
    ])


class debug(object):
    """Decorator which helps to control what aspects of a program to debug
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


class ifnotenabledreturn(object):
    """Checks whether plugin is enabled, returns retval otherwise
    """
    def __init__(decor, retval=None):
        decor.retval = retval

    def __call__(decor, method):
        def wrapper(*args, **kws):
            if not method.enabled:
                logger.error('bda ldap disabled: %s defaulting' % \
                        (method.func_name,))
                return decor.retval
            try:
                retval = method(*args, **kws)
            except Exception, e:
                logger.error('%s' % (str(e),))
                return decor.retval
            return retval
        wrapper.__doc__ = method.__doc__
        return wrapper
