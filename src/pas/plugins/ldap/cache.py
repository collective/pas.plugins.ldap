# -*- coding: utf-8 -*-

from bda.cache import Memcached
from bda.cache import NullCache
from node.ext.ldap.interfaces import ICacheProviderFactory
from pas.plugins.ldap.interfaces import ICacheSettingsRecordProvider
from pas.plugins.ldap.interfaces import ILDAPPlugin
from pas.plugins.ldap.interfaces import IPluginCacheHandler
from pas.plugins.ldap.interfaces import VALUE_NOT_CACHED
from zope.component import adapter
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.interface import implementer

import threading
import time


class PasLdapMemcached(Memcached):

    _servers = None

    def __init__(self, servers):
        self._servers = servers
        super(PasLdapMemcached, self).__init__(servers)

    @property
    def servers(self):
        return self._servers

    def disconnect_all(self):
        self._client.disconnect_all()

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.servers)


@implementer(ICacheProviderFactory)
class cacheProviderFactory(object):
    # memcache factory for node.ext.ldap

    _thread_local = threading.local()

    @property
    def _key(self):
        return "_v_{0}_PasLdapMemcached".format(self.__class__.__name__)

    @property
    def servers(self):
        recordProvider = queryUtility(ICacheSettingsRecordProvider)
        if not recordProvider:
            return ""

        value = recordProvider().value or ""
        return value.split()

    @property
    def cache(self):
        servers = self.servers
        if not servers:
            return NullCache()

        key = self._key

        # thread safety for memcached connections
        mcd = getattr(self._thread_local, key, None)

        # if mcd is set and server config has not changed
        # return mcd
        if mcd and frozenset(mcd.servers) == frozenset(servers):
            return mcd
        elif mcd:
            # server config has changed, close all connections
            mcd.disconnect_all()
            del mcd

        # establish new memcached connection and store
        # it on local thread
        mcd = PasLdapMemcached(servers)
        setattr(self._thread_local, key, mcd)

        return mcd

    def __call__(self):
        return self.cache


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
        return "_v_ldap_ugm_{0}_".format(self.context.getId())

    def get(self):
        request = getRequest()
        rcachekey = self._key()
        if request and rcachekey in list(request.keys()):
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
        if request and rcachekey in list(request.keys()):
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
