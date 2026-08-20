"""Cache management for the LDAP plugin."""

from .interfaces import ICacheSettingsRecordProvider
from .interfaces import ILDAPPlugin
from .interfaces import IPluginCacheHandler
from .interfaces import VALUE_NOT_CACHED
from bda.cache import Memcached
from bda.cache import NullCache
from node.ext.ldap.interfaces import ICacheProviderFactory
from zope.component import adapter
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.interface import implementer

import contextlib
import threading
import time


class PasLdapMemcached(Memcached):
    """Memcached client for LDAP plugin.

    Args:
        servers: The list of memcached servers.
    """

    _servers = None

    def __init__(self, servers):
        self._servers = servers
        super().__init__(servers)

    @property
    def servers(self):
        """Get the list of memcached servers."""
        return self._servers

    def disconnect_all(self):
        """Disconnect all memcached connections."""
        self._client.disconnect_all()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.servers}>"


@implementer(ICacheProviderFactory)
class cacheProviderFactory:
    """Cache provider factory for LDAP plugin.

    memcache factory for node.ext.ldap
    """

    # thread local to store memcached instance per thread for thread safety
    _thread_local = threading.local()

    @property
    def _key(self):
        """Key for storing the memcached instance on the thread local."""
        return f"_v_{self.__class__.__name__}_PasLdapMemcached"

    @property
    def servers(self):
        """Get the list of memcached servers from the cache settings
        record provider."""
        recordProvider = queryUtility(ICacheSettingsRecordProvider)
        if not recordProvider:
            return ""

        value = recordProvider().value or ""
        return value.split()

    @property
    def cache(self):
        """Get the cache instance for the current thread."""
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
    """Get the plugin cache for the given context."""
    if not context.plugin_caching:
        # bypass for testing
        return NullPluginCache(context)
    plugin_cache = IPluginCacheHandler(context, None)
    if plugin_cache is not None:
        return plugin_cache
    return RequestPluginCache(context)


@implementer(IPluginCacheHandler)
class NullPluginCache:
    """Null plugin cache for LDAP plugin."""

    def __init__(self, context):
        self.context = context

    def get(self):
        """Get the value from the cache, always returning VALUE_NOT_CACHED."""
        return VALUE_NOT_CACHED

    def set(self, value):
        """Set the value in the cache, does nothing for NullPluginCache."""
        pass


@implementer(IPluginCacheHandler)
class RequestPluginCache:
    """Request-based plugin cache for LDAP plugin.

    Args:
        context: The context for the cache.
    """

    def __init__(self, context):
        self.context = context
        self._key = f"_v_ldap_ugm_{self.context.getId()}_"

    def getRootRequest(self):
        """Get the root request from the current request."""

        def parent_request(current_request):
            preq = current_request.get("PARENT_REQUEST", None)
            if preq:
                return parent_request(preq)
            return current_request

        return parent_request(getRequest())

    def get(self):
        """Get the value from the cache by looking it up on the request."""
        return (self.getRootRequest() or {}).get(self._key, VALUE_NOT_CACHED)

    def set(self, value):
        """Set the value in the cache by storing it on the request."""
        request = self.getRootRequest()
        if request is not None:
            request[self._key] = value

    def invalidate(self):
        """Invalidate the cache by removing the cached value
        from the request."""
        request = self.getRootRequest()
        if request and self._key in list(request.keys()):
            del request[self._key]


VOLATILE_CACHE_MAXAGE = 10  # 10s default maxage on volatile


@adapter(ILDAPPlugin)
class VolatilePluginCache(RequestPluginCache):
    """Volatile plugin ºcache for LDAP plugin.

    Args:
        RequestPluginCache (object): Request-based plugin cache for
        LDAP plugin.
    """

    def get(self):
        """Get the value from the cache by looking it up on the request and
        checking if it is still valid based on the max age."""
        try:
            cachetime, value = getattr(self.context, self._key)
        except AttributeError:
            return VALUE_NOT_CACHED
        if time.time() - cachetime > VOLATILE_CACHE_MAXAGE:
            return VALUE_NOT_CACHED
        return value

    def set(self, value):
        """Set the value in the cache by storing it on the context
        with a timestamp."""
        setattr(self.context, self._key, (time.time(), value))

    def invalidate(self):
        """Invalidate the cache by removing the cached value
        from the context."""
        with contextlib.suppress(AttributeError):
            delattr(self.context, self._key)
