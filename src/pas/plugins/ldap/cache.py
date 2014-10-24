# -*- coding: utf-8 -*-
from bda.cache import Memcached
from bda.cache import NullCache
from pas.plugins.ldap.interfaces import ICacheSettingsRecordProvider
from pas.plugins.ldap.interfaces import ILDAPPlugin
from pas.plugins.ldap.interfaces import IPluginCacheHandler
from pas.plugins.ldap.interfaces import VALUE_NOT_CACHED
from zope.component import adapter
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.interface import implementer
import time


def cacheProviderFactory():
    recordProvider = queryUtility(ICacheSettingsRecordProvider)
    if not recordProvider:
        return NullCache()
    value = recordProvider().value or ''
    servers = value.split()
    if servers:
        return Memcached(servers)
    return NullCache()


def get_plugin_cache(context):
    if not context.plugin_caching:
        # bypass for testing
        return NullPluginCache(context)
    plugin_cache = IPluginCacheHandler(context, None)
    if plugin_cache is not None:
        return plugin_cache
    return RequestPluginCache(context)


@implementer(IPluginCacheHandler)
class NullPluginCache(object):

    def __init__(self, context):
        self.context = context

    def get(self):
        return VALUE_NOT_CACHED

    def set(self, value):
        pass


@implementer(IPluginCacheHandler)
class RequestPluginCache(object):

    def __init__(self, context):
        self.context = context

    def _key(self):
        return '_v_ldap_ugm_{0}_'.format(self.context.getId())

    def get(self):
        request = getRequest()
        rcachekey = self._key()
        if request and rcachekey in request.keys():
            return request[rcachekey]
        return VALUE_NOT_CACHED

    def set(self, value):
        request = getRequest()
        if request is not None:
            rcachekey = self._key()
            request[rcachekey] = value

    def invalidate(self):
        request = getRequest()
        rcachekey = self._key()
        if request and rcachekey in request.keys():
            del request[rcachekey]

VOLATILE_CACHE_MAXAGE = 10  # 10s default maxage on volatile


@adapter(ILDAPPlugin)
class VolatilePluginCache(RequestPluginCache):

    def get(self):
        try:
            cachetime, value = getattr(self.context, self._key())
        except AttributeError:
            return VALUE_NOT_CACHED
        if time.time() - cachetime > VOLATILE_CACHE_MAXAGE:
            return VALUE_NOT_CACHED
        return value

    def set(self, value):
        setattr(self.context, self._key(), (time.time(), value))

    def invalidate(self):
        try:
            delattr(self.context, self._key())
        except AttributeError:
            pass
